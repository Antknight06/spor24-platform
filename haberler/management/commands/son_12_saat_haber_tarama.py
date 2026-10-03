from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from haberler.models import FederasyonWebsite, Haber, Kategori
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests
from bs4 import BeautifulSoup
import time

class Command(BaseCommand):
    help = 'Son 12 saat içinde eklenen haberleri tüm sitelerde tarar ve ekler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Gerçek ekleme yapmadan sadece rapor ver',
        )

    def handle(self, *args, **options):
        # Prevent UnicodeEncodeError on Windows systems (e.g. cp1254)
        orig_stdout_write = self.stdout.write
        orig_stderr_write = self.stderr.write
        
        def safe_write(msg, *args, **kwargs):
            try:
                orig_stdout_write(msg, *args, **kwargs)
            except UnicodeEncodeError:
                clean_msg = msg.encode('ascii', errors='replace').decode('ascii')
                orig_stdout_write(clean_msg, *args, **kwargs)
                
        def safe_stderr_write(msg, *args, **kwargs):
            try:
                orig_stderr_write(msg, *args, **kwargs)
            except UnicodeEncodeError:
                clean_msg = msg.encode('ascii', errors='replace').decode('ascii')
                orig_stderr_write(clean_msg, *args, **kwargs)
                
        self.stdout.write = safe_write
        self.stderr.write = safe_stderr_write

        self.stdout.write(
            self.style.SUCCESS('\n🔍 SON 12 SAAT İÇİN HABER TARAMASI\n')
        )
        self.stdout.write('=' * 50)
        
        # Calculate the time 12 hours ago
        twelve_hours_ago = timezone.now() - timedelta(hours=12)
        
        # Get all active websites
        websites = FederasyonWebsite.objects.filter(aktif=True)
        
        if not websites.exists():
            self.stdout.write(
                self.style.WARNING('Aktif website bulunamadı.')
            )
            return
        
        self.stdout.write(f'Taranacak website sayısı: {websites.count()}')
        self.stdout.write(f'Tarama başlangıç zamanı: {twelve_hours_ago.strftime("%Y-%m-%d %H:%M:%S")}')
        
        total_new_news = 0
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
                    continue
                
                new_news_count = 0
                for item in news_items:
                    # Check if this news already exists
                    if self.news_exists(item['url']):
                        continue
                    
                    # Check if the news is from the last 12 hours
                    if item['date'] and item['date'] < twelve_hours_ago:
                        continue
                    
                    # Add the news if not in dry-run mode
                    if not options['dry_run']:
                        if self.add_news_item(item, website):
                            new_news_count += 1
                            total_new_news += 1
                    else:
                        new_news_count += 1
                        total_new_news += 1
                
                if new_news_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {website.ad} - {new_news_count} yeni haber eklendi')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {website.ad} - Yeni haber bulunamadı')
                    )
                
                # Record TaramaLog on success
                if not options['dry_run']:
                    from haberler.models import TaramaLog
                    TaramaLog.objects.create(
                        federasyon_website=website,
                        durum='basarili',
                        eklenen_sayi=new_news_count,
                        mesaj=f"{new_news_count} adet yeni haber eklendi." if new_news_count > 0 else "Yeni haber bulunamadı."
                    )
                
                total_checked_sites += 1
                
                # Be respectful to the servers - add a small delay
                time.sleep(1)
                
            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {website.ad} - Website erişim hatası: {e}')
                )
                if not options['dry_run']:
                    from haberler.models import TaramaLog
                    TaramaLog.objects.create(
                        federasyon_website=website,
                        durum='hata',
                        eklenen_sayi=0,
                        mesaj=f"Erişim hatası: {str(e)[:500]}"
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {website.ad} - İşleme hatası: {e}')
                )
                if not options['dry_run']:
                    from haberler.models import TaramaLog
                    TaramaLog.objects.create(
                        federasyon_website=website,
                        durum='hata',
                        eklenen_sayi=0,
                        mesaj=f"İşleme hatası: {str(e)[:500]}"
                    )
        
        self.stdout.write('\n' + '=' * 50)
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'🔍 Tarama tamamlandı! {total_checked_sites} website tarandı, {total_new_news} potansiyel yeni haber bulundu.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Tarama ve ekleme tamamlandı! {total_checked_sites} website tarandı, {total_new_news} yeni haber eklendi.')
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
        # This is a simplified implementation
        # In a real application, you would need more sophisticated date parsing
        try:
            # Try common Turkish date formats
            import re
            from django.utils.dateparse import parse_datetime, parse_date
            
            # Try ISO format first
            dt = parse_datetime(date_text)
            if dt:
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            
            # Try date only format
            d = parse_date(date_text)
            if d:
                return timezone.make_aware(timezone.datetime.combine(d, timezone.datetime.min.time()))
                
        except Exception:
            pass
        
        return None
    
    def news_exists(self, url):
        """Check if a news item with the given URL already exists"""
        return Haber.objects.filter(kaynak_url=url).exists()
    
    def add_news_item(self, item, website):
        """Add a new news item to the database"""
        try:
            # Get or create category for this website
            kategori, created = Kategori.objects.get_or_create(
                slug=website.ad.lower().replace(' ', '-'),
                defaults={
                    'ad': website.ad,
                    'federasyon_website': website
                }
            )
            
            # Get or create bot user
            from django.contrib.auth.models import User
            bot_user, created = User.objects.get_or_create(
                username='newsbot',
                defaults={
                    'email': 'newsbot@antnews.com',
                    'first_name': 'News',
                    'last_name': 'Bot',
                    'is_active': True
                }
            )
            
            # Generate slug from title
            from django.utils.text import slugify
            base_slug = slugify(item['title'][:50])  # Limit length
            if not base_slug:
                base_slug = "haber"
            
            slug = base_slug
            counter = 1
            while Haber.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Create the news item
            haber = Haber.objects.create(
                baslik=item['title'][:200],  # Limit to max_length
                slug=slug,
                ozet=item['summary'][:500] if item['summary'] else item['title'][:200],  # Limit to max_length
                icerik=item['summary'] or item['title'],  # Use summary or title as content
                kategori=kategori,
                yazar=bot_user,
                kaynak_url=item['url'],
                federasyon_website=website,
                otomatik_eklendi=True,
                yayinlandi=False
            )
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'      Haber ekleme hatası: {e}')
            )
            return False