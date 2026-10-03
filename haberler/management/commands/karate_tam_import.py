from django.core.management.base import BaseCommand
from django.db import transaction
from haberler.models import Haber, Kategori, FederasyonWebsite
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from django.core.files.base import ContentFile
import io
from PIL import Image
import uuid
import time
import re

class Command(BaseCommand):
    help = 'Karate federasyonunun 5 bölümünden tüm haberleri ve orijinal fotoğrafları çek'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit-per-section',
            type=int,
            default=20,
            help='Her bölümden çekilecek haber sayısı (varsayılan: 20)'
        )
        parser.add_argument(
            '--clean-start',
            action='store_true',
            help='Mevcut karate haberlerini sil ve baştan başla'
        )

    def handle(self, *args, **options):
        limit_per_section = options['limit_per_section']
        clean_start = options['clean_start']
        
        self.stdout.write('🥋 KARATE FEDERASYONU TAM İMPORT SİSTEMİ')
        self.stdout.write('=' * 60)
        
        # Karate federation sections
        karate_sections = [
            {
                'name': 'Federasyon',
                'url': 'https://karate.gov.tr/haber-kategori/federasyon',
                'slug': 'karate-federasyon'
            },
            {
                'name': 'Kyokushin', 
                'url': 'https://karate.gov.tr/haber-kategori/kyokushin',
                'slug': 'karate-kyokushin'
            },
            {
                'name': 'Etkinlikler',
                'url': 'https://karate.gov.tr/haber-kategori/etkinlikler', 
                'slug': 'karate-etkinlikler'
            },
            {
                'name': 'Kurs & Seminer',
                'url': 'https://karate.gov.tr/haber-kategori/kurs-seminer',
                'slug': 'karate-kurs-seminer'
            },
            {
                'name': 'Ziyaretler',
                'url': 'https://karate.gov.tr/haber-kategori/ziyaretler',
                'slug': 'karate-ziyaretler'
            }
        ]
        
        if clean_start:
            self._clean_existing_karate_news()
        
        # Setup
        federation, main_kategori = self._setup_federation()
        bot_user = self._get_bot_user()
        
        total_imported = 0
        
        # Process each section
        for section in karate_sections:
            self.stdout.write(f'\\n🔄 {section["name"]} bölümü işleniyor...')
            self.stdout.write(f'📡 URL: {section["url"]}')
            
            # Create/get category for this section
            kategori = self._get_or_create_category(section, federation)
            
            # Import news from this section
            imported_count = self._import_section_news(
                section, kategori, bot_user, limit_per_section
            )
            
            total_imported += imported_count
            self.stdout.write(f'✅ {imported_count} haber içe aktarıldı')
            
            # Rate limiting
            time.sleep(2)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\\n🎉 İşlem tamamlandı! Toplam {total_imported} haber 5 bölümden içe aktarıldı'
            )
        )

    def _clean_existing_karate_news(self):
        """Mevcut karate haberlerini temizle"""
        self.stdout.write('🗑️  Mevcut karate haberleri temizleniyor...')
        
        # Find all karate-related news
        karate_categories = Kategori.objects.filter(ad__icontains='Karate')
        karate_news_by_category = []
        
        for cat in karate_categories:
            news = list(Haber.objects.filter(kategori=cat))
            karate_news_by_category.extend(news)
        
        karate_news_by_title = list(Haber.objects.filter(baslik__icontains='karate'))
        karate_news_by_source = list(Haber.objects.filter(kaynak_url__icontains='karate.gov.tr'))
        
        all_karate_news = list(set(karate_news_by_category + karate_news_by_title + karate_news_by_source))
        
        self.stdout.write(f'📊 {len(all_karate_news)} mevcut karate haberi siliniyor...')
        
        for news in all_karate_news:
            if news.resim:
                news.resim.delete(save=False)
            news.delete()
        
        self.stdout.write(f'✅ {len(all_karate_news)} karate haberi silindi')

    def _setup_federation(self):
        """Federation ve ana kategori kurulumu"""
        # Federation setup
        federation, created = FederasyonWebsite.objects.get_or_create(
            ana_url='https://karate.gov.tr',
            defaults={
                'ad': 'Türkiye Karate Federasyonu (Resmi)',
                'haberler_url': 'https://karate.gov.tr/haber-kategori/federasyon',
                'haber_listesi_selector': '.row .col-md-4',
                'haber_baslik_selector': 'h3, h4',
                'haber_link_selector': 'a',
                'aktif': True
            }
        )
        
        # Ana karate kategorisi
        main_kategori, created = Kategori.objects.get_or_create(
            slug='karate',
            defaults={
                'ad': 'Karate',
                'aciklama': 'Karate haberleri ve duyuruları',
                'federasyon_website': federation
            }
        )
        
        return federation, main_kategori

    def _get_bot_user(self):
        """Bot kullanıcı al/oluştur"""
        bot_user, created = User.objects.get_or_create(
            username='karate_full_importer',
            defaults={
                'email': 'karate@fullimporter.gov.tr',
                'first_name': 'Karate',
                'last_name': 'Full Importer',
                'is_active': True
            }
        )
        return bot_user

    def _get_or_create_category(self, section, federation):
        """Bölüm için kategori al/oluştur"""
        # Ana karate kategorisini kullan (tüm haberler tek kategoride)
        kategori, created = Kategori.objects.get_or_create(
            slug='karate',
            defaults={
                'ad': 'Karate',
                'aciklama': 'Karate haberleri ve duyuruları',
                'federasyon_website': federation
            }
        )
        return kategori

    def _import_section_news(self, section, kategori, bot_user, limit):
        """Bölümden haberleri içe aktar"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(section['url'], headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news items
            news_elements = soup.select('.row .col-md-4, .haber-item, article')
            news_elements = news_elements[:limit] if limit > 0 else news_elements
            
            self.stdout.write(f'📰 {len(news_elements)} haber bulundu')
            
            imported_count = 0
            
            for i, element in enumerate(news_elements, 1):
                try:
                    # Extract news data
                    news_data = self._extract_news_data(element, section['url'])
                    
                    if not news_data:
                        continue
                    
                    self.stdout.write(f'  [{i}/{len(news_elements)}] 📄 {news_data["title"][:50]}...')
                    
                    # Check if news already exists
                    if Haber.objects.filter(kaynak_url=news_data['url']).exists():
                        self.stdout.write('    ⚠️  Zaten mevcut, atlanıyor')
                        continue
                    
                    # Create news article
                    haber = self._create_news_article(news_data, kategori, bot_user, section)
                    
                    if haber:
                        # Download original photo
                        photo_success = self._download_original_photo(haber, news_data['url'])
                        
                        if photo_success:
                            self.stdout.write('    📸 Orijinal fotoğraf indirildi')
                        else:
                            self.stdout.write('    📷 Fotoğraf bulunamadı')
                        
                        imported_count += 1
                        self.stdout.write('    ✅ İçe aktarıldı')
                    else:
                        self.stdout.write('    ❌ Oluşturulamadı')
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.stdout.write(f'    ❌ Hata: {e}')
                    continue
            
            return imported_count
            
        except Exception as e:
            self.stdout.write(f'❌ Bölüm import hatası: {e}')
            return 0

    def _extract_news_data(self, element, base_url):
        """HTML elementinden haber verilerini çıkar"""
        try:
            # Title
            title_elem = element.select_one('h3, h4, .title, .baslik, a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            if not title:
                return None
            
            # Link
            link_elem = element.select_one('a')
            if not link_elem:
                return None
            
            href = link_elem.get('href')
            if not href:
                return None
            
            # Build full URL
            if href.startswith('/haber/'):
                url = f'https://karate.gov.tr{href}'
            elif href.startswith('haber/'):
                url = f'https://karate.gov.tr/{href}'
            elif href.startswith('/'):
                url = f'https://karate.gov.tr{href}'
            elif href.startswith('http'):
                url = href
            else:
                url = urljoin(base_url, href)
            
            # Date
            date_elem = element.select_one('.date, .tarih, time, small')
            date_text = date_elem.get_text(strip=True) if date_elem else None
            
            # Summary
            summary_elem = element.select_one('.excerpt, .ozet, p, .summary')
            summary = summary_elem.get_text(strip=True) if summary_elem else ''
            
            return {
                'title': title,
                'url': url,
                'date': date_text,
                'summary': summary[:300] if summary else title[:100]  # Limit summary length
            }
            
        except Exception as e:
            return None

    def _create_news_article(self, news_data, kategori, bot_user, section):
        """Haber makalesini oluştur"""
        try:
            # Get detailed content from news page
            content = self._scrape_detailed_content(news_data['url'])
            
            # Create unique slug
            base_slug = slugify(news_data['title'])
            slug = base_slug
            counter = 1
            while Haber.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Create the news article
            haber = Haber.objects.create(
                baslik=news_data['title'],
                slug=slug,
                ozet=news_data['summary'],
                icerik=content,
                kategori=kategori,
                yazar=bot_user,
                kaynak_url=news_data['url'],
                yayinlandi=True,
                olusturma_tarihi=timezone.now(),
                guncelleme_tarihi=timezone.now()
            )
            
            return haber
            
        except Exception as e:
            self.stdout.write(f'    ❌ Makale oluşturma hatası: {e}')
            return None

    def _scrape_detailed_content(self, url):
        """Haber detay sayfasından içeriği çek"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # URL encoding fix for Turkish characters
            # url_encoded = requests.utils.quote(url.encode('utf-8'), safe=':/?#[]@!$&\'()*+,;=')
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Content selectors
            content_selectors = [
                '.news-detail-content',
                '.haber-detay-icerik', 
                '.content',
                '.article-body',
                '.post-content',
                'main .container',
                '.row .col-md-8',
                'article'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator='\\n', strip=True)
                    break
            
            # Clean content
            content = self._clean_content(content)
            
            return content if content and len(content) > 50 else "İçerik federasyon sitesinden alınmıştır."
            
        except Exception as e:
            return f"İçerik çekilemedi: {str(e)}"

    def _clean_content(self, content):
        """İçeriği temizle"""
        if not content:
            return ""
        
        # Navigation text patterns to remove
        navigation_patterns = [
            r'ANASAYFA.*?İLETİŞİM',
            r'TKF MENÜ.*?İletişim Formu', 
            r'SOSYAL MEDYA.*?Formu',
            r'Karate-Do Nedir\?.*?Vizyonumuz',
            r'KULÜP BİLGİ SİSTEMİ.*?İLETİŞİM',
            r'HaberlerEtkinlikler.*?Geri'
        ]
        
        for pattern in navigation_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove individual menu items
        menu_items = [
            'ANASAYFA', 'KURUMSAL', 'HABERLER', 'İLETİŞİM',
            'TKF MENÜ', 'SOSYAL MEDYA', 'İletişim Formu',
            'Karate-Do Nedir?', 'Tarihçe', 'Vizyonumuz'
        ]
        
        for item in menu_items:
            if content.startswith(item):
                content = content[len(item):].strip()
        
        # Clean whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        content = content.strip()
        
        return content

    def _download_original_photo(self, haber, source_url):
        """Orijinal fotoğrafı federasyon sitesinden indir (modifikasyon yapmadan)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://karate.gov.tr/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br'
            }
            
            response = requests.get(source_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Enhanced image selectors for karate federation
            image_selectors = [
                'img.haber-detay-image',
                '.news-detail img',
                '.haber-detay img', 
                '.content img',
                'article img',
                'main img',
                '.container img',
                'img[src*=\"upload\"]',
                'img[src*=\"haber\"]',
                'img[src*=\"resim\"]',
                'img[src*=\"foto\"]'
            ]
            
            # Find best image
            best_image_url = None
            best_score = 0
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    alt = img.get('alt', '').lower()
                    
                    if not src or not self._is_valid_federation_image(src, alt):
                        continue
                    
                    # Build full URL
                    if src.startswith('/'):
                        image_url = f'https://karate.gov.tr{src}'
                    elif src.startswith('//'):
                        image_url = f'https:{src}'
                    elif src.startswith('http'):
                        image_url = src
                    else:
                        image_url = urljoin(source_url, src)
                    
                    # Score image relevance
                    score = self._score_image_relevance(src, alt, haber.baslik)
                    
                    if score > best_score:
                        best_score = score
                        best_image_url = image_url
            
            if not best_image_url:
                return False
            
            # Download and save original image
            img_response = requests.get(best_image_url, headers=headers, timeout=30, verify=False)
            img_response.raise_for_status()
            
            # Process image (basic optimization only, no modifications)
            image = Image.open(io.BytesIO(img_response.content))
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'P', 'L'):
                image = image.convert('RGB')
            
            # Basic size optimization (keep original quality)
            max_width = 1200
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with high quality (no modifications)
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95, optimize=True)
            output.seek(0)
            
            # Generate filename
            safe_title = slugify(haber.baslik)[:30]
            unique_id = str(uuid.uuid4())[:8]
            filename = f"karate_federation_{safe_title}_{unique_id}.jpg"
            
            # Save to news article
            haber.resim.save(filename, ContentFile(output.read()), save=True)
            
            return True
            
        except Exception as e:
            return False

    def _is_valid_federation_image(self, src, alt):
        """Federasyon sitesinden geçerli resim mi kontrol et"""
        src_lower = src.lower()
        alt_lower = alt.lower()
        
        # Skip unwanted images
        skip_patterns = [
            'logo', 'icon', 'favicon', 'banner', 'default', 
            'placeholder', 'avatar', 'profile', 'advertisement'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower or pattern in alt_lower:
                return False
        
        # Must be valid image format
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if not any(ext in src_lower for ext in valid_extensions):
            return False
        
        # Skip very small images
        if any(size in src_lower for size in ['50x', '100x', 'thumb']):
            return False
        
        return True

    def _score_image_relevance(self, src, alt, title):
        """Resmin haber ile alakasını puanla"""
        score = 0
        src_lower = src.lower()
        alt_lower = alt.lower()
        title_lower = title.lower()
        
        # High priority for federation uploads
        if 'upload' in src_lower or 'haber' in src_lower:
            score += 50
        
        # High score for larger images
        if 'large' in src_lower or 'big' in src_lower:
            score += 30
        
        # Score based on relevance to title
        title_words = title_lower.split()
        for word in title_words:
            if len(word) > 3:  # Skip short words
                if word in src_lower:
                    score += 20
                if word in alt_lower:
                    score += 15
        
        # Boost for karate-specific terms
        karate_terms = ['karate', 'kata', 'kumite', 'şampiyon', 'sporcu', 'antrenör']
        for term in karate_terms:
            if term in alt_lower:
                score += 10
        
        # Prefer JPEG format
        if src_lower.endswith(('.jpg', '.jpeg')):
            score += 5
        
        return score