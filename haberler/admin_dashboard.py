from django.utils import timezone
from .models import Haber, BekleyenHaber, BekleyenYetkiliHaberi, FederasyonWebsite, Kategori
from django.contrib.auth.models import User

def dashboard_callback(request, context):
    """
    Supplies real-time live statistics and quick action metrics
    to Unfold Admin Dashboard for Kenan Ant (General Editor & Superadmin).
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_haber = Haber.objects.filter(yayinlandi=True).count()
    bugun_haber = Haber.objects.filter(yayinlandi=True, olusturma_tarihi__gte=today_start).count()
    bekleyen_bot = BekleyenHaber.objects.filter(onaylandi=False).count()
    bekleyen_yetkili = BekleyenYetkiliHaberi.objects.filter(onaylandi=False, reddedildi=False).count()
    aktif_fed = FederasyonWebsite.objects.filter(aktif=True).count()
    toplam_fed = FederasyonWebsite.objects.count()
    toplam_kat = Kategori.objects.count()
    toplam_yazar = User.objects.filter(is_staff=True).count()
    
    bekleyen_sosyal = 0
    try:
        from .models import BekleyenSosyalMedyaHaberi
        bekleyen_sosyal = BekleyenSosyalMedyaHaberi.objects.filter(onaylandi=False, reddedildi=False).count()
    except Exception:
        bekleyen_sosyal = 0

    broken_links = 0
    try:
        from linkcheck.models import Link
        broken_links = Link.objects.filter(url__status=False).count()
    except Exception:
        broken_links = 0

    context.update({
        "stats": {
            "total_haber": total_haber,
            "bugun_haber": bugun_haber,
            "bekleyen_bot": bekleyen_bot,
            "bekleyen_sosyal": bekleyen_sosyal,
            "bekleyen_yetkili": bekleyen_yetkili,
            "aktif_fed": aktif_fed,
            "toplam_fed": toplam_fed,
            "toplam_kat": toplam_kat,
            "toplam_yazar": toplam_yazar,
            "broken_links": broken_links,
        },
        "recent_published": Haber.objects.filter(yayinlandi=True).order_by('-olusturma_tarihi')[:6],
        "recent_bot": BekleyenHaber.objects.filter(onaylandi=False).order_by('-olusturma_tarihi')[:6],
    })
    return context
