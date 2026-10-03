from django.core.management.base import BaseCommand
from haberler.models import Haber
from haberler.services.news_scraper import NewsScrapingService
import requests
from django.core.files.base import ContentFile
import time

class Command(BaseCommand):
    help = 'Resmi olmayan haberlere karate temalı stok resimler ekle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='İşlenecek haber sayısı (varsayılan: 10)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        # Resmi olmayan haberleri bul
        haberler = Haber.objects.filter(
            resim__isnull=True,
            yayinlandi=True
        )[:limit]
        
        if not haberler.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ Tüm haberler zaten resme sahip!')
            )
            return
        
        self.stdout.write(f'🥋 {haberler.count()} haber için karate temalı resim ekleniyor...\n')
        
        # Karate ile ilgili genel resim URL'leri (açık kaynak veya creative commons)
        karate_images = [
            "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=800&q=80",  # Karate training
            "https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?w=800&q=80",  # Martial arts
            "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80",  # Karate kick
            "https://images.unsplash.com/photo-1594736797933-d0401ba6fe65?w=800&q=80",  # Martial arts training
            "https://images.unsplash.com/photo-1555597467-f8c4bf03df5e?w=800&q=80",   # Karate dojo
        ]
        
        success_count = 0
        failed_count = 0
        
        for i, haber in enumerate(haberler):
            try:
                self.stdout.write(f'🥋 İşleniyor: {haber.baslik[:50]}...')
                
                # Döngüsel olarak resim seç
                image_url = karate_images[i % len(karate_images)]
                
                # Resmi indir
                image_file = self._download_stock_image(image_url, haber.baslik)
                
                if image_file:
                    haber.resim.save(image_file.name, image_file, save=True)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Stok resim eklendi')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Resim indirilemedi')
                    )
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! '
                f'✅ {success_count} başarılı, ⚠️ {failed_count} başarısız'
            )
        )

    def _download_stock_image(self, image_url, news_title):
        """Stok resim indir"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, timeout=30, stream=True, headers=headers)
            response.raise_for_status()
            
            # Content type kontrolü
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
            
            # Resim içeriğini al
            image_content = response.content
            
            # Dosya adı oluştur
            from django.utils.text import slugify
            import uuid
            safe_title = slugify(news_title)[:30]
            unique_id = str(uuid.uuid4())[:8]
            filename = f"stock_karate_{safe_title}_{unique_id}.jpg"
            
            return ContentFile(image_content, name=filename)
            
        except Exception as e:
            print(f"Stock image download error: {e}")
            return None