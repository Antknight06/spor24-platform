from django.core.management.base import BaseCommand
from haberler.models import Haber
import requests
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = 'Haber sayfalarının yapısını analiz et'

    def handle(self, *args, **options):
        # Kaynak URL'si olan bir haber al
        haber = Haber.objects.filter(
            kaynak_url__isnull=False,
            kaynak_url__contains='karate.gov.tr'
        ).first()
        
        if not haber:
            self.stdout.write('Karate.gov.tr haberı bulunamadı')
            return
        
        self.stdout.write(f'📰 Analiz edilen haber: {haber.baslik}')
        self.stdout.write(f'🔗 URL: {haber.kaynak_url}')
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(haber.kaynak_url, timeout=30, headers=headers, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            self.stdout.write('\n🖼️  SAYFA ÜZERİNDEKİ TÜM RESİMLER:')
            self.stdout.write('=' * 50)
            
            images = soup.find_all('img')
            for i, img in enumerate(images[:20], 1):
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', 'Alt text yok')
                width = img.get('width', 'Bilinmiyor')
                height = img.get('height', 'Bilinmiyor')
                
                self.stdout.write(f'\n{i}. Resim:')
                self.stdout.write(f'   SRC: {src}')
                self.stdout.write(f'   ALT: {alt}')
                self.stdout.write(f'   Boyut: {width}x{height}')
                
                # CSS sınıflarını göster
                classes = img.get('class', [])
                if classes:
                    self.stdout.write(f'   CSS: {" ".join(classes)}')
            
            self.stdout.write('\n📄 SAYFA YAPISI:')
            self.stdout.write('=' * 30)
            
            # Ana içerik alanlarını bul
            content_areas = [
                ('article', soup.find('article')),
                ('.content', soup.select_one('.content')),
                ('.haber-detay', soup.select_one('.haber-detay')),
                ('.news-detail', soup.select_one('.news-detail')),
                ('main', soup.find('main')),
                ('.container', soup.select_one('.container'))
            ]
            
            for name, element in content_areas:
                if element:
                    inner_images = element.find_all('img')
                    self.stdout.write(f'{name}: {len(inner_images)} resim bulundu')
            
        except Exception as e:
            self.stdout.write(f'❌ Hata: {e}')