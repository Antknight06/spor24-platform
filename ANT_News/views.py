from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from haberler.models import BekleyenHaber, BekleyenYetkiliHaberi

def check_new_news(request):
    """Admin endpoint to check for new pending news"""
    # Calculate 12 hours ago
    twelve_hours_ago = timezone.now() - timedelta(hours=12)
    
    # Count pending regular news from the last 12 hours based on actual publication date
    recent_pending_count = BekleyenHaber.objects.filter(
        onaylandi=False, 
        reddedildi=False,
        haber_tarihi__gte=twelve_hours_ago
    ).count()
    
    # Count all pending regular news regardless of date
    total_pending_count = BekleyenHaber.objects.filter(
        onaylandi=False, 
        reddedildi=False
    ).count()
    
    # Count pending yetkili news from the last 12 hours
    recent_yetkili_count = BekleyenYetkiliHaberi.objects.filter(
        onaylandi=False, 
        reddedildi=False,
        olusturma_tarihi__gte=twelve_hours_ago
    ).count()
    
    # Count all pending yetkili news regardless of date
    total_yetkili_count = BekleyenYetkiliHaberi.objects.filter(
        onaylandi=False, 
        reddedildi=False
    ).count()
    
    return JsonResponse({
        'has_new_news': total_pending_count > 0,  # Show new news symbol if there are any pending news
        'new_news_count': recent_pending_count,
        'pending_news_count': total_pending_count,
        'has_yetkili_news': total_yetkili_count > 0,  # Show yetkili news symbol if there are any pending yetkili news
        'new_yetkili_count': recent_yetkili_count,
        'pending_yetkili_count': total_yetkili_count
    })

def boxing_test(request):
    """Test page for boxing images"""
    return render(request, 'boxing_test.html')