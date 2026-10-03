from haberler.models import Reklam, Kategori, FederasyonWebsite, Ad
from django.utils import timezone

def global_ads(request):
    """Context processor to inject global tracking, ads and engagement widgets on every page"""
    try:
        active_ads = Reklam.objects.filter(aktif=True)
        categories = Kategori.objects.filter(menude_goster=True).order_by('ad')
        aktif_federasyon_sayisi = FederasyonWebsite.objects.filter(aktif=True).count()
        toplam_federasyon_sayisi = FederasyonWebsite.objects.count()

        # Active poll for sidebar widget
        now = timezone.now()
        try:
            from haberler.models_engagement import Poll, Quiz
            from django.db.models import Sum, Q
            active_polls = Poll.objects.filter(
                is_active=True
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gt=now)
            ).prefetch_related('choices').order_by('-created_at')

            active_poll = active_polls.first()
            polls_by_position = {p.position: p for p in active_polls}
            active_quiz_count = Quiz.objects.filter(is_active=True).count()
        except Exception:
            active_poll = None
            polls_by_position = {}
            active_quiz_count = 0

        
        card_ads = Ad.objects.filter(aktif=True)
        ads_by_slot = {a.konum: a for a in card_ads}

        return {
            'card_ads': card_ads,
            'ads_by_slot': ads_by_slot,
            'global_head_ad': active_ads.filter(konum='global_head').first(),
            'global_body_ad': active_ads.filter(konum='global_body').first(),
            'header_ad': active_ads.filter(konum='header_ad').first(),
            'menudeki_kategoriler': categories,
            'sidebar_poll': active_poll,
            'polls_by_position': polls_by_position,
            'active_quiz_count': active_quiz_count,
            'aktif_federasyon_sayisi': aktif_federasyon_sayisi,
            'toplam_federasyon_sayisi': toplam_federasyon_sayisi,
        }
    except Exception:
        return {}
