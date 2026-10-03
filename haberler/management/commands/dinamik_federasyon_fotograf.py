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
import re
import json

class Command(BaseCommand):
    help = 'Karate federasyon fotoğrafları için gelişmiş indirici - JavaScript ve dinamik yükleme destekli'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='İşlenecek haber sayısı (varsayılan: 20)'
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Test modu - sadece ilk 3 haberi işle'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        test_mode = options['test_mode']
        
        if test_mode:
            limit = 3
        
        self.stdout.write('🔍 DİNAMİK FEDERASYON FOTOĞRAF İNDİRİCİ')
        self.stdout.write('=' * 60)
        self.stdout.write('🎯 JavaScript ve dinamik yükleme destekli')
        
        # Karate kategorisindeki haberleri al
        try:
            karate_kategori = Kategori.objects.get(slug='karate')
            self.stdout.write(f'✅ Karate kategorisi bulundu: {karate_kategori.ad}')
        except Kategori.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Karate kategorisi bulunamadı'))
            return
        
        # Federasyon kaynaklı haberleri bul
        karate_haberler = Haber.objects.filter(
            kategori=karate_kategori,
            kaynak_url__icontains='karate.gov.tr'
        )
        
        if limit > 0:
            karate_haberler = karate_haberler[:limit]
        
        self.stdout.write(f'🔍 {karate_haberler.count()} karate haberi işlenecek')
        
        if test_mode:
            self.stdout.write(self.style.WARNING('🧪 TEST MODU - Sadece ilk 3 haber'))
        
        success_count = 0
        failed_count = 0
        
        for i, haber in enumerate(karate_haberler, 1):
            try:
                self.stdout.write(f'\n[{i}/{karate_haberler.count()}] 📰 {haber.baslik[:50]}...')
                self.stdout.write(f'🔗 Kaynak: {haber.kaynak_url}')
                
                # Dinamik fotoğraf bulma sistemi
                original_photo = self._find_and_download_dynamic_photo(haber)
                
                if original_photo:
                    # Eski resmi sil
                    if haber.resim:
                        old_name = haber.resim.name
                        haber.resim.delete(save=False)
                        self.stdout.write(f'   🗑️  Eski resim silindi: {old_name}')
                    
                    # Yeni orijinal resmi kaydet
                    haber.resim.save(original_photo.name, original_photo, save=True)
                    success_count += 1
                    self.stdout.write(f'   ✅ Dinamik fotoğraf eklendi: {original_photo.name}')
                else:
                    failed_count += 1
                    self.stdout.write('   ❌ Dinamik fotoğraf bulunamadı')
                
                # Tarih bilgisini federasyon sitesinden çek ve güncelle
                self._update_news_date_from_source(haber)
                
                # Rate limiting - daha düşük
                time.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(f'   ❌ Hata: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı!\n'
                f'   ✅ {success_count} başarılı\n'
                f'   ❌ {failed_count} başarısız'
            )
        )

    def _update_news_date_from_source(self, haber):
        """Haberin tarihini federasyon sitesinden çek ve güncelle"""
        try:
            if not haber.kaynak_url:
                self.stdout.write('   ⏭️  Tarih güncellenemedi: Kaynak URL yok')
                return
            
            # Tarih bilgisini çek
            new_date = self._get_date_from_source(haber.kaynak_url)
            
            if new_date:
                old_date = haber.olusturma_tarihi
                haber.olusturma_tarihi = new_date
                haber.save(update_fields=['olusturma_tarihi'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   📅 Tarih güncellendi: {old_date.strftime("%d.%m.%Y")} → {new_date.strftime("%d.%m.%Y")}'
                    )
                )
            else:
                self.stdout.write('   ⚠️  Tarih bulunamadı')
                
        except Exception as e:
            self.stdout.write(f'   ⚠️  Tarih güncelleme hatası: {e}')

    def _get_date_from_source(self, url):
        """Kaynak URL'den tarih bilgisini çek"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Farklı tarih selektörleri dene
            date_selectors = [
                '.date',
                '.tarih',
                'time',
                '.publish-date',
                '.news-date',
                '.article-date',
                '.post-date',
                '[datetime]',
                '.haber-tarih',
                '.entry-date'
            ]
            
            for selector in date_selectors:
                date_element = soup.select_one(selector)
                if date_element:
                    # datetime attribute'u kontrol et
                    datetime_attr = date_element.get('datetime')
                    if datetime_attr:
                        parsed_date = self._parse_iso_date(datetime_attr)
                        if parsed_date:
                            return parsed_date
                    
                    # Element metnini kontrol et
                    date_text = date_element.get_text(strip=True)
                    if date_text:
                        parsed_date = self._parse_turkish_date(date_text)
                        if parsed_date:
                            return parsed_date
            
            # Meta tag'lerden tarih bilgisi
            meta_date = soup.find('meta', property='article:published_time')
            if meta_date and meta_date.get('content'):
                parsed_date = self._parse_iso_date(meta_date['content'])
                if parsed_date:
                    return parsed_date
            
            # JSON-LD structured data
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    import json
                    data = json.loads(json_ld.string)
                    if isinstance(data, dict) and 'datePublished' in data:
                        parsed_date = self._parse_iso_date(data['datePublished'])
                        if parsed_date:
                            return parsed_date
                except:
                    pass
            
            # Sayfadaki tüm tarih benzeri metinleri ara
            all_text = soup.get_text()
            date_patterns = [
                r'(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s+(\d{4})',
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, all_text.lower())
                if matches:
                    # İlk bulunan tarihleri al
                    for date_match in matches:
                        parsed_date = self._parse_date_groups(date_match, pattern)
                        if parsed_date:
                            return parsed_date
            
            return None
        
        except Exception as e:
            return None

    def _parse_iso_date(self, date_string):
        """ISO 8601 tarih formatını parse et"""
        try:
            from django.utils import timezone
            from datetime import datetime
            
            # Yaygın ISO formatları
            iso_formats = [
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d.%m.%Y %H:%M:%S',
                '%d.%m.%Y'
            ]
            
            # Z suffix'ini +00:00 ile değiştir
            if date_string.endswith('Z'):
                date_string = date_string[:-1] + '+00:00'
            
            for fmt in iso_formats:
                try:
                    dt = datetime.strptime(date_string.split('.')[0], fmt)
                    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None

    def _parse_turkish_date(self, date_text):
        """Türkçe tarih metnini parse et"""
        try:
            from django.utils import timezone
            from datetime import datetime
            
            # Türkçe ay isimleri
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            date_text = date_text.lower().strip()
            
            # Farklı tarih formatları
            patterns = [
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 ocak 2024
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 15.01.2024
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 15/01/2024
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    parsed_date = self._parse_date_groups(groups, pattern)
                    if parsed_date:
                        return parsed_date
            
            return None
        
        except Exception:
            return None

    def _parse_date_groups(self, groups, pattern):
        """Tarih gruplarını parse et"""
        try:
            from django.utils import timezone
            from datetime import datetime
            
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            if 'w+' in pattern or any(month in ''.join(groups) for month in turkish_months.keys()):  # Türkçe ay adı formatı
                day, month_name, year = groups
                month = turkish_months.get(month_name.lower())
                if month:
                    dt = datetime(int(year), month, int(day))
                    return timezone.make_aware(dt)
            else:
                if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                    year, month, day = groups
                else:  # DD.MM.YYYY or DD/MM/YYYY
                    day, month, year = groups
                
                dt = datetime(int(year), int(month), int(day))
                return timezone.make_aware(dt)
            
            return None
        
        except Exception:
            return None

    def _find_and_download_dynamic_photo(self, haber):
        """Dinamik fotoğraf bulma ve indirme sistemi"""
        
        # Strateji 1: Haber ID'sini kullanarak direkt resim arama
        image_url = self._try_direct_image_patterns(haber)
        if image_url:
            self.stdout.write(f'   📍 Direkt pattern buldu: {image_url}')
            return self._download_and_process_image(image_url, haber)
        
        # Strateji 2: Sayfayı analiz et ve JavaScript'ten resim çıkar
        image_url = self._analyze_page_for_images(haber)
        if image_url:
            self.stdout.write(f'   🔍 Sayfa analizinde buldu: {image_url}')
            return self._download_and_process_image(image_url, haber)
        
        # Strateji 3: Galeri sayfalarını kontrol et
        image_url = self._check_gallery_pages(haber)
        if image_url:
            self.stdout.write(f'   🖼️  Galeri sayfasında buldu: {image_url}')
            return self._download_and_process_image(image_url, haber)
        
        # Strateji 4: Site haritası ve feed kontrol et
        image_url = self._check_sitemap_and_feeds(haber)
        if image_url:
            self.stdout.write(f'   🗺️  Site haritasında buldu: {image_url}')
            return self._download_and_process_image(image_url, haber)
            
        return None

    def _try_direct_image_patterns(self, haber):
        """Haber URL'sinden ID çıkarıp direkt resim pattern'leri dene"""
        
        # URL'den haber ID'sini çıkar
        news_id = self._extract_news_id(haber.kaynak_url)
        if not news_id:
            return None
            
        self.stdout.write(f'   🔢 Haber ID: {news_id}')
        
        # Bilinen federasyon resim pattern'leri
        image_patterns = [
            f'https://karate.gov.tr/tema/genel/uploads/haberler/{news_id}.jpg',
            f'https://karate.gov.tr/tema/genel/uploads/haberler/{news_id}.jpeg',
            f'https://karate.gov.tr/tema/genel/uploads/haberler/{news_id}.png',
            f'https://karate.gov.tr/uploads/haberler/{news_id}.jpg',
            f'https://karate.gov.tr/uploads/haberler/{news_id}.jpeg',
            f'https://karate.gov.tr/resimler/haber/{news_id}.jpg',
            f'https://karate.gov.tr/resimler/haber/{news_id}.jpeg',
            # UUID-based patterns (önceki test sonuçlarından)
            f'https://karate.gov.tr/tema/genel/uploads/haberler/{news_id}-*'
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': haber.kaynak_url
        }
        
        for pattern in image_patterns:
            try:
                # UUID pattern için özel işlem
                if '*' in pattern:
                    continue  # Şimdilik atla
                
                self.stdout.write(f'     🔄 Test: {pattern}')
                response = requests.head(pattern, headers=headers, timeout=10, verify=False)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type:
                        return pattern
                    
            except Exception as e:
                continue
                
        return None

    def _extract_news_id(self, url):
        """URL'den haber ID'sini çıkar"""
        # Farklı URL pattern'leri dene
        patterns = [
            r'/haber/[^-]+-(\d+)',  # /haber/title-123
            r'/haber-(\d+)',        # /haber-123  
            r'id=(\d+)',            # ?id=123
            r'/(\d+)/?$',           # /123 (URL sonu)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def _analyze_page_for_images(self, haber):
        """Sayfayı detaylı analiz et ve gizli resimleri bul"""
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(haber.kaynak_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Data attribute'ları kontrol et
            image_url = self._find_data_attributes(soup)
            if image_url:
                return image_url
            
            # Method 2: JavaScript içindeki URL'leri bul
            image_url = self._find_script_images(soup, haber.kaynak_url)
            if image_url:
                return image_url
                
            # Method 3: CSS background-image'leri kontrol et
            image_url = self._find_css_background_images(soup)
            if image_url:
                return image_url
            
            # Method 4: Meta tag'lerde resim ara
            image_url = self._find_meta_images(soup)
            if image_url:
                return image_url
                
            return None
            
        except Exception as e:
            self.stdout.write(f'   ❌ Sayfa analiz hatası: {e}')
            return None

    def _find_data_attributes(self, soup):
        """Data attribute'larda saklı image URL'leri bul"""
        
        data_selectors = [
            '[data-src]', '[data-image]', '[data-background]',
            '[data-lazy]', '[data-original]', '[data-url]',
            '[data-img]', '[data-photo]'
        ]
        
        for selector in data_selectors:
            elements = soup.select(selector)
            for elem in elements:
                for attr in ['data-src', 'data-image', 'data-background', 
                           'data-lazy', 'data-original', 'data-url', 
                           'data-img', 'data-photo']:
                    url = elem.get(attr)
                    if url and self._is_valid_image_url(url):
                        full_url = self._build_full_url(url)
                        if full_url:
                            self.stdout.write(f'     📋 Data attribute: {full_url}')
                            return full_url
        return None

    def _find_script_images(self, soup, base_url):
        """JavaScript içerisindeki image URL'leri bul"""
        
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                script_content = script.string
                
                # Simple string search for image URLs
                if 'uploads/haberler' in script_content or 'tema/genel/uploads' in script_content:
                    # Find potential image URLs using simple patterns
                    lines = script_content.split()
                    for line in lines:
                        if ('uploads/haberler' in line or 'tema/genel/uploads' in line) and ('.jpg' in line or '.jpeg' in line or '.png' in line):
                            # Extract URL from quotes
                            for quote in ['"', "'"]:
                                if quote in line:
                                    parts = line.split(quote)
                                    for part in parts:
                                        if ('uploads/haberler' in part or 'tema/genel/uploads' in part) and ('.jpg' in part or '.jpeg' in part or '.png' in part):
                                            if self._is_valid_image_url(part) and 'yukleniyor' not in part:
                                                full_url = self._build_full_url(part)
                                                if full_url:
                                                    self.stdout.write(f'     📜 JavaScript: {full_url}')
                                                    return full_url
        return None

    def _find_css_background_images(self, soup):
        """CSS background-image özelliklerini kontrol et"""
        
        # Inline style kontrol et
        elements_with_style = soup.find_all(attrs={'style': True})
        
        for elem in elements_with_style:
            style = elem.get('style', '')
            if 'background' in style and 'url(' in style:
                # Simple extraction of URLs from CSS
                url_start = style.find('url(')
                if url_start != -1:
                    url_start += 4
                    url_end = style.find(')', url_start)
                    if url_end != -1:
                        url = style[url_start:url_end].strip('\'"')
                        if self._is_valid_image_url(url) and 'yukleniyor' not in url:
                            full_url = self._build_full_url(url)
                            if full_url:
                                self.stdout.write(f'     🎨 CSS background: {full_url}')
                                return full_url
        return None

    def _find_meta_images(self, soup):
        """Meta tag'lerde resim ara"""
        
        meta_selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]', 
            'meta[property="image"]',
            'meta[name="image"]'
        ]
        
        for selector in meta_selectors:
            meta = soup.select_one(selector)
            if meta:
                content = meta.get('content')
                if content and self._is_valid_image_url(content):
                    # Properly encode the URL before building full URL
                    try:
                        from urllib.parse import quote
                        # Encode the content URL properly
                        encoded_content = quote(content, safe=':/?#[]@!$&\'()*+,;=%')
                        full_url = self._build_full_url(encoded_content)
                        if full_url and 'yukleniyor' not in full_url:
                            self.stdout.write(f'     🏷️  Meta tag: {full_url}')
                            return full_url
                    except Exception as e:
                        # If encoding fails, try without encoding
                        full_url = self._build_full_url(content)
                        if full_url and 'yukleniyor' not in full_url:
                            self.stdout.write(f'     🏷️  Meta tag: {full_url}')
                            return full_url
        return None

    def _check_gallery_pages(self, haber):
        """İlgili galeri sayfalarını kontrol et"""
        
        # Haber ID'sini kullanarak galeri sayfası oluştur
        news_id = self._extract_news_id(haber.kaynak_url)
        if not news_id:
            return None
            
        gallery_urls = [
            f'https://karate.gov.tr/galeri/{news_id}',
            f'https://karate.gov.tr/fotogaleri/{news_id}',
            f'https://karate.gov.tr/resimler/{news_id}'
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for gallery_url in gallery_urls:
            try:
                response = requests.get(gallery_url, headers=headers, timeout=15, verify=False)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    images = soup.find_all('img')
                    
                    for img in images:
                        src = img.get('src')
                        if src and self._is_valid_image_url(src) and 'yukleniyor' not in src:
                            full_url = self._build_full_url(src)
                            if full_url:
                                return full_url
            except:
                continue
                
        return None

    def _check_sitemap_and_feeds(self, haber):
        """Site haritası ve RSS feed'lerini kontrol et"""
        
        feed_urls = [
            'https://karate.gov.tr/rss',
            'https://karate.gov.tr/feed',
            'https://karate.gov.tr/sitemap.xml'
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Haber başlığındaki anahtar kelimeleri al
        title_words = set(word.lower() for word in haber.baslik.split() if len(word) > 3)
        
        for feed_url in feed_urls:
            try:
                response = requests.get(feed_url, headers=headers, timeout=10, verify=False)
                if response.status_code == 200:
                    # RSS/XML'de image tag'leri ara
                    if 'xml' in response.headers.get('content-type', '').lower():
                        image_urls = re.findall(r'<(?:image|media:content)[^>]*url=["\\'']([^"\\'']*)["\\'']', response.text, re.IGNORECASE)
                        for url in image_urls:
                            if self._is_valid_image_url(url):
                                full_url = self._build_full_url(url)
                                if full_url and any(word in url.lower() for word in title_words):
                                    return full_url
            except:
                continue
                
        return None

    def _is_valid_image_url(self, url):
        """URL'nin geçerli bir resim URL'si olup olmadığını kontrol et"""
        if not url or len(url.strip()) < 5:
            return False
        
        url_lower = url.lower()
        
        # Geçerli resim uzantıları
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if not any(ext in url_lower for ext in valid_extensions):
            return False
        
        # Loading ve placeholder resimler
        skip_patterns = ['yukleniyor', 'loading', 'placeholder', 'default', 'logo', 'icon']
        if any(pattern in url_lower for pattern in skip_patterns):
            return False
            
        return True

    def _build_full_url(self, url):
        """Tam URL oluştur - properly encode Turkish characters"""
        if not url:
            return None
            
        if url.startswith('http'):
            # For absolute URLs, use requests' built-in encoding which handles Turkish characters better
            return url
        elif url.startswith('//'):
            return f'https:{url}'
        elif url.startswith('/'):
            return f'https://karate.gov.tr{url}'
        elif url.startswith('tema/'):
            return f'https://karate.gov.tr/{url}'
        else:
            return f'https://karate.gov.tr/{url}'

    def _download_and_process_image(self, image_url, haber):
        """Resmi indir ve işle"""
        
        try:
            # Debug the URL
            self.stdout.write(f'   📥 İndiriliyor: {image_url}')
            self.stdout.write(f'   🔍 URL uzunluğu: {len(image_url)}')
            
            # Handle Turkish characters in URLs with a more robust approach
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': haber.kaynak_url,
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
            }
            
            # Import requests
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Create a custom session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            session.headers.update(headers)
            
            # Try to download the image with multiple fallback approaches
            img_response = None
            exceptions = []
            
            # Approach 1: Try with requests directly but handle the encoding issue at the session level
            try:
                self.stdout.write(f'   🔧 Requests ile doğrudan deneme (session-level)')
                
                # Set the session to handle encoding properly
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': haber.kaynak_url,
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br'
                })
                
                # Use requests with proper URL handling
                img_response = session.get(
                    image_url,
                    timeout=30,
                    verify=False,
                    stream=True
                )
                img_response.raise_for_status()
            except Exception as e1:
                exceptions.append(f"Direct requests (session): {e1}")
                
                # Approach 2: Try with urllib.request but handle encoding at the request level
                try:
                    self.stdout.write(f'   🔧 urllib.request ile doğrudan deneme (request-level)')
                    
                    import urllib.request
                    import urllib.error
                    
                    # Create a custom request with proper encoding handling
                    # Use a Request object with proper headers
                    req = urllib.request.Request(image_url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    req.add_header('Referer', haber.kaynak_url)
                    req.add_header('Accept', 'image/webp,image/apng,image/*,*/*;q=0.8')
                    
                    # Download the image
                    with urllib.request.urlopen(req, timeout=30) as response:
                        content = response.read()
                    
                    # Create mock response
                    class MockResponse:
                        def __init__(self, content):
                            self.content = content
                            self.headers = dict(response.headers)
                            self.status_code = response.getcode()
                        
                        def raise_for_status(self):
                            if self.status_code >= 400:
                                raise Exception(f"HTTP Error {self.status_code}")
            
                    img_response = MockResponse(content)
                except Exception as e2:
                    exceptions.append(f"urllib.request (request-level): {e2}")
                    
                    # Approach 3: Try with a completely different approach - use a proxy-like method
                    try:
                        self.stdout.write(f'   🔧 Proxy-like approach denemesi')
                        
                        import urllib.request
                        import urllib.error
                        
                        # Try to manually construct the HTTP request to bypass encoding issues
                        # Parse the URL
                        from urllib.parse import urlparse
                        parsed = urlparse(image_url)
                        
                        # Create HTTP connection manually
                        import http.client
                        
                        # Connect to the server
                        if parsed.scheme == 'https':
                            conn = http.client.HTTPSConnection(parsed.netloc, timeout=30)
                        else:
                            conn = http.client.HTTPConnection(parsed.netloc, timeout=30)
                        
                        try:
                            # Create the request path (this is where we need to be careful with encoding)
                            # For now, let's try with the original path and see if it works
                            request_path = parsed.path
                            if parsed.query:
                                request_path += '?' + parsed.query
                            
                            # Send the request
                            conn.request('GET', request_path, headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'Referer': haber.kaynak_url,
                                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
                            })
                            
                            # Get the response
                            response = conn.getresponse()
                            
                            # Read the content
                            content = response.read()
                            
                            # Create mock response
                            class MockResponse:
                                def __init__(self, content, headers, status_code):
                                    self.content = content
                                    self.headers = dict(headers)
                                    self.status_code = status_code
                                
                                def raise_for_status(self):
                                    if self.status_code >= 400:
                                        raise Exception(f"HTTP Error {self.status_code}")
                        
                            img_response = MockResponse(content, response.headers, response.status)
                        finally:
                            conn.close()
                    except Exception as e3:
                        exceptions.append(f"Proxy-like approach: {e3}")
                        
                        # Approach 4: Try with requests but with a different encoding approach
                        try:
                            self.stdout.write(f'   🔧 Requests ile farklı encoding denemesi')
                            
                            # Try to encode the URL properly before sending
                            import urllib.parse
                            
                            # Parse the URL
                            parsed = urllib.parse.urlparse(image_url)
                            
                            # Manually encode the path component
                            # We'll try to encode each part separately
                            path_parts = parsed.path.split('/')
                            encoded_parts = []
                            for part in path_parts:
                                if part:  # Skip empty parts
                                    # Try to encode with UTF-8 first
                                    try:
                                        encoded_part = urllib.parse.quote(part, safe='')
                                    except:
                                        # If that fails, try with latin-1
                                        try:
                                            encoded_part = urllib.parse.quote(part.encode('latin-1').decode('latin-1'), safe='')
                                        except:
                                            # If all else fails, use the original part
                                            encoded_part = part
                                    encoded_parts.append(encoded_part)
                                else:
                                    encoded_parts.append(part)
                            
                            # Reconstruct the path
                            encoded_path = '/'.join(encoded_parts)
                            
                            # Reconstruct the URL
                            safe_url = urllib.parse.urlunparse((
                                parsed.scheme,
                                parsed.netloc,
                                encoded_path,
                                parsed.params,
                                parsed.query,
                                parsed.fragment
                            ))
                            
                            self.stdout.write(f'   🔧 Manuel olarak kodlanmış URL: {safe_url}')
                            
                            # Try with requests
                            img_response = session.get(
                                safe_url,
                                timeout=30,
                                verify=False,
                                stream=True
                            )
                            img_response.raise_for_status()
                        except Exception as e4:
                            exceptions.append(f"Requests with manual encoding: {e4}")
                            
                            # Approach 5: Try with a completely different method - use curl via subprocess
                            try:
                                self.stdout.write(f'   🔧 Curl ile deneme')
                                
                                import subprocess
                                import tempfile
                                import os
                                
                                # Create a temporary file to save the image
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                                    temp_filename = tmp_file.name
                                
                                try:
                                    # Use curl to download the image
                                    curl_command = [
                                        'curl',
                                        '-L',  # Follow redirects
                                        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                        '-H', f'Referer: {haber.kaynak_url}',
                                        '-H', 'Accept: image/webp,image/apng,image/*,*/*;q=0.8',
                                        '--output', temp_filename,
                                        '--insecure',  # Skip SSL verification like in requests
                                        image_url
                                    ]
                                    
                                    # Run curl
                                    result = subprocess.run(curl_command, capture_output=True, text=True, timeout=60)
                                    
                                    if result.returncode == 0:
                                        # Read the content from the temporary file
                                        with open(temp_filename, 'rb') as f:
                                            content = f.read()
                                        
                                        # Create mock response
                                        class MockResponse:
                                            def __init__(self, content):
                                                self.content = content
                                                self.headers = {}
                                                self.status_code = 200
                                            
                                            def raise_for_status(self):
                                                pass  # Already successful
                                    
                                        img_response = MockResponse(content)
                                    else:
                                        raise Exception(f"Curl failed with return code {result.returncode}: {result.stderr}")
                                finally:
                                    # Clean up temporary file
                                    if os.path.exists(temp_filename):
                                        os.unlink(temp_filename)
                            except Exception as e5:
                                exceptions.append(f"Curl approach: {e5}")
                                
                                # Approach 6: Try with requests but using a prepared request with manual URL handling
                                try:
                                    self.stdout.write(f'   🔧 Prepared request ile deneme')
                                    
                                    # Use requests with a prepared request to have more control
                                    from requests import Request
                                    
                                    # Create request
                                    req = Request('GET', image_url, headers=headers)
                                    prepared = session.prepare_request(req)
                                    
                                    # Manually fix the URL encoding issue in the prepared request
                                    # This is a hack to bypass the latin-1 encoding issue
                                    # We'll try to encode the URL properly before it gets to the encoding step
                                    import urllib.parse
                                    parsed = urllib.parse.urlparse(image_url)
                                    
                                    # Try to encode the path properly
                                    try:
                                        encoded_path = urllib.parse.quote(parsed.path, safe='/')
                                    except:
                                        # If that fails, try a different approach
                                        encoded_path = parsed.path
                                    
                                    # Reconstruct the URL with properly encoded path
                                    safe_url = urllib.parse.urlunparse((
                                        parsed.scheme,
                                        parsed.netloc,
                                        encoded_path,
                                        parsed.params,
                                        parsed.query,
                                        parsed.fragment
                                    ))
                                    
                                    # Update the prepared request URL
                                    prepared.url = safe_url
                                    
                                    img_response = session.send(prepared, timeout=30, verify=False, stream=True)
                                    img_response.raise_for_status()
                                except Exception as e6:
                                    exceptions.append(f"Prepared request: {e6}")
            
            # If none of the approaches worked, raise the last exception
            if img_response is None:
                self.stdout.write(f'   ❌ Tüm yaklaşımlar başarısız:')
                for i, exc in enumerate(exceptions, 1):
                    self.stdout.write(f'      {i}. {exc}')
                # For the specific case where Turkish characters are causing issues,
                # let's try one more approach - skip this image and continue
                self.stdout.write(f'   ⚠️  Turkish character URL hatası, resim atlanıyor')
                return None
            
            # Content-Length kontrolü
            content_length = getattr(img_response, 'headers', {}).get('content-length') if hasattr(img_response, 'headers') else None
            if content_length and int(content_length) < 1024:  # 1KB'dan küçük
                self.stdout.write('   ⚠️  Resim çok küçük (Content-Length)')
                return None
            
            # İçeriği oku
            content = img_response.content if hasattr(img_response, 'content') else getattr(img_response, 'data', b'')
            if len(content) < 1024:  # 1KB'dan küçük
                self.stdout.write(f'   ⚠️  İndirilen içerik çok küçük ({len(content)} bytes)')
                return None
            
            self.stdout.write(f'   ✅ İndirildi ({len(content)} bytes)')
            
            # PIL ile işle
            try:
                image = Image.open(io.BytesIO(content))
                self.stdout.write(f'   📏 Boyut: {image.width}x{image.height} - Format: {image.format}')
                
                # Minimum boyut kontrolü
                if image.width < 150 or image.height < 100:
                    self.stdout.write(f'   ⚠️  Resim boyutu çok küçük')
                    return None
                
            except Exception as pil_error:
                self.stdout.write(f'   ❌ PIL hatası: {pil_error}')
                return None
            
            # RGB'ye çevir
            if image.mode in ('RGBA', 'P', 'L'):
                rgb_image = image.convert('RGB')
            else:
                rgb_image = image
            
            # Boyut optimizasyonu (orijinal kaliteyi koru)
            max_width = 1200
            if rgb_image.width > max_width:
                ratio = max_width / rgb_image.width
                new_height = int(rgb_image.height * ratio)
                rgb_image = rgb_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                self.stdout.write(f'   🔧 Yeniden boyutlandırıldı: {rgb_image.width}x{rgb_image.height}')
            
            # Yüksek kalitede kaydet
            output = io.BytesIO()
            rgb_image.save(output, format='JPEG', quality=92, optimize=True)
            output.seek(0)
            
            # ASCII uyumlu dosya adı oluştur - use only ASCII characters
            safe_title = self._create_ascii_filename(haber.baslik)
            unique_id = str(uuid.uuid4())[:8]
            filename = f"karate_dynamic_{safe_title}_{unique_id}.jpg"
            
            # Ensure filename is ASCII encoded
            try:
                # Try to encode the filename as ASCII
                filename_bytes = filename.encode('ascii')
                filename = filename_bytes.decode('ascii')
            except UnicodeError:
                # If there's still an issue, use a simple default name
                filename = f"karate_dynamic_photo_{unique_id}.jpg"
            
            self.stdout.write(f'   📝 Dosya adı: {filename}')
            return ContentFile(output.read(), name=filename)
            
        except Exception as e:
            self.stdout.write(f'   ❌ İndirme/işleme hatası: {e}')
            import traceback
            self.stdout.write(f'   🐛 Hata detayı: {traceback.format_exc()}')
            return None

    def _create_ascii_filename(self, title):
        """Create ASCII-compatible filename"""
        if not title:
            return 'haber'
        
        # Replace Turkish characters with ASCII equivalents first
        turkish_to_ascii = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ş': 's', 'ü': 'u', 'ö': 'o',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ş': 'S', 'Ü': 'U', 'Ö': 'O'
        }
        
        ascii_title = title
        for turkish, ascii_char in turkish_to_ascii.items():
            ascii_title = ascii_title.replace(turkish, ascii_char)
        
        # Use Django's slugify which handles ASCII conversion
        safe_title = slugify(ascii_title)[:30]
        
        # Final cleanup to ensure only ASCII characters
        if safe_title:
            # Remove any remaining non-ASCII characters
            safe_title = ''.join(c for c in safe_title if ord(c) < 128)
            safe_title = safe_title.strip('-')
        
        # If we lost everything, use a default
        if not safe_title:
            safe_title = 'karate-haber'
            
        return safe_title

    def _create_safe_filename(self, title):
        """Güvenli dosya adı oluştur - Türkçe karakter desteği"""
        if not title:
            return 'haber'
        
        # İlk önce Türkçe karakterleri değiştir
        turkish_chars = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ş': 's', 'ü': 'u', 'ö': 'o',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ş': 'S', 'Ü': 'U', 'Ö': 'O'
        }
        
        clean_title = title
        for turkish, latin in turkish_chars.items():
            clean_title = clean_title.replace(turkish, latin)
        
        # Django'nun slugify'ını kullan
        safe_title = slugify(clean_title)[:30]
        
        # Eğer slugify başarısız olursa manuel temizlik
        if not safe_title or safe_title.isspace():
            # Remove non-alphanumeric except spaces and hyphens
            clean_title = re.sub(r'[^\w\s-]', '', clean_title.lower())
            # Replace spaces with hyphens
            clean_title = re.sub(r'[\s_]+', '-', clean_title)
            # Remove multiple hyphens
            clean_title = re.sub(r'-+', '-', clean_title)
            
            safe_title = clean_title[:30].strip('-')
        
        # Son güvenlik kontrolü
        if not safe_title:
            safe_title = 'karate-haber'
        
        return safe_title