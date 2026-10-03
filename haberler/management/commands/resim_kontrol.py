from django.core.management.base import BaseCommand
from haberler.models import Haber
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class Command(BaseCommand):
    help = 'Haberlerin resimlerinin doğru olup olmadığını kontrol et'

    def handle(self, *args, **options):
        self.stdout.write('🔍 HBR-RESİM UYUMLULUĞU KONTROLÜ')
        self.stdout.write('=' * 50)
        
        # Kaynak URL'si olan haberleri al
        haberler = Haber.objects.filter(
            kaynak_url__isnull=False,
            resim__isnull=False
        ).exclude(kaynak_url='')[:10]
        
        for haber in haberler:
            self.stdout.write(f'\n📰 {haber.baslik[:50]}...')
            self.stdout.write(f'🖼️  Mevcut resim: {haber.resim.name}')
            self.stdout.write(f'🔗 Kaynak URL: {haber.kaynak_url}')
            
            # Sayfadaki gerçek resmi kontrol et
            if 'karate.gov.tr' in haber.kaynak_url:
                actual_image = self._get_actual_image_from_page(haber.kaynak_url)
                if actual_image:
                    self.stdout.write(f'✅ Sayfadaki gerçek resim: {actual_image}')
                    
                    # Resim adlarını karşılaştır
                    current_image_base = haber.resim.name.split('/')[-1].split('_')[1] if '_' in haber.resim.name else haber.resim.name
                    actual_image_base = actual_image.split('/')[-1]
                    
                    if actual_image_base in current_image_base or current_image_base in actual_image_base:
                        self.stdout.write('✅ DOĞRU RESIM')
                    else:
                        self.stdout.write('❌ YANLIŞ RESIM!')
                        self.stdout.write(f'   Olması gereken: {actual_image}')
                else:
                    self.stdout.write('⚠️  Sayfada resim bulunamadı')
            else:
                self.stdout.write('ℹ️  karate.gov.tr dışı kaynak')

    def _get_actual_image_from_page(self, url):
        """Sayfadaki gerçek ana resmi bul"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, timeout=15, headers=headers, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ana haber resmini bul
            selectors = [
                'img.haber-detay-image',
                '.haber-detay-image',
                'img[src*="/uploads/haberler/"][src*="IMG"]',
                'img[src*="/uploads/haberler/"][src*=".jpg"]',
                'img[src*="/uploads/haberler/"][src*=".jpeg"]'
            ]
            
            for selector in selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src')
                    if src and 'arkaplan' not in src.lower() and 'logo' not in src.lower():
                        return src
            
            return None
            
        except Exception as e:
            return None