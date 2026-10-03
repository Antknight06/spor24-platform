from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import F, Sum
from .models_engagement import Poll, PollChoice, PollVote, Quiz, QuizQuestion, UserQuizScore
import json

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@require_POST
def vote_poll(request, poll_id):
    """AJAX view to register a vote on a poll"""
    poll = get_object_or_404(Poll, id=poll_id, is_active=True)
    
    # Check if choice_id is provided
    try:
        data = json.loads(request.body)
        choice_id = data.get('choice_id')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Geçersiz veri biçimi.'}, status=400)
        
    if not choice_id:
        return JsonResponse({'success': False, 'message': 'Lütfen bir seçenek işaretleyin.'}, status=400)
        
    choice = get_object_or_404(PollChoice, id=choice_id, poll=poll)
    ip_address = get_client_ip(request)
    
    # Check if duplicate vote
    if request.user.is_authenticated:
        already_voted = PollVote.objects.filter(poll=poll, user=request.user).exists()
    else:
        already_voted = PollVote.objects.filter(poll=poll, ip_address=ip_address).exists()
        
    if already_voted:
        # Get current results to return
        choices_data = []
        total_votes = poll.choices.aggregate(total=Sum('votes_count'))['total'] or 1
        for ch in poll.choices.all():
            percentage = round((ch.votes_count / total_votes) * 100)
            choices_data.append({
                'id': ch.id,
                'text': ch.choice_text,
                'votes': ch.votes_count,
                'percentage': percentage
            })
        return JsonResponse({
            'success': False, 
            'error_code': 'already_voted',
            'message': 'Bu ankette zaten oy kullandınız.',
            'results': choices_data
        })
        
    # Record the vote
    vote = PollVote(poll=poll, choice=choice, ip_address=ip_address)
    if request.user.is_authenticated:
        vote.user = request.user
    vote.save()
    
    # Increment choice votes
    choice.votes_count = F('votes_count') + 1
    choice.save()
    
    # Get updated results
    choice.refresh_from_db()
    total_votes = poll.choices.aggregate(total=Sum('votes_count'))['total'] or 1
    choices_data = []
    for ch in poll.choices.all():
        percentage = round((ch.votes_count / total_votes) * 100)
        choices_data.append({
            'id': ch.id,
            'text': ch.choice_text,
            'votes': ch.votes_count,
            'percentage': percentage
        })
        
    return JsonResponse({
        'success': True,
        'message': 'Oyunuz başarıyla kaydedildi.',
        'results': choices_data
    })

def quiz_list(request):
    """View to list all active quizzes and display global leaderboard"""
    quizzes = Quiz.objects.filter(is_active=True).order_by('-created_at')
    
    # Fetch top 10 leaderboard scores overall
    leaderboard = UserQuizScore.objects.select_related('user', 'quiz').order_by('-score', 'completed_at')[:10]
    
    context = {
        'quizzes': quizzes,
        'leaderboard': leaderboard,
    }
    return render(request, 'engagement/quiz_list.html', context)

def quiz_detail(request, quiz_id):
    """View to show quiz details and questions"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    questions = quiz.questions.all()
    
    user_best_score = None
    if request.user.is_authenticated:
        user_best_score = UserQuizScore.objects.filter(quiz=quiz, user=request.user).order_by('-score').first()
        
    context = {
        'quiz': quiz,
        'questions': questions,
        'user_best_score': user_best_score,
    }
    return render(request, 'engagement/quiz_detail.html', context)

@login_required
@require_POST
def submit_quiz(request, quiz_id):
    """AJAX view to process quiz answers and record score"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    questions = quiz.questions.all()
    
    try:
        data = json.loads(request.body)
        answers = data.get('answers', {}) # format: {"question_id": "A/B/C/D"}
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Geçersiz veri biçimi.'}, status=400)
        
    correct_count = 0
    total_questions = questions.count()
    
    if total_questions == 0:
        return JsonResponse({'success': False, 'message': 'Bu yarışmada soru bulunmamaktadır.'}, status=400)
        
    results_detail = {}
    for q in questions:
        user_ans = answers.get(str(q.id))
        is_correct = (user_ans == q.correct_option)
        if is_correct:
            correct_count += 1
        results_detail[q.id] = {
            'user_answer': user_ans,
            'correct_answer': q.correct_option,
            'is_correct': is_correct
        }
        
    score_percentage = round((correct_count / total_questions) * 100)
    
    # Save the user score
    UserQuizScore.objects.create(
        quiz=quiz,
        user=request.user,
        score=score_percentage
    )
    
    return JsonResponse({
        'success': True,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'score': score_percentage,
        'results_detail': results_detail
    })
