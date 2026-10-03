from django.core.management.base import BaseCommand
from django.db import transaction
from haberler.models import Haber, Kategori
from django.core.files.base import ContentFile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import io
from PIL import Image
import uuid
from django.utils.text import slugify
import time

class Command(BaseCommand):
    help = 'Karate haberlerindeki generated fotoğrafları federasyon sitesindeki orijinal fotoğraflarla değiştir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='İşlenecek haber sayısı (varsayılan: 50)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write('📸 FEDERASYON ORİJİNAL FOTOĞRAF İNDİRİCİ')
        self.stdout.write('=' * 60)
        
        # Karate kategorisindeki haberleri al
        try:
            karate_kategori = Kategori.objects.get(slug='karate')
            self.stdout.write(f'✅ Karate kategorisi bulundu: {karate_kategori.ad}')
        except Kategori.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Karate kategorisi bulunamadı'))
            return
        
        # Generated fotoğraflı haberleri bul
        karate_haberler = Haber.objects.filter(
            kategori=karate_kategori,
            kaynak_url__isnull=False,
            resim__isnull=False
        ).exclude(kaynak_url='')
        
        if limit > 0:
            karate_haberler = karate_haberler[:limit]
        
        self.stdout.write(f'🔍 {karate_haberler.count()} karate haberi işlenecek')
        
        success_count = 0
        failed_count = 0
        
        for i, haber in enumerate(karate_haberler, 1):
            try:
                self.stdout.write(f'\\n[{i}/{karate_haberler.count()}] 📰 {haber.baslik[:50]}...')
                self.stdout.write(f'🔗 Kaynak: {haber.kaynak_url}')
                
                # Orijinal fotoğrafı bul ve indir
                original_photo = self._download_original_federation_photo(haber)
                
                if original_photo:
                    # Eski resmi sil
                    if haber.resim:
                        old_name = haber.resim.name
                        haber.resim.delete(save=False)
                        self.stdout.write(f'   🗑️  Eski resim silindi: {old_name}')
                    
                    # Yeni orijinal resmi kaydet
                    haber.resim.save(original_photo.name, original_photo, save=True)
                    success_count += 1
                    self.stdout.write(f'   ✅ Orijinal federasyon fotoğrafı eklendi: {original_photo.name}')
                else:
                    failed_count += 1
                    self.stdout.write('   ❌ Orijinal fotoğraf bulunamadı')
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(f'   ❌ Hata: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\\n🎉 İşlem tamamlandı!\\n'
                f'   ✅ {success_count} orijinal fotoğraf indirildi\\n'
                f'   ❌ {failed_count} başarısız'
            )
        )

    def _download_original_federation_photo(self, haber):
        """Federasyon sitesinden orijinal fotoğrafı indir"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Haber sayfasını çek
            response = requests.get(haber.kaynak_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Federasyon sitesine özel görsel selektörleri
            image_selectors = [
                # Ana haber resmi
                'img.haber-detay-image',
                'img.haber-image',
                '.haber-detay-icerik img',
                '.news-detail img',
                
                # İçerik alanındaki resimler
                '.content img',
                'article img',
                'main img',
                '.container img',
                
                # Haber ile ilgili resimler
                'img[src*=\"upload\"]',
                'img[src*=\"haber\"]',
                'img[src*=\"resim\"]',
                'img[src*=\"foto\"]',
                'img[src*=\"galeri\"]',
                
                # Genel img tagları
                'img[alt*=\"haber\"]',
                'img[alt*=\"foto\"]',
                'img[width], img[height]'  # Boyutu olan resimler
            ]
            
            best_image_url = None
            best_score = 0
            
            # Her selektörü dene
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    
                    if not src:
                        continue
                    
                    # Tam URL oluştur
                    if src.startswith('/'):
                        image_url = f'https://karate.gov.tr{src}'
                    elif src.startswith('//'):
                        image_url = f'https:{src}'  
                    elif src.startswith('http'):
                        image_url = src
                    else:
                        image_url = urljoin(haber.kaynak_url, src)
                    
                    # Resim geçerliliğini ve kalitesini puanla
                    score = self._score_federation_image(img, src, haber.baslik)
                    
                    if score > best_score and score > 10:  # Minimum threshold
                        best_score = score
                        best_image_url = image_url
            
            if not best_image_url:
                return None
            
            self.stdout.write(f'   📷 En iyi resim bulundu (puan: {best_score}): {best_image_url}')
            
            # Resmi indir
            img_response = requests.get(best_image_url, headers=headers, timeout=30, verify=False)
            img_response.raise_for_status()
            
            # Resim boyutunu kontrol et
            if len(img_response.content) < 1024:  # 1KB'dan küçük
                self.stdout.write('   ⚠️  Resim çok küçük, atlanıyor')
                return None
            
            # PIL ile işle
            image = Image.open(io.BytesIO(img_response.content))
            
            # Çok küçük resimleri filtrele
            if image.width < 100 or image.height < 100:
                self.stdout.write(f'   ⚠️  Resim boyutu çok küçük ({image.width}x{image.height})')
                return None
            
            # RGB'ye çevir
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Makul boyuta getir (orijinal kalitesini koru)
            max_width = 1200
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Yüksek kalitede kaydet
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Dosya adı oluştur
            safe_title = slugify(haber.baslik)[:30]
            unique_id = str(uuid.uuid4())[:8]
            filename = f"federation_original_{safe_title}_{unique_id}.jpg"
            
            return ContentFile(output.read(), name=filename)
            
        except Exception as e:
            self.stdout.write(f'   ❌ Fotoğraf indirme hatası: {e}')
            return None

    def _score_federation_image(self, img_tag, src, title):
        """Federasyon resminin kalitesini ve uygunluğunu puanla"""
        score = 0
        src_lower = src.lower()
        alt = img_tag.get('alt', '').lower()
        title_lower = title.lower()
        
        # Atlanacak resimler (negatif puan)
        skip_patterns = [
            'logo', 'icon', 'favicon', 'banner', 'header', 'footer',
            'menu', 'nav', 'button', 'arrow', 'background', 'bg',
            'social', 'share', 'print', 'email', 'facebook', 'twitter'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower or pattern in alt:
                return -100
        
        # Federasyon upload klasöründeki resimler (yüksek puan)
        if '/upload' in src_lower or '/tema/genel/upload' in src_lower:
            score += 100
        
        # Haber klasöründeki resimler
        if '/haber' in src_lower or '/news' in src_lower:
            score += 80
        
        # Galeri resimleri
        if '/galeri' in src_lower or '/fotogaleri' in src_lower:
            score += 60
        
        # Resim formatı tercihi
        if src_lower.endswith(('.jpg', '.jpeg')):
            score += 30
        elif src_lower.endswith('.png'):
            score += 20
        elif src_lower.endswith('.webp'):
            score += 10
        
        # Boyut ipuçları (büyük resimler tercih)
        width = img_tag.get('width')
        height = img_tag.get('height')
        
        if width and height:
            try:
                w, h = int(width), int(height)
                if w >= 300 and h >= 200:
                    score += 40
                elif w >= 200 and h >= 150:
                    score += 20
                elif w < 100 or h < 100:
                    score -= 50
            except ValueError:
                pass
        
        # Alt text ve src'de haber ile ilgili kelimeler
        title_words = [word for word in title_lower.split() if len(word) > 3]
        for word in title_words:
            if word in src_lower:
                score += 15
            if word in alt:
                score += 10
        
        # Karate ile ilgili terimler
        karate_terms = ['karate', 'kata', 'kumite', 'şampiyon', 'sporcu', 
                       'antrenör', 'federasyon', 'müsabaka', 'turnuva']
        for term in karate_terms:
            if term in alt:
                score += 15
            if term in src_lower:
                score += 10
        
        return score