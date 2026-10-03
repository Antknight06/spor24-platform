from django.core.management.base import BaseCommand
from haberler.models import Haber
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class Command(BaseCommand):
    help = 'Eray Şamdan haberlerinin resimlerini kontrol et ve düzelt'

    def handle(self, *args, **options):
        self.stdout.write('🔍 ERAY ŞAMDAN HABER KONTROLÜ')
        self.stdout.write('=' * 40)
        
        # Eray Şamdan ile ilgili haberleri bul
        eray_haberler = Haber.objects.filter(
            baslik__icontains='eray',
            kaynak_url__isnull=False
        )
        
        if not eray_haberler.exists():
            self.stdout.write('❌ Eray Şamdan haberı bulunamadı')
            return
        
        for haber in eray_haberler:
            self.stdout.write(f'\n📰 {haber.baslik}')
            self.stdout.write(f'🖼️  Mevcut resim: {haber.resim.name if haber.resim else "YOK"}')
            self.stdout.write(f'🔗 Kaynak URL: {haber.kaynak_url}')
            
            # Sayfadaki resmi kontrol et
            if 'karate.gov.tr' in haber.kaynak_url:
                actual_images = self._get_all_images_from_page(haber.kaynak_url)
                if actual_images:
                    self.stdout.write('📸 Sayfadaki tüm resimler:')
                    for i, img in enumerate(actual_images, 1):
                        self.stdout.write(f'  {i}. {img}')
                else:
                    self.stdout.write('⚠️  Sayfada resim bulunamadı')

    def _get_all_images_from_page(self, url):
        """Sayfadaki tüm haber resimlerini listele"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, timeout=15, headers=headers, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Haber ile ilgili tüm resimleri bul
            image_urls = []
            
            # Ana haber resmi
            main_selectors = [
                'img.haber-detay-image',
                '.haber-detay-image'
            ]
            
            for selector in main_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src')
                    if src and self._is_news_image(src):
                        image_urls.append(src)
            
            # Haber klasöründeki diğer resimler
            other_selectors = [
                'img[src*="/uploads/haberler/"]'
            ]
            
            for selector in other_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src')
                    if src and self._is_news_image(src) and src not in image_urls:
                        image_urls.append(src)
            
            return image_urls
            
        except Exception as e:
            return []

    def _is_news_image(self, src):
        """Haber resmi olup olmadığını kontrol et"""
        src_lower = src.lower()
        
        # Skip patterns
        skip_patterns = [
            'logo', 'arkaplan', 'icon', 'yukleniyor', 'loading'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False
        
        return '/uploads/haberler/' in src_lower