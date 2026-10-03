from django.core.management.base import BaseCommand
from haberler.models import Haber
from haberler.services.news_scraper import NewsScrapingService
import time

class Command(BaseCommand):
    help = 'Mevcut haberlere kaynak sitelerinden resim indir ve ekle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='İşlenecek haber sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--only-scraped',
            action='store_true',
            help='Sadece otomatik çekilen haberleri işle'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        only_scraped = options['only_scraped']
        
        # Resmi olmayan haberleri bul
        queryset = Haber.objects.filter(
            resim__isnull=True,
            kaynak_url__isnull=False,
            yayinlandi=True
        ).exclude(kaynak_url='')
        
        if only_scraped:
            queryset = queryset.filter(otomatik_eklendi=True)
        
        haberler = queryset[:limit]
        
        if not haberler.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  Resmi olmayan haber bulunamadı.')
            )
            return
        
        self.stdout.write(f'🖼️  {haberler.count()} haber için resim indiriliyor...\n')
        
        scraper = NewsScrapingService()
        success_count = 0
        failed_count = 0
        
        for haber in haberler:
            try:
                self.stdout.write(f'📰 İşleniyor: {haber.baslik[:50]}...')
                
                # Haberin kaynak URL'sinden resim çek
                image_urls = scraper.get_news_images(haber.kaynak_url)
                
                if not image_urls:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Resim bulunamadı')
                    )
                    failed_count += 1
                    continue
                
                # İlk resmi indir ve işle
                image_file = scraper.download_and_process_image(
                    image_urls[0], haber.baslik
                )
                
                if image_file:
                    haber.resim.save(image_file.name, image_file, save=True)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Resim eklendi: {image_file.name}')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Resim indirilemedi')
                    )
                
                # Nazik bir bekleme süresi
                time.sleep(2)
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! '
                f'✅ {success_count} başarılı, ❌ {failed_count} başarısız'
            )
        )