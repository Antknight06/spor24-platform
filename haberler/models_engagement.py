from django.db import models
from django.contrib.auth.models import User

class Poll(models.Model):
    POSITION_CHOICES = [
        ('grid_3', '3. Haber Kartı Yeri'),
        ('grid_5', '5. Haber Kartı Yeri'),
        ('grid_7', '7. Haber Kartı Yeri'),
        ('grid_10', '10. Haber Kartı Yeri'),
        ('grid_12', '12. Haber Kartı Yeri'),
        ('grid_15', '15. Haber Kartı Yeri'),
        ('sidebar', 'Sağ Yan Sütun (Sidebar)'),
    ]

    question = models.CharField(max_length=255, verbose_name="Anket Sorusu")
    position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        default='grid_3',
        verbose_name="Anket Yerleşim Pozisyonu",
        help_text="Anketin haber listesinde kaçıncı haber kartının yerine geleceğini seçin."
    )
    start_date = models.DateTimeField(verbose_name="Başlangıç Tarihi", null=True, blank=True)
    end_date = models.DateTimeField(verbose_name="Bitiş Tarihi", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    class Meta:
        verbose_name = "Anket"
        verbose_name_plural = "Anketler"
        ordering = ['-created_at']

    def __str__(self):
        return self.question

class PollChoice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choices', verbose_name="Anket")
    choice_text = models.CharField(max_length=255, verbose_name="Seçenek Metni")
    votes_count = models.PositiveIntegerField(default=0, verbose_name="Oy Sayısı")

    class Meta:
        verbose_name = "Anket Seçeneği"
        verbose_name_plural = "Anket Seçenekleri"

    def __str__(self):
        return f"{self.poll.question[:30]} - {self.choice_text}"

class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, verbose_name="Anket")
    choice = models.ForeignKey(PollChoice, on_delete=models.CASCADE, verbose_name="Seçenek")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Oy Veren Kullanıcı")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oy Verme Zamanı")

    class Meta:
        verbose_name = "Anket Oyu"
        verbose_name_plural = "Anket Oyları"
        unique_together = [['poll', 'user'], ['poll', 'ip_address']]

    def __str__(self):
        return f"{self.poll.question[:30]} - Oy"

class Quiz(models.Model):
    title = models.CharField(max_length=255, verbose_name="Yarışma Başlığı")
    description = models.TextField(blank=True, verbose_name="Yarışma Açıklaması")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    class Meta:
        verbose_name = "Yarışma (Quiz)"
        verbose_name_plural = "Yarışmalar (Quizzes)"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name="Yarışma")
    question_text = models.TextField(verbose_name="Soru Metni")
    option_a = models.CharField(max_length=255, verbose_name="A Şıkkı")
    option_b = models.CharField(max_length=255, verbose_name="B Şıkkı")
    option_c = models.CharField(max_length=255, verbose_name="C Şıkkı")
    option_d = models.CharField(max_length=255, verbose_name="D Şıkkı")
    correct_option = models.CharField(
        max_length=1, 
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        verbose_name="Doğru Cevap"
    )

    class Meta:
        verbose_name = "Yarışma Sorusu"
        verbose_name_plural = "Yarışma Soruları"

    def __str__(self):
        return f"{self.quiz.title[:30]} - Soru"

class UserQuizScore(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name="Yarışma")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    score = models.PositiveIntegerField(verbose_name="Alınan Puan")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Tamamlama Tarihi")

    class Meta:
        verbose_name = "Yarışma Skoru"
        verbose_name_plural = "Yarışma Skorları"
        ordering = ['-score', 'completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title[:30]} - {self.score}"
