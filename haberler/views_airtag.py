"""
SPOR24 AirTag Yönlendirici & Dağıtım Takipçisi (AirTag Redirector & Trace Router)
Kısa linkleri (/c/1433) karşılar, sinyali kaydeder ve habere yönlendirir.
"""

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseNotFound
from django.utils import timezone
from django.db import models
import hashlib
import re

from haberler.models import Haber
from haberler.models_analytics import ZiyaretLog
from .smart_tags import generate_smart_tags, get_airtag_id, get_airtag_shortlink


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def airtag_redirect(request, news_id=None, content_id=None):
    """
    AirTag Kısa Link Giriş Noktası (/c/<id> veya /c/<content_id>)
    Örnek:
      /c/1433?tag=wa_durum
      /c/1433?tag=ant_tv
      /c/SP24-1433-692C2D
    """
    target_id = None
    if news_id:
        target_id = news_id
    elif content_id:
        # SP24-1433-692C2D formatından ID çıkar
        match = re.search(r'SP24-(\d+)-', str(content_id), re.IGNORECASE)
        if match:
            target_id = int(match.group(1))
        elif str(content_id).isdigit():
            target_id = int(content_id)

    if not target_id:
        return redirect('/')

    haber = Haber.objects.filter(id=target_id, yayinlandi=True).first()
    if not haber:
        return redirect('/')

    # 1. AirTag Sinyalini Kaydet
    tag_channel = request.GET.get('tag') or request.GET.get('src') or request.GET.get('utm_source') or 'direct_airtag'
    ip = _get_client_ip(request)
    ip_hash = hashlib.sha256((ip + "_SPOR24_SALT_2026_").encode('utf-8')).hexdigest()[:32]
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    device_type = 'mobile' if re.search(r'mobile|android|iphone|ipod', user_agent.lower()) else 'desktop'

    try:
        ZiyaretLog.objects.create(
            ip_hash=ip_hash,
            path=f"/c/{target_id}?tag={tag_channel}",
            haber_id=target_id,
            kategori_ad=haber.kategori.ad if haber.kategori else 'GÜNCEL',
            utm_source=f"airtag_{tag_channel}"[:100],
            utm_medium='airtag',
            device_type=device_type,
            event_type='airtag_scan',
            referrer=request.META.get('HTTP_REFERER', ''),
            referrer_domain=f"AirTag ({tag_channel})"[:100]
        )
    except Exception:
        pass

    # 2. Canonical Haber Sayfasına Yönlendir
    if haber.slug:
        target_url = f"/haberler/{haber.slug}/?airtag={tag_channel}"
    else:
        target_url = f"/post.html?id={haber.id}&airtag={tag_channel}"

    return redirect(target_url)


def api_tag_news(request, tag_name):
    """
    Belirli bir akıllı taga ait haberleri listeler.
    Örnek: /api/tags/Karate/ veya /api/tags/U14/
    """
    clean_tag = tag_name.replace('#', '').strip().lower()
    
    # Başlık ve özette tag geçen haberleri ara
    haberler = Haber.objects.filter(yayinlandi=True).filter(
        models.Q(baslik__icontains=clean_tag) |
        models.Q(ozet__icontains=clean_tag) |
        models.Q(kategori__ad__icontains=clean_tag)
    ).order_by('-olusturma_tarihi')[:20]

    results = []
    for h in haberler:
        results.append({
            'id': h.id,
            'title': h.baslik,
            'category': h.kategori.ad if h.kategori else 'GÜNCEL',
            'airtag_id': get_airtag_id(h),
            'shortlink': get_airtag_shortlink(h, 'tag_browse'),
            'url': f"/haberler/{h.slug}/" if h.slug else f"/post.html?id={h.id}",
            'smart_tags': generate_smart_tags(h)
        })

    return JsonResponse({'tag': tag_name, 'count': len(results), 'results': results})
