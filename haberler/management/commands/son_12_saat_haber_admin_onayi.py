from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from haberler.models import FederasyonWebsite, Haber, Kategori, BekleyenHaber
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests
from bs4 import BeautifulSoup
import time

class Command(BaseCommand):
    help = 'Son 4 saat içinde eklenen haberleri tüm sitelerde tarar ve admin onayı için bekleyen haberlere ekler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🔍 SON 4 SAAT İÇİN HABER TARAMASI (Admin Onayı İçin)\n')
        )
        self.stdout.write('=' * 50)
        
        # Calculate the time 4 hours ago
        four_hours_ago = timezone.now() - timedelta(hours=4)
        
        # Get all active websites
        websites = FederasyonWebsite.objects.filter(aktif=True)
        
        if not websites.exists():
            self.stdout.write(
                self.style.WARNING('Aktif website bulunamadı.')
            )
            return
        
        self.stdout.write(f'Taranacak website sayısı: {websites.count()}')
        self.stdout.write(f'Tarama başlangıç zamanı: {four_hours_ago.strftime("%Y-%m-%d %H:%M:%S")}')
        
        total_new_pending_news = 0
        total_checked_sites = 0
        
        # Process each website
        for website in websites:
            self.stdout.write(f'\n🌐 {website.ad} taranıyor...')
            
            try:
                # Try to fetch the news page with browser headers to avoid 403 ModSecurity blocks
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
                }
                response = requests.get(website.haberler_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Parse the content
                import warnings
                from bs4 import XMLParsedAsHTMLWarning
                warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find news items using the configured selectors
                news_items = self.extract_news_items(soup, website)
                
                if not news_items:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  {website.ad} için haber bulunamadı veya seçici hatalı')
                    )
                    # Update website status on empty but successful scrape
                    website.hata_durumu = False
                    website.son_hata_mesaji = ""
                    website.son_tarama = timezone.now()
                    website.save()
                    continue
                
                new_pending_news_count = 0
                for item in news_items:
                    # Check if this news already exists in pending news
                    if self.pending_news_exists(item['url']):
                        continue
                    
                    # Check if this news already exists in published news
                    if self.published_news_exists(item['url']):
                        continue
                        
                    # Check title similarity (%85)
                    if self.is_duplicate_title(item['title'], website):
                        self.stdout.write(f'   ⏭️  Atlandı (benzer başlık): {item["title"][:50]}...')
                        continue
                    
                    # Check if the news is from the last 4 hours
                    if item['date'] and item['date'] < four_hours_ago:
                        continue
                    
                    # Add the news to pending news
                    if self.add_pending_news_item(item, website):
                        new_pending_news_count += 1
                        total_new_pending_news += 1
                
                if new_pending_news_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {website.ad} - {new_pending_news_count} haber admin onayı için eklendi')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {website.ad} - Yeni haber bulunamadı')
                    )
                
                # Update website status on success
                website.hata_durumu = False
                website.son_hata_mesaji = ""
                website.son_tarama = timezone.now()
                website.save()
                
                total_checked_sites += 1
                
                # Be respectful to the servers - add a small delay
                time.sleep(1)
                
            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {website.ad} - Website erişim hatası: {e}')
                )
                website.hata_durumu = True
                website.son_hata_mesaji = f"Website erişim hatası: {str(e)}"
                website.save()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {website.ad} - İşleme hatası: {e}')
                )
                website.hata_durumu = True
                website.son_hata_mesaji = f"İşleme hatası: {str(e)}"
                website.save()
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Tarama tamamlandı! {total_checked_sites} website tarandı, {total_new_pending_news} yeni haber admin onayı için eklendi.')
        )
    
    def extract_news_items(self, soup, website):
        """Extract news items from the website using configured selectors"""
        news_items = []
        
        try:
            # Check if it is an RSS feed
            is_rss = False
            if website.haberler_url.endswith('.rss') or website.haberler_url.endswith('.xml') or 'rss' in website.haberler_url.lower() or 'xml' in website.haberler_url.lower():
                is_rss = True
                
            if is_rss or not website.haber_listesi_selector:
                # Parse as RSS
                try:
                    import re
                    items = soup.find_all('item')
                    if items:
                        for item in items:
                            title_el = item.find('title')
                            link_el = item.find('link')
                            desc_el = item.find('description')
                            pubdate_el = item.find('pubdate') or item.find('pubDate')
                            
                            title = title_el.get_text(strip=True) if title_el else "Başlıksız"
                            link = link_el.get_text(strip=True) if link_el else ""
                            if not link and link_el:
                                # Try next sibling or text node
                                link = link_el.next_sibling.strip() if link_el.next_sibling and isinstance(link_el.next_sibling, str) else ""
                            if not link and link_el:
                                link = link_el.get('href', '')
                            
                            if not link:
                                continue
                                
                            date = None
                            if pubdate_el:
                                date_text = pubdate_el.get_text(strip=True)
                                try:
                                    import email.utils
                                    date = email.utils.parsedate_to_datetime(date_text)
                                except Exception:
                                    pass
                                    
                            summary = desc_el.get_text(strip=True) if desc_el else ""
                            summary = re.sub(r'<[^>]+>', '', summary).strip()
                            
                            news_items.append({
                                'title': title,
                                'url': link,
                                'date': date,
                                'summary': summary
                            })
                        return news_items
                except Exception as rss_err:
                    self.stdout.write(self.style.WARNING(f"      RSS ayrıştırma hatası: {rss_err}"))
            
            # Find news list
            news_list = soup.select(website.haber_listesi_selector) if website.haber_listesi_selector else []
            
            for item in news_list:
                try:
                    # Extract title
                    title_element = item.select_one(website.haber_baslik_selector) if website.haber_baslik_selector else None
                    title = title_element.get_text(strip=True) if title_element else "Başlıksız"
                    
                    # Extract link
                    link_element = item.select_one(website.haber_link_selector) if website.haber_link_selector else None
                    if not link_element:
                        continue
                    
                    link = link_element.get('href')
                    if not link:
                        continue
                    
                    # Make absolute URL if needed
                    if link.startswith('/'):
                        from urllib.parse import urljoin
                        link = urljoin(website.haberler_url, link)
                    
                    # Validate URL
                    validator = URLValidator()
                    try:
                        validator(link)
                    except ValidationError:
                        continue
                    
                    # Extract date if available
                    date = None
                    if website.haber_tarih_selector:
                        date_element = item.select_one(website.haber_tarih_selector)
                        if date_element:
                            date_text = date_element.get_text(strip=True)
                            date = self.parse_date(date_text)
                    
                    # Extract summary if available
                    summary = ""
                    if website.haber_ozet_selector:
                        summary_element = item.select_one(website.haber_ozet_selector)
                        if summary_element:
                            summary = summary_element.get_text(strip=True)
                    
                    news_items.append({
                        'title': title,
                        'url': link,
                        'date': date,
                        'summary': summary
                    })
                    
                except Exception as e:
                    # Skip individual news items with errors
                    continue
                    
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'      Haber çıkarma hatası: {e}')
            )
        
        return news_items
    
    def parse_date(self, date_text):
        """Parse date text into datetime object"""
        if not date_text:
            return None
            
        try:
            # Clean the date text
            date_text = date_text.strip().lower()
            
            # Try common Turkish date formats
            import re
            from django.utils.dateparse import parse_datetime, parse_date
            from django.utils import timezone as dj_timezone
            import datetime
            
            # Try ISO format first
            dt = parse_datetime(date_text)
            if dt:
                return dj_timezone.make_aware(dt) if dj_timezone.is_naive(dt) else dt
            
            # Try date only format
            d = parse_date(date_text)
            if d:
                return dj_timezone.make_aware(datetime.datetime.combine(d, datetime.datetime.min.time()))
            
            # Try common Turkish formats
            # Format: 24.09.2025 or 24.09.2025 13:00
            turkish_pattern1 = r'(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2}))?'
            match = re.match(turkish_pattern1, date_text)
            if match:
                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if match.group(4):  # Time is present
                    hour, minute = int(match.group(4)), int(match.group(5))
                    dt = datetime.datetime(year, month, day, hour, minute)
                else:
                    dt = datetime.datetime(year, month, day)
                return dj_timezone.make_aware(dt)
            
            # Format: 24 Eylül 2025 or 24 Eylül 2025 13:00
            months_tr = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            for month_name, month_num in months_tr.items():
                if month_name in date_text:
                    # Extract day and year
                    parts = date_text.split()
                    for part in parts:
                        if part.isdigit():
                            if len(part) == 4:  # Year
                                year = int(part)
                            elif len(part) <= 2:  # Day
                                day = int(part)
                    
                    # Extract time if present
                    hour, minute = 0, 0
                    time_match = re.search(r'(\d{1,2}):(\d{2})', date_text)
                    if time_match:
                        hour, minute = int(time_match.group(1)), int(time_match.group(2))
                    
                    dt = datetime.datetime(year, month_num, day, hour, minute)
                    return dj_timezone.make_aware(dt)
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'      Tarih ayrıştırma hatası: {e} - "{date_text}"')
            )
            pass
        
        return None
    
    def pending_news_exists(self, url):
        """Check if a pending news item with the given URL already exists"""
        return BekleyenHaber.objects.filter(kaynak_url=url).exists()
    
    def published_news_exists(self, url):
        """Check if a published news item with the given URL already exists"""
        return Haber.objects.filter(kaynak_url=url).exists()
    
    def add_pending_news_item(self, item, website):
        """Add a new pending news item to the database"""
        try:
            # Extract image URL
            from haberler.services.news_scraper import NewsScrapingService
            scraper = NewsScrapingService()
            image_urls = scraper.get_news_images(item['url'])
            image_url = image_urls[0] if image_urls else None
            
            # Create the pending news item
            pending_news = BekleyenHaber.objects.create(
                baslik=item['title'][:200],  # Limit to max_length
                ozet=item['summary'][:500] if item['summary'] else item['title'][:200],  # Limit to max_length
                icerik=item['summary'] or item['title'],  # Use summary or title as content
                kaynak_url=item['url'],
                kaynak_resim_url=image_url,  # New field!
                federasyon_website=website,
                haber_tarihi=item['date']  # Store the actual news publication date
            )
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'      Bekleyen haber ekleme hatası: {e}')
            )
            return False

    def is_duplicate_title(self, title, website):
        """Check if a similar news title exists in the database within this federation/category"""
        from difflib import SequenceMatcher
        from haberler.models import Kategori
        
        category = Kategori.objects.filter(federasyon_website=website).first()
        if not category:
            return False
            
        recent_published = list(Haber.objects.filter(kategori=category).order_by('-olusturma_tarihi')[:30].values_list('baslik', flat=True))
        recent_pending = list(BekleyenHaber.objects.filter(federasyon_website=website).order_by('-olusturma_tarihi')[:30].values_list('baslik', flat=True))
        
        for existing_title in recent_published + recent_pending:
            ratio = SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if ratio >= 0.85:
                return True
        return False