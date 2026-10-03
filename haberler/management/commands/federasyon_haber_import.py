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

class Command(BaseCommand):
    help = 'Federasyon sitelerinden haberleri aynen alıp siteye ekle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--federation-id',
            type=int,
            help='Belirli bir federasyon ID\'si (boş bırakılırsa tüm aktif federasyonlar)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Çekilecek maksimum haber sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Mevcut haberleri de güncelle'
        )
        parser.add_argument(
            '--allow-category-creation',
            action='store_true',
            help='YENİ KATEGORİ OLUŞTURMAYA İZİN VER (GÜVENLİK UYARISI!)'
        )

    def handle(self, *args, **options):
        federation_id = options.get('federation_id')
        limit = options['limit']
        force_update = options['force_update']
        self._allow_category_creation = options['allow_category_creation']
        
        if self._allow_category_creation:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  UYARI: Otomatik kategori oluşturma etkinleştirildi!\n'
                    '   Bu durum onaylanmamış kategoriler oluşturabilir.'
                )
            )
        
        self.stdout.write('🏛️  FEDERASYON HABERLERİ İMPORT SİSTEMİ')
        self.stdout.write('=' * 50)
        
        # Federasyonları belirle
        if federation_id:
            try:
                federations = [FederasyonWebsite.objects.get(id=federation_id, aktif=True)]
            except FederasyonWebsite.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ ID {federation_id} ile aktif federasyon bulunamadı')
                )
                return
        else:
            federations = FederasyonWebsite.objects.filter(aktif=True)
        
        if not federations:
            self.stdout.write(
                self.style.WARNING('⚠️  Aktif federasyon bulunamadı')
            )
            return
        
        # Bot kullanıcı oluştur/al
        bot_user, created = User.objects.get_or_create(
            username='federation_importer',
            defaults={
                'email': 'importer@federations.gov.tr',
                'first_name': 'Federation',
                'last_name': 'Importer',
                'is_active': True
            }
        )
        
        total_imported = 0
        
        for federation in federations:
            self.stdout.write(f'\n🔄 {federation.ad} işleniyor...')
            
            try:
                imported_count = self._import_federation_news(
                    federation, bot_user, limit, force_update
                )
                total_imported += imported_count
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {federation.ad}: {imported_count} haber eklendi')
                )
                
                # Son tarama zamanını güncelle
                federation.son_tarama = timezone.now()
                federation.save()
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {federation.ad} hatası: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Toplam {total_imported} haber başarıyla eklendi!')
        )

    def _import_federation_news(self, federation, bot_user, limit, force_update):
        """Belirli bir federasyondan haber import et"""
        imported_count = 0
        
        try:
            # Federasyon kategorisini bul (otomatik oluşturma engellendi)
            kategori_slug = slugify(federation.ad)
            try:
                kategori = Kategori.objects.get(slug=kategori_slug)
            except Kategori.DoesNotExist:
                # Fallback 1: Federasyona bağlı kategori
                kategori = Kategori.objects.filter(federasyon_website=federation).first()
                # Fallback 2: Jiu Jitsu benzeri adlarla eşleşme
                if not kategori:
                    kategori = Kategori.objects.filter(ad__iregex=r"jiu|jutsu|jujitsu|ju-jitsu").first()
                if not kategori:
                    # Kategori bulunamadı - otomatik oluşturma engellendi
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ HATA: \'{federation.ad}\' için kategori bulunamadı!\n'
                            f'   Slug: {kategori_slug}\n'
                            f'   Lütfen önce bu kategoriyi manuel olarak oluşturun veya\n'
                            f'   --allow-category-creation parametresini kullanın (önerilmez!)'
                        )
                    )
                    return 0
            
            # Eğer kategori oluşturma izni verilmişse (güvenlik riski!)
            if hasattr(self, '_allow_category_creation') and self._allow_category_creation:
                kategori, created = Kategori.objects.get_or_create(
                    slug=kategori_slug,
                    defaults={
                        'ad': federation.ad.replace('Federasyonu', '').replace('Türkiye', '').strip(),
                        'aciklama': f'{federation.ad} haberleri',
                        'federasyon_website': federation
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  YENİ KATEGORİ OLUŞTURULDU: {kategori.ad} (onaylanmamış!)'
                        )
                    )
            
            # Federasyon sitesinden haberleri çek
            news_items = self._scrape_federation_news(federation, limit)
            
            for news_data in news_items:
                try:
                    # Mevcut haberi kontrol et
                    existing_news = Haber.objects.filter(
                        kaynak_url=news_data['url']
                    ).first()
                    
                    if existing_news and not force_update:
                        self.stdout.write(f'   ⏭️  Atlandı (mevcut): {news_data["title"][:40]}...')
                        continue
                    
                    # Haberi oluştur veya güncelle
                    if existing_news:
                        haber = existing_news
                        self.stdout.write(f'   🔄 Güncelleniyor: {news_data["title"][:40]}...')
                    else:
                        # Benzersiz slug oluştur
                        base_slug = slugify(news_data['title'])
                        slug = base_slug
                        counter = 1
                        while Haber.objects.filter(slug=slug).exists():
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        
                        haber = Haber(slug=slug)
                        self.stdout.write(f'   ➕ Ekleniyor: {news_data["title"][:40]}...')
                    
                    # Haber verilerini ata
                    haber.baslik = news_data['title']
                    haber.ozet = news_data['summary']
                    haber.icerik = news_data['content']
                    haber.kategori = kategori
                    haber.yazar = bot_user
                    haber.kaynak_url = news_data['url']
                    haber.federasyon_website = federation
                    haber.otomatik_eklendi = True
                    haber.yayinlandi = True
                    
                    if news_data.get('date'):
                        haber.olusturma_tarihi = news_data['date']
                    
                    haber.save()
                    
                    # Resmi ekle
                    if news_data.get('image_url'):
                        self._add_image_to_news(haber, news_data['image_url'])
                    
                    imported_count += 1
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Haber import hatası: {e}')
                    )
                    continue
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Federasyon import hatası: {e}')
            )
        
        return imported_count

    def _scrape_federation_news(self, federation, limit):
        """Federasyon sitesinden haber listesini çek"""
        news_items = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(federation.haberler_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Haber listesini bul
            news_elements = soup.select(federation.haber_listesi_selector)
            
            # Fallback: bazı sitelerde haber listesi ana sayfada olabilir veya linkler doğrudan anchor olarak bulunur
            if not news_elements:
                # 1) Eğer yapı anchor tabanlı ise doğrudan tüm anchor'ları deneyelim
                anchor_candidates = soup.select("a[href]")
                anchor_candidates = [a for a in anchor_candidates if "/haberler/" in (a.get('href') or '')]
                if anchor_candidates:
                    news_elements = anchor_candidates
                
            if not news_elements:
                # 2) Ana sayfadan dene (ör. jujitsuturkiye.com)
                try:
                    fallback_url = federation.ana_url or ''
                    if fallback_url:
                        r2 = requests.get(fallback_url, headers=headers, timeout=30, verify=False)
                        r2.raise_for_status()
                        s2 = BeautifulSoup(r2.content, 'html.parser')
                        anchor_candidates = s2.select("a[href]")
                        news_elements = [a for a in anchor_candidates if "/haberler/" in (a.get('href') or '')]
                except Exception:
                    pass
            
            if not news_elements:
                self.stdout.write(f'   ⚠️  Haber listesi bulunamadı (fallbacklar denendi)')
                return news_items
                
            # Sadece son 12 saat içindeki haberleri çekmek için zaman sınırı
            time_limit = timezone.now() - timezone.timedelta(hours=12)
            self.stdout.write(f"   🕒 Filtreleme: {time_limit} sonrası haberler (tarihsiz haberler alınmayacak)")
            
            for element in news_elements[:limit]:
                news_data = self._extract_news_from_element(element, federation)
                if news_data:
                    # Tarih kontrolü yap
                    if news_data.get('date') and news_data['date'] >= time_limit:
                        # Tam içeriği al
                        full_content = self._get_full_news_content(news_data['url'], federation)
                        if full_content:
                            news_data['content'] = full_content
                        
                        # Ana resmi al
                        image_url = self._get_main_news_image(news_data['url'], federation)
                        if image_url:
                            news_data['image_url'] = image_url
                        
                        news_items.append(news_data)
                    elif not news_data.get('date'):
                        self.stdout.write(f"   ⏭️  Tarihsiz haber atlandı: {news_data['title'][:50]}...")
                    else:
                        self.stdout.write(f"   ⏭️  Eski haber atlandı: {news_data['title'][:50]}... ({news_data['date']})")

        
        except Exception as e:
            self.stdout.write(f'   ❌ Scraping hatası: {e}')
        
        return news_items

    def _extract_news_from_element(self, element, federation):
        """Haber elementinden temel bilgileri çıkar"""
        try:
            # Anchor tabanlı listelemelerde element doğrudan <a> olabilir
            if element.name == 'a':
                href = element.get('href')
                if not href:
                    return None
                full_url = urljoin(federation.ana_url, href)
                title = element.get_text(strip=True) or full_url
            else:
                # Başlık
                title_element = None
                if getattr(federation, 'haber_baslik_selector', None):
                    title_element = element.select_one(federation.haber_baslik_selector)
                # Eğer belirlenen başlık seçici yoksa, element içindeki ilk anchor metnini dene
                if not title_element:
                    title_element = element.select_one('a')
                if not title_element:
                    return None
                title = title_element.get_text(strip=True)
                
                # Link
                link_element = None
                if getattr(federation, 'haber_link_selector', None):
                    link_element = element.select_one(federation.haber_link_selector)
                if not link_element:
                    link_element = element.select_one('a')
                if not link_element:
                    return None
                
                href = link_element.get('href')
                if not href:
                    return None
                
                # Tam URL oluştur
                full_url = urljoin(federation.ana_url, href)
            
            # Özet
            summary = ""
            if federation.haber_ozet_selector:
                summary_element = element.select_one(federation.haber_ozet_selector)
                if summary_element:
                    summary = summary_element.get_text(strip=True)
            
            # Tarih
            news_date = None
            if federation.haber_tarih_selector:
                date_element = element.select_one(federation.haber_tarih_selector)
                if date_element:
                    date_text = date_element.get_text(strip=True)
                    news_date = self._parse_turkish_date(date_text)
            
            return {
                'title': title[:200],
                'url': full_url,
                'summary': summary[:500] if summary else title[:500],
                'date': news_date
            }
        
        except Exception as e:
            return None

    def _get_full_news_content(self, url, federation):
        """Haber sayfasından tam içeriği al"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Script ve style elementlerini kaldır
            for script in soup(["script", "style"]):
                script.decompose()
            
            # İçerik selektörleri
            content_selectors = [
                'article',
                '.content',
                '.haber-icerik',
                '.news-content',
                '.post-content',
                '.entry-content',
                '.article-content',
                'main'
            ]
            
            content = ""
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    content = content_element.get_text(strip=True)
                    break
            
            # İçerik bulunamazsa body'den al
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)
            
            # İçeriği temizle
            content = re.sub(r'\s+', ' ', content)
            content = content[:10000]  # Maksimum uzunluk
            
            return content
        
        except Exception as e:
            return ""

    def _get_main_news_image(self, url, federation):
        """Haber sayfasından ana resmi al"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ana resim selektörleri
            image_selectors = [
                'img.haber-detay-image',
                '.haber-detay-image',
                'img[src*="/uploads/haberler/"]',
                'article img',
                '.content img',
                'main img'
            ]
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and self._is_valid_news_image(src):
                        return self._build_image_url(src, url)
            
            # Meta tag'den resim
            meta_image = soup.find('meta', property='og:image')
            if meta_image and meta_image.get('content'):
                return urljoin(url, meta_image['content'])
            
            return None
        
        except Exception as e:
            return None

    def _is_valid_news_image(self, src):
        """Resmin geçerli haber resmi olup olmadığını kontrol et"""
        src_lower = src.lower()
        
        # Atlanacak resimler
        skip_patterns = [
            'logo', 'icon', 'favicon', 'banner', 'header',
            'footer', 'social', 'share', 'avatar', 'profile',
            'advertisement', 'ads', 'sponsor', 'arkaplan',
            'yukleniyor', 'loading'
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
        elif src.startswith('tema/'):
            return f'https://karate.gov.tr/{src}'
        else:
            return urljoin(base_url, src)

    def _add_image_to_news(self, haber, image_url):
        """Habere resim ekle"""
        try:
            scraper = NewsScrapingService()
            image_file = scraper.download_and_process_image(image_url, haber.baslik)
            
            if image_file:
                haber.resim.save(image_file.name, image_file, save=True)
                self.stdout.write(f'     🖼️  Resim eklendi')
        
        except Exception as e:
            self.stdout.write(f'     ⚠️  Resim eklenemedi: {e}')

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