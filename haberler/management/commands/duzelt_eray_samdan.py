from django.core.management.base import BaseCommand
from haberler.models import Haber
from haberler.services.news_scraper import NewsScrapingService
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

class Command(BaseCommand):
    help = 'Eray Şamdan haberlerinin doğru resimlerle eşleştirilmesini sağla'

    def handle(self, *args, **options):
        # Eray Şamdan ile ilgili haberleri bul
        eray_haberler = Haber.objects.filter(
            baslik__icontains='eray',
            kaynak_url__isnull=False
        )
        
        if not eray_haberler.exists():
            self.stdout.write('❌ Eray Şamdan haberı bulunamadı')
            return
        
        self.stdout.write(f'🏆 {eray_haberler.count()} Eray Şamdan haberı için resim düzeltmesi başlıyor...\n')
        
        success_count = 0
        
        for haber in eray_haberler:
            self.stdout.write(f'📰 İşleniyor: {haber.baslik}')
            
            # Mevcut resmi sil
            if haber.resim:
                old_image = haber.resim.name
                haber.resim.delete(save=False)
                self.stdout.write(f'   🗑️  Eski resim silindi: {old_image}')
            
            # Bu Eray Şamdan haberinin kendi sayfasındaki Eray'ın resmini al
            success = self._get_eray_specific_image(haber)
            
            if success:
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Eray Şamdan resmi atandı: {haber.resim.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  Eray Şamdan resmi bulunamadı')
                )
            
            time.sleep(2)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Eray Şamdan resim düzeltmesi tamamlandı! '
                f'✅ {success_count}/{eray_haberler.count()} başarılı'
            )
        )

    def _get_eray_specific_image(self, haber):
        """Eray Samdan'in gercek resmini bul ve ata"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(haber.kaynak_url, timeout=30, headers=headers, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Eray Şamdan'ın resmini bul - öncelikle kişisel fotoğraflar
            eray_image_patterns = [
                # Kişi fotoğrafları (social media formatları)
                'img[src*="528045026"]',  # Eray'ın bilinen foto ID'si
                'img[src*="528647176"]',  # Alternatif foto
                'img[src*="528817994"]',  # Başka alternatif
                
                # Ana haber resmi (eğer Eray'ın fotoğrafıysa)
                'img.haber-detay-image',
                '.haber-detay-image'
            ]
            
            for pattern in eray_image_patterns:
                images = soup.select(pattern)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and self._is_eray_photo(src):
                        full_url = self._build_url(src, haber.kaynak_url)
                        self.stdout.write(f'   🎯 Eray resmi bulundu: {src}')
                        return self._download_and_assign(full_url, haber)
            
            # Eğer özel Eray fotoğrafı bulunamazsa, ana haber resmini al
            main_images = soup.select('img.haber-detay-image, .haber-detay-image')
            if main_images:
                img = main_images[0]
                src = img.get('src') or img.get('data-src')
                if src and '/uploads/haberler/' in src:
                    full_url = self._build_url(src, haber.kaynak_url)
                    self.stdout.write(f'   📸 Ana resim alınıyor: {src}')
                    return self._download_and_assign(full_url, haber)
            
            return False
            
        except Exception as e:
            self.stdout.write(f'   ❌ Hata: {e}')
            return False

    def _is_eray_photo(self, src):
        """Resmin Eray Samdan'in fotografi olup olmadigini kontrol et"""
        src_lower = src.lower()
        
        # Eray'ın bilinen foto ID'leri
        eray_photo_ids = [
            '528045026',  # Şampiyonluk fotoğrafı
            '528647176',  # Alternatif fotoğraf
            '528817994',  # Başka fotoğraf
            'img_4332',   # Potansiyel Eray fotoğrafı
            'img_4804',   # Galeri fotoğrafı
            'img_4801',   # Galeri fotoğrafı
            'img_4803'    # Galeri fotoğrafı
        ]
        
        for photo_id in eray_photo_ids:
            if photo_id in src_lower:
                return True
        
        # Genel haber resmi olabilir
        return '/uploads/haberler/' in src_lower

    def _build_url(self, src, base_url):
        """Dogru tam URL olustur"""
        if src.startswith('http'):
            return src
        elif src.startswith('tema/'):
            return f'https://karate.gov.tr/{src}'
        else:
            return urljoin(base_url, src)

    def _download_and_assign(self, image_url, haber):
        """Resmi indir ve habere ata"""
        try:
            # URL erişilebilirlik kontrolü
            head_response = requests.head(image_url, timeout=10, verify=False)
            if head_response.status_code != 200:
                return False
            
            # Resmi indir
            scraper = NewsScrapingService()
            
            try:
                image_file = scraper.download_and_process_image(image_url, haber.baslik)
            except UnicodeEncodeError:
                # Turkish character fix
                safe_title = (haber.baslik
                             .replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u')
                             .replace('ş', 's').replace('ç', 'c').replace('ö', 'o'))
                image_file = scraper.download_and_process_image(image_url, safe_title)
            
            if image_file:
                haber.resim.save(image_file.name, image_file, save=True)
                return True
            
            return False
            
        except Exception as e:
            self.stdout.write(f'   ❌ Indirme hatasi: {e}')
            return False