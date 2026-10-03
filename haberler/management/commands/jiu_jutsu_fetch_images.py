from django.core.management.base import BaseCommand
from django.db.models import Q
from haberler.models import Haber
from haberler.services.news_scraper import NewsScrapingService


class Command(BaseCommand):
    help = 'Jiu Jutsu (jujitsuturkiye.com) haberlerinde eksik görselleri sayfadan çekip ekler'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=300, help='İşlenecek maksimum haber sayısı')

    def handle(self, *args, **options):
        limit = options['limit']

        self.stdout.write('🥋 JIU JUTSU GÖRSEL TAMAMLAMA')
        self.stdout.write('=' * 40)

        qs = Haber.objects.filter(
            Q(kaynak_url__icontains='jujitsuturkiye.com'),
            Q(resim__isnull=True)
        ).order_by('-olusturma_tarihi')
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f'📊 Aday haber: {total}')
        if total == 0:
            return

        scraper = NewsScrapingService()
        # trust site with no SSL verify if needed
        try:
            scraper.session.verify = False
        except Exception:
            pass

        attached = 0
        for i, haber in enumerate(qs, 1):
            try:
                self.stdout.write(f"[{i}/{total}] {haber.baslik[:60]}...")
                image_urls = scraper.get_news_images(haber.kaynak_url)
                if not image_urls:
                    self.stdout.write('   ⚠️  Resim bulunamadı')
                    continue
                img_file = scraper.download_and_process_image(image_urls[0], haber.baslik)
                if img_file:
                    haber.resim.save(img_file.name, img_file, save=True)
                    attached += 1
                    self.stdout.write('   🖼️  Resim eklendi')
                else:
                    self.stdout.write('   ⚠️  Resim indirilemedi')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Hata: {e}')
                continue

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Tamamlandı: {attached} habere resim eklendi"))


