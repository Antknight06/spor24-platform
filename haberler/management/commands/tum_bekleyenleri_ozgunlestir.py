# -*- coding: utf-8 -*-
import time
import logging
from django.core.management.base import BaseCommand
from haberler.models import BekleyenHaber
from haberler.ai_news_engine import ozgunlestir_haber

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Tüm bekleyen haberleri Google Gemini ile özgünleştirir ve puanlar"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='İşlenecek maksimum haber sayısı')
        parser.add_argument('--delay', type=float, default=2.0, help='İki istek arası bekleme süresi (saniye)')
        parser.add_argument('--force', action='store_true', help='Hazır olanları da yeniden işle')

    def handle(self, *args, **options):
        limit = options['limit']
        delay = options['delay']
        force = options['force']

        qs = BekleyenHaber.objects.filter(onaylandi=False, reddedildi=False)
        if not force:
            # ham, hata veya yarım kalmış (isleniyor) ya da başlığı boş olanlar
            qs = qs.filter(
                ai_durum__in=['ham', 'hata', 'isleniyor', None]
            ) | qs.filter(ozgun_baslik__isnull=True) | qs.filter(ozgun_baslik='')
            qs = qs.distinct()

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("✨ Özgünleştirilecek bekleyen haber bulunamadı, tümü zaten hazır!"))
            return

        if limit:
            qs = qs[:limit]
            total = min(total, limit)

        self.stdout.write(self.style.SUCCESS(f"🚀 Toplam {total} adet bekleyen haber yapay zeka ile özgünleştirilmek üzere işleme alınıyor (Gecikme: {delay}s)..."))

        success_count = 0
        error_count = 0

        for idx, item in enumerate(qs, start=1):
            fed_name = item.federasyon_website.ad if item.federasyon_website else "Genel"
            clean_title = ' '.join(item.baslik.split())[:45]
            self.stdout.write(f"[{idx}/{total}] ID #{item.id:4d} | {fed_name[:25]:25s} | {clean_title}...")

            ok, res = ozgunlestir_haber(item, ton='standart')
            if ok:
                item.refresh_from_db()
                score = item.haber_degeri_skoru or 0
                badge = "🔥" if score >= 75 else "⚡" if score >= 50 else "💤"
                self.stdout.write(self.style.SUCCESS(f"   -> {badge} Skor: {score:2d}/100 | {item.ozgun_baslik[:55]}"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR(f"   -> ❌ Hata: {str(res)[:80]}"))
                error_count += 1

            if idx < total and delay > 0:
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(f"\n🏁 İŞLEM TAMAMLANDI: {success_count} başarılı, {error_count} hatalı."))
