from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Haber, Kategori

class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return [
            'anasayfa',
            'hakkimizda_root',
            'iletisim_root',
            'gizlilik_politikasi_root',
            'kullanim_sartlari_root',
            'kunye_root',
            'yazarlar_listesi_root',
            'haberler:karate_antrenorler',
            'haberler:video_sayfasi',
        ]

    def location(self, item):
        try:
            return reverse(item)
        except Exception:
            return '/'


class HaberSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Haber.objects.filter(yayinlandi=True).order_by('-olusturma_tarihi')

    def lastmod(self, obj):
        return obj.guncelleme_tarihi or obj.olusturma_tarihi
        
    def location(self, obj):
        return reverse('haberler:haber_detay', args=[obj.slug])


class KategoriSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8
    
    def items(self):
        return Kategori.objects.all().order_by('ad')
        
    def location(self, obj):
        return reverse('haberler:kategori_haberler', args=[obj.slug])


class YazarSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        # Only authors who have published news or columns
        return User.objects.filter(haber__yayinlandi=True).distinct().order_by('username')

    def location(self, obj):
        return reverse('haberler:yazar_detay', args=[obj.username])
