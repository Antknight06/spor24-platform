from django.db import models
from django.utils import timezone
from datetime import timedelta
import hashlib
from urllib.parse import urlparse

def get_content_id(haber):
    if not haber:
        return "SP24-0000-NONE"
    tarih_str = haber.olusturma_tarihi.strftime('%Y%m%d') if getattr(haber, 'olusturma_tarihi', None) else '2026'
    raw = f"{haber.id}_{tarih_str}_{haber.baslik[:20]}"
    sig = hashlib.sha256(raw.encode('utf-8', errors='ignore')).hexdigest()[:6].upper()
    return f"SP24-{haber.id}-{sig}"

class ZiyaretLog(models.Model):
    ip_hash = models.CharField(max_length=64, db_index=True)
    session_id = models.CharField(max_length=64, null=True, blank=True)
    path = models.CharField(max_length=255)
    haber_id = models.IntegerField(null=True, blank=True, db_index=True)
    kategori_ad = models.CharField(max_length=100, null=True, blank=True)
    yazar_ad = models.CharField(max_length=100, null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    referrer = models.CharField(max_length=500, null=True, blank=True)
    referrer_domain = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    utm_source = models.CharField(max_length=100, null=True, blank=True)
    utm_medium = models.CharField(max_length=100, null=True, blank=True)
    utm_campaign = models.CharField(max_length=100, null=True, blank=True)
    device_type = models.CharField(max_length=20, default='desktop')
    browser = models.CharField(max_length=50, null=True, blank=True)
    event_type = models.CharField(max_length=30, default='pageview', db_index=True)
    target_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        managed = False
        db_table = 'haberler_ziyaretlog'
        ordering = ['-created_at']

    @classmethod
    def parse_domain(cls, ref):
        if not ref:
            return 'Doğrudan (Direct)'
        try:
            parsed = urlparse(ref)
            netloc = parsed.netloc.lower()
            if not netloc or 'spor24.net' in netloc:
                return 'Doğrudan (Direct)'
            if 'google' in netloc:
                return 'Google Arama'
            if 'facebook' in netloc or 'fb.com' in netloc:
                return 'Facebook / Meta'
            if 'instagram' in netloc:
                return 'Instagram'
            if 'twitter' in netloc or 't.co' in netloc or 'x.com' in netloc:
                return 'X (Twitter)'
            if 'telegram' in netloc or 't.me' in netloc:
                return 'Telegram'
            if 'whatsapp' in netloc:
                return 'WhatsApp'
            if 'yandex' in netloc:
                return 'Yandex'
            if 'bing' in netloc:
                return 'Bing'
            return netloc.replace('www.', '')
        except Exception:
            return 'Diğer Kaynaklar'
