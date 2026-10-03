from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite, Haber, Kategori
from haberler.services.news_scraper import NewsScrapingService
import requests
from bs4 import BeautifulSoup
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
from urllib.parse import urljoin
import time
import re
import logging
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(category=InsecureRequestWarning)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Türkiye Boks Federasyonu\'ndan sadece Son Haberler ve Güncel Duyurular bölümlerinden haberleri çeker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Çekilecek haber sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece göster, gerçekten kaydetme'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write('🥊 TÜRKİYE BOKS FEDERASYONU HABERLERİ ÇEKME SİSTEMİ')
        self.stdout.write('=' * 60)
        
        try:
            # Türkiye Boks Federasyonu'nu bul
            federation = FederasyonWebsite.objects.get(ad='Türkiye Boks Federasyonu')
            self.stdout.write(f'Federasyon: {federation.ad}')
            self.stdout.write(f'URL: {federation.haberler_url}')
        except FederasyonWebsite.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Türkiye Boks Federasyonu veritabanında bulunamadı')
            )
            return
        
        # Kategoriyi bul
        try:
            kategori = Kategori.objects.get(federasyon_website=federation)
        except Kategori.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('⚠️  Kategori bulunamadı')
            )
            return
        
        # Bot kullanıcı oluştur/al
        bot_user, created = User.objects.get_or_create(
            username='boks_importer',
            defaults={
                'email': 'boks_importer@federations.gov.tr',
                'first_name': 'Boks',
                'last_name': 'Importer',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('🤖 Yeni bot kullanıcı oluşturuldu')
            )
        
        # Haberleri çek
        news_items = self._scrape_specific_sections(federation, limit)
        
        if not news_items:
            self.stdout.write(
                self.style.WARNING('⚠️  Haber bulunamadı')
            )
            return
        
        self.stdout.write(f'📊 {len(news_items)} haber bulundu')
        
        # Haberleri işle
        imported_count = 0
        for news_data in news_items:
            try:
                # Mevcut haberi kontrol et
                if Haber.objects.filter(kaynak_url=news_data['url']).exists():
                    self.stdout.write(f'⏭️  Atlandı (mevcut): {news_data["title"][:50]}...')
                    continue
                
                if dry_run:
                    self.stdout.write(f'📝 Bulundu: {news_data["title"][:50]}...')
                    imported_count += 1
                    continue
                
                # Benzersiz slug oluştur
                base_slug = slugify(news_data['title'])
                slug = base_slug
                counter = 1
                while Haber.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Haberi oluştur
                haber = Haber.objects.create(
                    baslik=news_data['title'][:200],
                    slug=slug,
                    ozet=news_data['summary'][:500] if news_data['summary'] else news_data['title'][:500],
                    icerik=news_data['content'][:15000] if news_data['content'] else news_data['summary'],
                    kategori=kategori,
                    yazar=bot_user,
                    kaynak_url=news_data['url'],
                    federasyon_website=federation,
                    otomatik_eklendi=True,
                    yayinlandi=True,
                    olusturma_tarihi=news_data.get('date') or timezone.now()
                )
                
                # Resmi ekle
                if news_data.get('image_url'):
                    self._add_image_to_news(haber, news_data['image_url'])
                
                imported_count += 1
                self.stdout.write(f'✅ Eklendi: {news_data["title"][:50]}...')
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Haber import hatası: {e}')
                )
                logger.error(f"News import error: {e}")
                continue
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n🔍 DRY RUN TAMAMLANDI! '
                    f'{imported_count} haber bulundu.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 İŞLEM TAMAMLANDI! '
                    f'Toplam {imported_count} haber eklendi.'
                )
            )

    def _scrape_specific_sections(self, federation, limit):
        """Sadece Son Haberler ve Güncel Duyurular bölümlerinden haberleri çek"""
        news_items = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # SSL doğrulamasını devre dışı bırak
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(federation.haberler_url, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # "Son Haberler" ve "Güncel Duyurular" bölümlerini bul
            sections = soup.find_all(['h2', 'h3'], string=re.compile(r'(Son Haberler|Güncel Duyurular)', re.IGNORECASE))
            
            processed_urls = set()
            
            for section in sections:
                # Bölümün altındaki haberleri bul
                # Bölümün parent container'ını bul
                container = section.find_parent(['div', 'section', 'article'])
                if not container:
                    container = section.parent
                
                # Container içindeki tüm linkleri bul
                links = container.find_all('a', href=True) if container else []
                
                for link in links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    # Geçerli bir başlık ve URL kontrolü
                    if not title or len(title) < 5 or not href:
                        continue
                    
                    # Tam URL oluştur
                    full_url = urljoin(federation.ana_url, href)
                    
                    # Aynı URL'yi iki kez işlememek için
                    if full_url in processed_urls:
                        continue
                    processed_urls.add(full_url)
                    
                    # Tarih bilgisi al
                    news_date = None
                    date_element = link.find_next(string=re.compile(r'\d{1,2}[./]\d{1,2}[./]\d{4}'))
                    if date_element:
                        date_text = date_element.strip()
                        news_date = self._parse_turkish_date(date_text)
                    
                    # Özet metin al
                    summary = ""
                    parent = link.parent
                    if parent:
                        # Aynı parent içindeki diğer metinleri özet olarak kullan
                        siblings = parent.find_next_siblings()
                        for sibling in siblings[:2]:  # İlk 2 kardeş element
                            text = sibling.get_text(strip=True)
                            if text and len(text) > 20:
                                summary = text[:500]
                                break
                    
                    # Tam içeriği al
                    full_content = self._get_full_news_content(full_url)
                    
                    # Ana resmi al
                    image_url = self._get_main_news_image(full_url)
                    
                    news_items.append({
                        'title': title[:200],
                        'url': full_url,
                        'summary': summary[:500] if summary else title[:500],
                        'content': full_content,
                        'date': news_date,
                        'image_url': image_url
                    })
                    
                    if len(news_items) >= limit:
                        break
                
                if len(news_items) >= limit:
                    break
        
        except Exception as e:
            self.stdout.write(f'❌ Scraping hatası: {e}')
            logger.error(f"Scraping error: {e}")
        
        return news_items

    def _get_full_news_content(self, url):
        """Haber sayfasından tam içeriği al"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # SSL doğrulamasını devre dışı bırak
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Script ve style elementlerini kaldır
            for script in soup(["script", "style"]):
                script.decompose()
            
            # İçerik selektörleri
            content_selectors = [
                '.content', '.haber-icerik', '.news-content',
                '.post-content', '.entry-content', '.article-content',
                'article', 'main', '#content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # Navigasyon ve sidebar elementlerini kaldır
                    unwanted_selectors = [
                        'nav', 'header', 'footer', 'aside', '.navigation', '.menu', '.sidebar',
                        '.header', '.footer', '#menu', '#navigation', '#sidebar', '#header', '#footer',
                        '.social-media', '.breadcrumb', '.pagination', '.comments', '.advertisement',
                        '.ads', '.widget', '.share-buttons', '.tags', '.category', '.author-box',
                        '.post-meta', '.entry-meta', '.logo', '.branding', '.site-header',
                        '.site-footer', '.main-navigation'
                    ]
                    
                    for unwanted in unwanted_selectors:
                        for elem in content_element.select(unwanted):
                            elem.decompose()
                    
                    content = content_element.get_text(separator='\n', strip=True)
                    break
            
            # İçerik bulunamazsa body'den al
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator='\n', strip=True)
            
            # Improved cleaning - more precise approach to remove navigation/footer content
            lines = content.split('\n')
            cleaned_lines = []
            
            # Identify the start of actual content by looking for date patterns
            start_index = 0
            date_pattern = re.compile(r'\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}\s+\d{1,2}:\d{2}')
            
            for i, line in enumerate(lines):
                if date_pattern.search(line):
                    start_index = i
                    break
            
            # Identify the end of actual content by looking for common footer patterns
            end_index = len(lines)
            footer_patterns = [
                r'DİĞER HABERLER',
                r'GENEL HABERLER', 
                r'GÜNCEL DUYURULAR',
                r'ETKİNLİKLER',
                r'FOTO GALERİ',
                r'VİDEO GALERİ',
                r'KURUMSAL',
                r'BİLGİ BANKASI',
                r'BAĞLANTILAR',
                r'BANKA HESAP',
                r'Copyright',
                r'Tüm hakları saklıdır'
            ]
            
            for i in range(start_index, len(lines)):
                line = lines[i]
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in footer_patterns):
                    end_index = i
                    break
            
            # Extract the actual content between start and end indices
            actual_content_lines = lines[start_index:end_index]
            
            # Clean the actual content
            for line in actual_content_lines:
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Skip lines that are clearly navigation/menu items
                nav_patterns = [
                    'ANASAYFA', 'KURUMSAL', 'HABERLER', 'İLETİŞİM',
                    'T.C. Gençlik ve Spor Bakanımız', 'Onursal Başkanımız',
                    'Federasyon Başkanımız', 'Genel Sekreterimiz',
                    'Başkan Danışmanımız', 'Kurullarımız',
                    'KULÜP BİLGİ SİSTEMİ', 'FAALİYET TAKVİMİ',
                    'KARATE TÜRK TV', 'Y.T.K.F.Web Sitesi',
                    'SOSYAL MEDYA', 'Etkinlikler', 'Duyurular',
                    'Faaliyet Programı', 'Resmi Evraklar',
                    'Federasyon Talimatları', 'Fotoğraf Galerisi',
                    'Video Galeri', 'İletişim Formu', 'TKF MENÜ',
                    'Karate-Do Nedir?', 'Tarihçe', 'Vizyonumuz', 'Misyonumuz',
                    'Stratejik Plan', 'Arama Yap',
                    # Specific unwanted text patterns
                    'Suudi Antrenörler Derneği Başkanı’ndan Dostluk Plaketi',
                    'Gençlik ve Spor Bakanımız Sayın Osman Aşkın Bak, Diyarbakır’da Bizleri Yalnız Bırakmadı',
                    # Turkish Boxing Federation specific patterns
                    'Telefon:', 'E-Posta Adresi:', 'Toggle navigation',
                    'Bakanlık', 'Federasyonumuz', 'Başkanımız', 'Yönetim Kurulu',
                    'Ana Statü', 'Talimatlar', 'İhaleler', 'Yönetmelikler',
                    'İdari Personel', 'Türk Boks Tarihi', 'Dünya Boks Tarihi',
                    'İletişim', 'Faaliyet Takvimi', 'Hakemler', 'Kurullar',
                    'MERKEZ HAKEM KOMİTESİ', 'PLANLAMA VE KOORDİNASYON KURULU',
                    'BİLİM KURULU', 'HUKUK KURULU', 'SAĞLIK KURULU',
                    'ORGANİZASYON VE DIŞ İLİŞKİLER KURULU', 'ONUR KURULU',
                    'ETİK KURULU', 'BASIN KURULU', 'TEKNİK KURULU',
                    'EĞİTİM KURULU', 'DENETLEME KURULU', 'DİSİPLİN KURULU'
                ]
                
                line_upper = line.upper()
                is_nav_line = any(pattern.upper() in line_upper for pattern in nav_patterns)
                
                # Additional check: very short lines with common navigation words
                if not is_nav_line and len(line.strip()) < 15:
                    short_nav_words = ['ANASAYFA', 'HABERLER', 'İLETİŞİM', 'GALERİ']
                    is_nav_line = any(word in line_upper for word in short_nav_words)
                
                if not is_nav_line:
                    cleaned_lines.append(line)
            
            content = '\n'.join(cleaned_lines)
            
            # Apply end-text cleaning patterns
            unwanted_end_patterns = [
                r'\s*DIĞER HABERLER.*$',
                r'\s*GENEL HABERLER.*$',
                r'\s*GÜNCEL DUYURULAR.*$',
                r'\s*ETKİNLİKLER.*$',
                r'\s*FOTO GALERİ.*$',
                r'\s*VİDEO GALERİ.*$',
                r'\s*Devamı Oku.*$',
                r'\s*HABER GÖRSELLERİ.*$',
                r'\s*Daha Fazla Göster.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*Başkanımız.*Bir Araya Geldi\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*EĞİTİM SINAV BAŞVURULARI BAŞLIYOR\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*Turnuvası Açılış Töreni Gerçekleştirildi\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*Dostluk Plaketi\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*Zirvede\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*ŞAMPİYONASI TAMAMLANDI\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*ANTRENÖR KURSU\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*Etabı.*Tamamlandı\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*Bizleri Yalnız Bırakmadı\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]*Etabı.*Coşkuyla Başladı\s*\d{1,2}\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s*\d{4}.*$',
                r'\s*\d{1,2}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s+\d{4}\s+\d{1,2}:\d{2}\s*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]{10,}?\s+\d{1,2}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s+\d{4}\s+\d{1,2}:\d{2}\s*$',
                r'\s*(?:[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]{10,}?\s+\d{1,2}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s+\d{4}\s+\d{1,2}:\d{2}\s*){3,}\s*$'
            ]
            
            # Apply each pattern to clean the content
            for pattern in unwanted_end_patterns:
                content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Additional cleaning for Turkish Boxing Federation specific patterns
            # Remove phone numbers and email addresses at the beginning
            content = re.sub(r'^Telefon:\s*\n?\d.*?\n', '', content, flags=re.MULTILINE)
            content = re.sub(r'^E-Posta Adresi:\s*\n?.*?@.*?\n', '', content, flags=re.MULTILINE)
            
            # Remove navigation text at the end
            # Look for the pattern that indicates the end of actual content
            end_patterns = [
                r'\n\s*Paylaş:.*$',
                r'\n\s*Arat.*$',
                r'\n\s*Güncel Duyurular.*$',
                r'\n\s*Son Haberler.*$',
                r'\n\s*Telefon:.*$',
                r'\n\s*E-Posta:.*$',
                r'\n\s*Adres:.*$',
                r'\n\s*Faks:.*$',
                r'\n\s*Flaticon-.*$',
                r'\n\s*Kurumsal.*$',
                r'\n\s*Vizyonumuz ve Misyonumuz.*$',
                r'\n\s*Federasyon.*$',
                r'\n\s*Hakkımızda.*$',
                r'\n\s*Fotoğraf Galerisi.*$',
                r'\n\s*Hızlı Linkler.*$',
                r'\n\s*Ana Sayfa.*$',
                r'\n\s*Türk Boks Federasyonu ©.*$'
            ]
            
            # Apply each pattern to clean the end of content
            for pattern in end_patterns:
                content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove extra whitespace but be less aggressive
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Limit to double newlines
            content = re.sub(r'[ \t]+', ' ', content)  # Remove extra spaces/tabs
            
            return content
        
        except Exception as e:
            logger.error(f"Full content error: {e}")
            return ""

    def _get_main_news_image(self, url):
        """Haber sayfasından ana resmi al"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # SSL doğrulamasını devre dışı bırak
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ana resim selektörleri
            image_selectors = [
                'img.haber-detay-image', '.haber-detay-image',
                '.news-detail img', '.haber img', 'article img',
                '.content img', 'main img', '.post img'
            ]
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src and self._is_valid_news_image(src):
                        return self._build_image_url(src, url)
            
            # Meta tag'den resim
            meta_image = soup.find('meta', property='og:image')
            if meta_image and meta_image.get('content'):
                return urljoin(url, meta_image['content'])
            
            return None
        
        except Exception as e:
            logger.error(f"Image error: {e}")
            return None

    def _is_valid_news_image(self, src):
        """Resmin geçerli haber resmi olup olmadığını kontrol et"""
        src_lower = src.lower()
        
        # Atlanacak resimler
        skip_patterns = [
            'logo', 'icon', 'favicon', 'banner', 'header',
            'footer', 'social', 'share', 'avatar', 'profile',
            'advertisement', 'ads', 'sponsor', 'arkaplan',
            'yukleniyor', 'loading', 'placeholder', 'default'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False
        
        # Geçerli formatlar
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        return any(ext in src_lower for ext in valid_extensions)

    def _build_image_url(self, src, base_url):
        """Resim URL'sini oluştur"""
        if src.startswith('http'):
            return src
        else:
            return urljoin(base_url, src)

    def _add_image_to_news(self, haber, image_url):
        """Habere resim ekle"""
        try:
            from haberler.services.news_scraper import NewsScrapingService
            scraper = NewsScrapingService()
            # SSL doğrulamasını devre dışı bırak
            scraper.session.verify = False
            image_file = scraper.download_and_process_image(image_url, haber.baslik)
            
            if image_file:
                haber.resim.save(image_file.name, image_file, save=True)
                self.stdout.write(f'     🖼️  Resim eklendi')
                return True
        
        except Exception as e:
            self.stdout.write(f'     ⚠️  Resim eklenemedi: {e}')
            logger.error(f"Image add error: {e}")
        
        return False

    def _parse_turkish_date(self, date_text):
        """Türkçe tarih metnini parse et"""
        try:
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
            
            from datetime import datetime
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    if pattern == patterns[0]:  # Türkçe ay adı
                        day, month_name, year = match.groups()
                        month = turkish_months.get(month_name)
                        if month:
                            return datetime(int(year), month, int(day))
                    else:
                        if pattern == patterns[3]:  # YYYY-MM-DD
                            year, month, day = match.groups()
                        else:  # DD.MM.YYYY or DD/MM/YYYY
                            day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
            
            return None
        
        except Exception:
            return None