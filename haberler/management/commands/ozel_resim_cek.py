from django.core.management.base import BaseCommand
from haberler.models import Haber
from haberler.services.news_scraper import NewsScrapingService
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os

class Command(BaseCommand):
    help = 'Her haberin kendi sayfasından özel resimlerini çek ve değiştir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='İşlenecek haber sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Tüm haberleri işle'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        process_all = options['all']
        
        # Kaynak URL'si olan haberleri bul
        queryset = Haber.objects.filter(
            kaynak_url__isnull=False,
            yayinlandi=True
        ).exclude(kaynak_url='')
        
        if not process_all:
            queryset = queryset[:limit]
        
        haberler = queryset
        
        if not haberler.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  İşlenecek haber bulunamadı.')
            )
            return
        
        self.stdout.write(f'🎯 {haberler.count()} haber için özel resimler çekiliyor...\n')
        
        success_count = 0
        failed_count = 0
        
        for haber in haberler:
            try:
                self.stdout.write(f'📰 İşleniyor: {haber.baslik[:50]}...')
                
                # Mevcut resmi sil
                if haber.resim:
                    old_image = haber.resim
                    haber.resim.delete(save=False)
                    self.stdout.write(f'   🗑️  Eski resim silindi')
                
                # Haber sayfasından özel resim çek
                success = self._get_article_specific_image(haber)
                
                if success:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Özel resim eklendi: {haber.resim.name}')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Özel resim bulunamadı')
                    )
                
                time.sleep(2)  # Rate limiting
                
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

    def _get_article_specific_image(self, haber):
        """Haberin kendi sayfasından özel resim çek"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(haber.kaynak_url, timeout=30, headers=headers, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Karate.gov.tr özel selektorları
            if 'karate.gov.tr' in haber.kaynak_url:
                self.stdout.write(f'   🥋 karate.gov.tr sitesi tespit edildi')
                return self._get_karate_gov_tr_image(soup, haber)
            
            # Genel haber sayfası resim selektorları
            image_selectors = [
                # Ana içerik resimleri
                '.haber-resim img',
                '.news-image img', 
                '.article-image img',
                '.content-image img',
                'article img:first-of-type',
                '.post-content img:first-of-type',
                '.entry-content img:first-of-type',
                '.news-detail img:first-of-type',
                
                # Galeri resimleri
                '.gallery img:first-of-type',
                '.slider img:first-of-type',
                '.carousel img:first-of-type',
                
                # Genel resimler (logo olmayan)
                'main img[src*="jpg"], main img[src*="jpeg"], main img[src*="png"]',
                '.container img[src*="jpg"], .container img[src*="jpeg"], .container img[src*="png"]'
            ]
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src and self._is_valid_article_image(img, src, haber.baslik):
                        full_url = urljoin(haber.kaynak_url, src)
                        if self._download_and_save_image(full_url, haber):
                            return True
            
            return False
            
        except Exception as e:
            print(f"Article image extraction error for {haber.baslik}: {e}")
            return False

    def _get_karate_gov_tr_image(self, soup, haber):
        """karate.gov.tr sitesinden özel resim çek"""
        try:
            self.stdout.write(f'   🔍 Karate.gov.tr için özel resim arama başlıyor...')
            
            # Öncelik sırası: haber-detay-image (ana resim), sonra fotogaleri resimleri
            priority_selectors = [
                # Ana haber resmi
                'img.haber-detay-image',
                '.haber-detay-image',
                
                # Haber klasöründeki resimler
                'img[src*="/uploads/haberler/"][src*="IMG"]',
                'img[src*="/uploads/haberler/"][src*=".jpg"]',
                'img[src*="/uploads/haberler/"][src*=".jpeg"]',
                
                # Fotogaleri resimleri
                'img[src*="/fotogaleri/"]',
                'img[src*="/uploads/haberler/fotogaleri/"]',
                
                # Genel haber resimleri
                'img[src*="/uploads/haberler/"]'
            ]
            
            for i, selector in enumerate(priority_selectors):
                self.stdout.write(f'   🔎 Selector {i+1}/{len(priority_selectors)}: {selector}')
                images = soup.select(selector)
                self.stdout.write(f'   📊 Bulunan resim sayısı: {len(images)}')
                
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        self.stdout.write(f'   🎨 İncelenen resim: {src}')
                        
                        # Skip background images, logos, and loading gifs
                        if any(skip in src.lower() for skip in ['arkaplan', 'logo', 'yukleniyor', 'loading']):
                            self.stdout.write(f'   ⚠️ Atlandı (gereksiz): {src}')
                            continue
                        
                        # Skip very small images (likely icons)
                        if any(size in src.lower() for size in ['icon', 'thumb', 'small']):
                            self.stdout.write(f'   ⚠️ Atlandı (küçük): {src}')
                            continue
                            
                        full_url = urljoin(haber.kaynak_url, src)
                        
                        # karate.gov.tr için özel URL düzenlemesi
                        if 'karate.gov.tr' in haber.kaynak_url and not src.startswith('http'):
                            # Relative path'i ana domain ile birleştir
                            if src.startswith('tema/'):
                                full_url = f'https://karate.gov.tr/{src}'
                            else:
                                full_url = urljoin('https://karate.gov.tr/', src)
                        
                        self.stdout.write(f'   🌐 Tam URL: {full_url}')
                        
                        # URL'nin erişilebilir olup olmadığını kontrol et
                        try:
                            head_response = requests.head(full_url, timeout=10, verify=False)
                            self.stdout.write(f'   🔍 HTTP Status: {head_response.status_code}')
                            if head_response.status_code == 200:
                                self.stdout.write(f'   🎯 Deneniyor: {src}')
                                if self._download_and_save_image(full_url, haber):
                                    self.stdout.write(f'   ✅ BAŞARILI!')
                                    return True
                                else:
                                    self.stdout.write(f'   🚫 İndirme başarısız')
                        except Exception as e:
                            self.stdout.write(f'   ❌ URL erişim hatası: {src} - {e}')
                            continue
            
            self.stdout.write(f'   😞 Hiçbir uygun resim bulunamadı')
            return False
            
        except Exception as e:
            self.stdout.write(f'   ❌ Karate.gov.tr resim çekme hatası: {e}')
            return False

    def _is_valid_article_image(self, img_tag, src, title):
        """Resmin makale için uygun olup olmadığını kontrol et"""
        src_lower = src.lower()
        
        # Atlanacak resim türleri
        skip_patterns = [
            'logo', 'icon', 'favicon', 'banner', 'header',
            'footer', 'social', 'share', 'avatar', 'profile',
            'advertisement', 'ads', 'sponsor', 'partner',
            'pixel', 'tracking', 'spacer', 'separator',
            'background', 'bg', 'arkaplan'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False
        
        # Çok küçük resimleri atla
        width = img_tag.get('width')
        height = img_tag.get('height')
        if width and height:
            try:
                w, h = int(width), int(height)
                if w < 200 or h < 150:
                    return False
            except:
                pass
        
        # Alt text kontrolü
        alt_text = (img_tag.get('alt') or '').lower()
        if any(skip in alt_text for skip in ['logo', 'icon', 'banner']):
            return False
        
        # Geçerli resim formatları
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not any(ext in src_lower for ext in valid_extensions):
            return False
        
        return True

    def _download_and_save_image(self, image_url, haber):
        """Resmi indir ve kaydet"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': haber.kaynak_url
            }
            
            response = requests.get(image_url, timeout=30, stream=True, headers=headers, verify=False)
            response.raise_for_status()
            
            # Content type kontrolü
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False
            
            # NewsScrapingService kullanarak resmi işle ve kaydet
            scraper = NewsScrapingService()
            
            # Turkish character encoding fix
            try:
                image_file = scraper.download_and_process_image(image_url, haber.baslik)
            except UnicodeEncodeError:
                # Fallback: use safe title without Turkish characters
                safe_title = haber.baslik.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ö', 'o')
                image_file = scraper.download_and_process_image(image_url, safe_title)
            
            if image_file:
                haber.resim.save(image_file.name, image_file, save=True)
                return True
            
            return False
            
        except Exception as e:
            print(f"Image download error for {image_url}: {e}")
            return False