import asyncio
import os
import sys
import logging
import re
from datetime import datetime, timedelta, timezone as dt_tz
from django.utils import timezone
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

# Allow Django ORM in async context for management command
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.management.base import BaseCommand
from django.conf import settings
from haberler.models import FederasyonWebsite, BekleyenHaber, Kategori, Haber

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import trafilatura

logger = logging.getLogger(__name__)

BANNED_PATH_TOKENS = [
    'kurul', 'hakkinda', 'yonetim', 'plan', 'baskan', 'tuzuk', 'mevzuat',
    'talimat', 'teskilat', 'temsilci', 'iletisim', 'kvkk', 'privacy',
    'federasyon', 'misyon', 'vizyon', 'tarihce', 'logo', 'sponsor',
    'kulup', 'hakem', 'takvim', 'brans', 'faaliyet-takvimi', 'faaliyet-programi',
    'banka', 'hesap', 'uye', 'kayit', 'login', 'admin', 'auth',
    'muhasebe', 'mali', 'idari', 'yazi-isleri', 'form', 'talep', 'dilekce',
    'harc', 'harcirah', 'katilim-payi', 'cerez', 'politika', 'aydinlatma',
    'kanun', 'yonetmelik', 'statu', 'statü', 'dokuman', 'download', 'dosyalar',
    'sayfa.php', '/sayfa/', 'kategori/', 'category/', 'kurs-ve-seminer',
    'default.aspx', 'egitim-kosesi', 'denklik',
    'projeler-ve-faaliyetler', 'arsiv', 'rekor', 'tesis', 'baskanimiz',
    'resource-limit', 'error', 'hata', '404', '500', '503', '508',
    'hemen-izle', 'taf-tv', 'tv-hemen', 'canli-yayin', 'video-izle',
    'ova_dep', 'ova_sev', 'youtube',
    # Anti-clog & Anti-gallery tokens (Prevents TVF and others from trapping the crawler)
    'galeri', 'gallery', 'lig/', 'ligler', 'akreditasyon', 'sampiyonlar-kupasi',
    'puan-durumu', 'fikstur', 'mac-sonucu', 'foto-galeri', 'videos', 'videolar',
    'tedavi', 'tescil', 'evrak', 'hizmet-pasaportu', 'sosyal-medya'
]

BANNED_TITLE_TOKENS = [
    # Server / Hosting / Web errors
    'resource limit', 'service unavailable', 'bad gateway', 'gateway time-out',
    'internal server error', 'page not found', 'not found', 'sayfa bulunamadı',
    'hata oluştu', 'forbidden', 'access denied', 'just a moment', 'attention required',
    'ddos-guard', 'bevor sie zu youtube', 'temporarily unable', 'exceeded resource limit',
    
    # Video / Stream / TV / Consent
    'youtube', 'taf tv', 'hemen izle', 'canlı izle', 'video -', 'tv hemen',
    
    # Weather / Non-news / Static / Institutional
    'hava durumu', 'canlı rüzgar', 'rüzgar', 'km/h',
    'muhasebe', 'mali işler', 'mali genel kurul', 'idari işler', 'branş işlemleri',
    'kişisel veri', 'kvkk', 'çerez', 'gizlilik politikası', 'aydınlatma metni',
    'kanun ve yönetmelik', 'tüzük', 'talimat', 'yönetim kurulu', 'denetim kurulu',
    'disiplin kurulu', 'koordinasyon kurulu', 'merkez hakem kurulu', 'şeref aylığı',
    'talep formu', 'başvuru formu', 'harç ve katılım',
    'başkanımız', 'bakanımız', 'dr. osman aşkın bak',
    'osman aşkın bak', 'genel sekreter', 'ana sayfa', 'kurumsal', 'iletişim',
    'misyon', 'vizyon', 'tarihçe', 'banka hesap', 'sicil lisans', 'tescil işlemleri',
    'divan tutanağı', 'olağan genel kurul', 'olağanüstü genel kurul', 'seçim duyurusu',
    'delege listesi', 'rehberi', 'kılavuzu', 'eğitim köşesi', 'denklik işlemleri',
    'sponsorluk', 'satın alma', 'ihale',
    'hakem el kitabı', 'hakem bilgi formu', 'telefon ve e-posta', 'sosyal medya hesapları'
]

BANNED_IMAGE_TOKENS = [
    'logo', 'icon', 'banner', 'avatar', 'spacer', 'blank', 'pixel',
    'resim_yok', 'resimyok', 'no_image', 'no-image', 'noimg',
    'placeholder', 'default_image', 'default.jpg', 'default.png',
    'yok.jpg', 'yok.png', 'gecici', 'dummy'
]

MONTHS_TR = {
    'ocak': 1, 'şubat': 2, 'subat': 2, 'mart': 3, 'nisan': 4,
    'mayıs': 5, 'mayis': 5, 'haziran': 6, 'temmuz': 7,
    'ağustos': 8, 'agustos': 8, 'eylül': 9, 'eylul': 9,
    'ekim': 10, 'kasım': 11, 'kasim': 11, 'aralık': 12, 'aralik': 12
}

PAST_MONTHS_NAMES = [
    'ağustos', 'agustos', 'temmuz', 'haziran', 'mayıs', 'mayis',
    'nisan', 'mart', 'şubat', 'subat', 'ocak'
]

def extract_date_from_text(text):
    if not text:
        return None
    # 1. 21-23 Ağustos 2026 or 21 Ağustos 2026
    m = re.search(r'(\d{1,2})[-–\s]+(?:\d{1,2})?[-–\s]*([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\s+(202[0-9])', text)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        if month_name in MONTHS_TR:
            month = MONTHS_TR[month_name]
            try:
                return datetime(year, month, day, tzinfo=dt_tz.utc)
            except Exception:
                pass

    # 2. 21-23 Ağustos (without explicit year, infer current year 2026)
    m2 = re.search(r'(\d{1,2})[-–\s]+(?:\d{1,2})?[-–\s]*([a-zA-ZçğıöşüÇĞİÖŞÜ]+)', text)
    if m2:
        day = int(m2.group(1))
        month_name = m2.group(2).lower()
        if month_name in MONTHS_TR:
            month = MONTHS_TR[month_name]
            try:
                return datetime(datetime.now().year, month, day, tzinfo=dt_tz.utc)
            except Exception:
                pass
    
    # 3. 21.08.2026 or 21/08/2026
    m_num = re.search(r'(\d{1,2})[./](\d{1,2})[./](202[0-9])', text)
    if m_num:
        try:
            return datetime(int(m_num.group(3)), int(m_num.group(2)), int(m_num.group(1)), tzinfo=dt_tz.utc)
        except Exception:
            pass

    # 4. 2026-08-21
    m_iso = re.search(r'(202[0-9])[-/](\d{1,2})[-/](\d{1,2})', text)
    if m_iso:
        try:
            return datetime(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)), tzinfo=dt_tz.utc)
        except Exception:
            pass

    return None

class Command(BaseCommand):
    help = "Crawl4AI Powered Intelligent Federation News Scraper with Balanced Ingestion"

    def add_arguments(self, parser):
        parser.add_argument('--fed-id', type=int, help='Crawl a specific federation by ID')
        parser.add_argument('--limit', type=int, default=3, help='Max news per federation')

    def handle(self, *args, **options):
        fed_id = options.get('fed_id')
        limit = options.get('limit', 3)
        
        self.stdout.write(self.style.SUCCESS("🚀 Starting Crawl4AI Intelligent Multi-Sport News Pipeline..."))
        feds = list(FederasyonWebsite.objects.filter(aktif=True))
        if fed_id:
            feds = [f for f in feds if f.id == fed_id]

        asyncio.run(self.run_pipeline(feds, limit))

    async def run_pipeline(self, feds, limit=3):
        browser_cfg = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        self.stdout.write(f"📋 Loaded {len(feds)} active federations to crawl.")

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            for fed in feds:
                await self.crawl_federation(crawler, fed, limit)

    def crawl_rss_feed(self, fed, limit=3):
        """Directly parses RSS/XML feeds (e.g. TRT Haber Spor) cleanly and quickly"""
        self.stdout.write(f"\n📡 [{fed.ad}] Parsing RSS Feed: {fed.haberler_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Spor24/1.0',
        }
        try:
            r = requests.get(fed.haberler_url, headers=headers, timeout=15)
            root = ET.fromstring(r.content)
            items = root.findall('.//item')
            self.stdout.write(f"   🎯 Found {len(items)} RSS items. Processing up to {limit}...")
            
            category = Kategori.objects.filter(federasyon_website=fed).first()
            added = 0
            
            for item in items:
                if added >= limit:
                    break
                link_el = item.find('link')
                title_el = item.find('title')
                desc_el = item.find('description')
                
                url = link_el.text.strip() if link_el is not None and link_el.text else ""
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                content = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                
                if not url or not title:
                    continue
                
                if BekleyenHaber.objects.filter(kaynak_url=url).exists() or Haber.objects.filter(kaynak_url=url).exists():
                    continue
                
                # Image
                best_image = None
                enclosure = item.find('enclosure')
                if enclosure is not None and 'image' in enclosure.attrib.get('type', ''):
                    best_image = enclosure.attrib.get('url')
                if not best_image:
                    media_content = item.find('{http://search.yahoo.com/mrss/}content')
                    if media_content is not None:
                        best_image = media_content.attrib.get('url')

                # KRİTİK: Eğer RSS XML içinde görsel yoksa, haberin kendi sayfasına gidip gerçek görseli çıkar!
                if not best_image and url:
                    from haberler.ai_news_engine import extract_article_image_direct
                    best_image = extract_article_image_direct(url)
                        
                downloaded_img = None
                if best_image:
                    try:
                        from haberler.services.news_scraper import NewsScrapingService
                        ns = NewsScrapingService()
                        downloaded_img = ns.download_and_process_image_fit(best_image, title, target_size=(1200, 675))
                    except Exception as img_err:
                        logger.warning(f"Could not download RSS image for {url}: {img_err}")
                        
                pending = BekleyenHaber(
                    baslik=title,
                    ozet=content[:250] if content else title,
                    icerik=content or title,
                    kaynak_url=url,
                    kaynak_resim_url=best_image,
                    federasyon_website=fed,
                    kategori=category,
                    haber_tarihi=timezone.now()
                )
                if downloaded_img:
                    pending.resim.save(downloaded_img.name, downloaded_img, save=False)
                pending.save()
                
                try:
                    import threading
                    from haberler.ai_news_engine import ozgunlestir_haber
                    threading.Thread(target=ozgunlestir_haber, args=(pending,), daemon=True).start()
                except Exception:
                    pass
                    
                added += 1
                self.stdout.write(self.style.SUCCESS(f"      ✨ RSS INGESTED (ID: {pending.id}): {title[:55]}... [Image: {'PHOTO' if downloaded_img else ('LOGO' if fed.logo else 'NONE')}]"))
            return added
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ RSS Error for {fed.ad}: {e}"))
            return 0

    async def crawl_federation(self, crawler, fed, limit=3):
        # 1. Fast-path for RSS Feeds
        feed_url = fed.haberler_url.lower()
        if '.rss' in feed_url or '/feed' in feed_url or 'rss' in feed_url:
            self.crawl_rss_feed(fed, limit)
            return

        self.stdout.write(f"\n🌐 [{fed.ad}] Scanning: {fed.haberler_url}")
        try:
            run_cfg = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000,
                delay_before_return_html=2.0
            )
            # Timeout safeguard per federation (maximum 45s for homepage scan)
            result = await asyncio.wait_for(crawler.arun(url=fed.haberler_url, config=run_cfg), timeout=45)
            if not result.success or (getattr(result, 'status_code', None) and result.status_code >= 400):
                self.stdout.write(self.style.WARNING(f"   ⚠️ Failed to crawl {fed.ad}: Status {getattr(result, 'status_code', 'Unknown')}"))
                return

            candidates = self.discover_news_links(result, fed)
            self.stdout.write(f"   🎯 Discovered {len(candidates)} high-probability news links. Processing up to {limit}...")

            added_count = 0
            tested_count = 0
            for item in candidates:
                if added_count >= limit or tested_count >= 8:
                    break
                tested_count += 1
                created = await self.process_article(crawler, fed, item)
                if created:
                    added_count += 1

            self.stdout.write(self.style.SUCCESS(f"   ✅ Finished {fed.ad}: {added_count} new high-quality articles ingested."))

        except asyncio.TimeoutError:
            self.stdout.write(self.style.WARNING(f"   ⏱️ Scan timed out for {fed.ad}. Moving to next federation."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error crawling {fed.ad}: {e}"))

    def discover_news_links(self, result, fed):
        """Intelligently detects real news article links from Crawl4AI link graph with strict filtering"""
        base_domain = urlparse(fed.ana_url).netloc.lower()
        candidates = []
        seen_urls = set()

        internal_links = result.links.get("internal", [])
        for link_obj in internal_links:
            href = link_obj.get("href", "").strip()
            text = link_obj.get("text", "").strip()
            link_title = link_obj.get("title", "").strip()
            if not href:
                continue

            full_url = urljoin(fed.ana_url, href)
            parsed = urlparse(full_url)

            if base_domain not in parsed.netloc.lower():
                continue

            if full_url in seen_urls:
                continue

            clean_path = parsed.path.strip('/')
            if not clean_path or clean_path in ['haberler', 'duyurular', 'news', 'announcements', 'category/genel']:
                continue

            path_lower = parsed.path.lower()
            
            # Special strict filter for TVF: only real news announcements under /icerik/
            if 'tvf.org.tr' in base_domain:
                if '/icerik/' not in path_lower or '/icerikler/' in path_lower or '/galeri/' in path_lower or '/lig/' in path_lower:
                    continue

            # 1. URL Path Token Filter
            if any(token in path_lower for token in BANNED_PATH_TOKENS):
                continue

            # 2. Old Date Regex in URL (Filter out dates older than 2026)
            if re.search(r'/20[0-2][0-5]/', path_lower):
                continue

            # 3. Already Exists Check
            if BekleyenHaber.objects.filter(kaynak_url=full_url).exists() or Haber.objects.filter(kaynak_url=full_url).exists():
                continue

            # 4. Text or URL Slug Check (Allows modern image cards with empty <a> text)
            last_segment = clean_path.split('/')[-1]
            slug_words = [w for w in last_segment.split('-') if len(w) > 1]
            has_valid_text = len(text) >= 15 and len(text.split()) >= 3
            has_valid_slug = len(slug_words) >= 3 or any(k in path_lower for k in ['haber', 'duyuru', 'icerik', 'detay', 'sampiyona'])
            
            if not has_valid_text and not has_valid_slug:
                continue

            # Synthesize title if link text was empty (e.g. image-only card)
            best_title = text if has_valid_text else (link_title if len(link_title) >= 10 else " ".join(slug_words).capitalize())

            # 5. Link Text Blacklist Check
            t_lower = best_title.lower()
            if any(token in t_lower for token in BANNED_TITLE_TOKENS):
                continue

            # Past years filter in title or URL
            if any(str(py) in t_lower or f"/{py}/" in path_lower for py in range(2010, 2026)):
                continue

            seen_urls.add(full_url)
            candidates.append({
                'title': best_title,
                'url': full_url
            })

        return candidates

    async def process_article(self, crawler, fed, item):
        """Fetches the full article page with Crawl4AI, extracts high-res image and clean markdown text"""
        url = item['url']
        try:
            run_cfg = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=25000,
                delay_before_return_html=1.5
            )
            detail_res = await crawler.arun(url=url, config=run_cfg)
            if not detail_res.success or (getattr(detail_res, 'status_code', None) and detail_res.status_code >= 400):
                self.stdout.write(f"      🛑 Skipping HTTP error {getattr(detail_res, 'status_code', 'unknown')} for {url}")
                return False

            raw_html = detail_res.html or ""
            
            extracted_text = trafilatura.extract(raw_html, include_comments=False, include_tables=False)
            metadata = trafilatura.extract_metadata(raw_html)
            
            # Dynamic 7-day cutoff (Strict freshness requested by Editor-in-Chief)
            article_date = timezone.now()
            cutoff_dt = timezone.now() - timedelta(days=7)
            
            if metadata and metadata.date:
                try:
                    dt_str = str(metadata.date)[:10]
                    parsed_dt = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=dt_tz.utc)
                    if parsed_dt.year < 2026:
                        self.stdout.write(f"      🛑 Rejecting old article from {parsed_dt.year}: {item['title'][:40]}")
                        return False
                    
                    if parsed_dt < cutoff_dt:
                        self.stdout.write(f"      🛑 Rejecting article older than 7 days ({dt_str}): {item['title'][:40]}")
                        return False
                    article_date = parsed_dt
                except Exception as d_err:
                    logger.debug(f"Metadata date parse error: {d_err}")

            title = (metadata.title if metadata and metadata.title and len(metadata.title) > 10 else item['title']).strip()
            
            # Check Extracted Title Against Banned Tokens
            title_lower = title.lower()
            if any(token in title_lower for token in BANNED_TITLE_TOKENS):
                self.stdout.write(f"      🛑 Rejecting non-news title token: {title[:45]}")
                return False

            if any(str(py) in title_lower for py in range(2010, 2026)):
                self.stdout.write(f"      🛑 Rejecting past year article: {title[:45]}")
                return False

            content = extracted_text.strip() if extracted_text and len(extracted_text.strip()) > 80 else ""
            if not content:
                content = detail_res.markdown.raw_markdown[:3000] if hasattr(detail_res.markdown, 'raw_markdown') else str(detail_res.markdown)[:3000]

            content_lower = content[:3000].lower()

            current_year = datetime.now().year
            # Past months check (e.g. Ağustos 2026, Temmuz 2026 etc.)
            for pm in PAST_MONTHS_NAMES:
                if f"{pm} {current_year}" in content_lower or f"{pm} {current_year-1}" in content_lower:
                    self.stdout.write(f"      🛑 Rejecting past month ({pm.title()}) article: {title[:40]}")
                    return False

            # Text Event Date Gatekeeper (Scan first 2500 chars)
            detected_dt = extract_date_from_text(content[:2500]) or extract_date_from_text(title)
            if detected_dt:
                if detected_dt.year < current_year or detected_dt < cutoff_dt:
                    self.stdout.write(f"      🛑 Rejecting article with old event date ({detected_dt.strftime('%Y-%m-%d')}): {title[:40]}")
                    return False
                article_date = detected_dt

            # Server error detection
            c_lower = content.lower()
            server_errors = [
                'resource limit is reached', 'the website is temporarily unable to service your request',
                'exceeded resource limit', 'service temporarily unavailable', '503 service unavailable',
                '504 gateway time-out', '502 bad gateway', '403 forbidden', '404 not found',
                'access denied', 'bevor sie zu youtube', 'an error occurred while processing your request'
            ]
            if any(se in c_lower for se in server_errors):
                self.stdout.write(f"      🛑 Rejecting server error page content: {title[:45]}")
                return False

            menu_indicators = ['e-taf', 'giriş yap', 'ana sayfa kurumsal', 'yönetim kurulu üyeleri', 'çerez politikası', 'kişisel verilerin korunması']
            if any(mi in c_lower for mi in menu_indicators):
                self.stdout.write(f"      🛑 Rejecting institutional menu page: {title[:45]}")
                return False

            if len(content) < 80:
                self.stdout.write(f"      🛑 Rejecting content too short ({len(content)} chars): {title[:45]}")
                return False

            summary = content[:250] + ("..." if len(content) > 250 else "")

            # Strict Image Filtering & Fallback
            best_image = None
            images = detail_res.media.get("images", [])
            images_sorted = sorted(images, key=lambda x: x.get("score", 0), reverse=True)
            for img in images_sorted:
                src = img.get("src", "").strip()
                if src:
                    src = urljoin(url, src)
                    src_lower = src.lower()
                    if any(src_lower.endswith(ext) or ext in src_lower for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        if not any(k in src_lower for k in BANNED_IMAGE_TOKENS):
                            best_image = src
                            break

            # Fallback image search in raw_html
            if not best_image and raw_html:
                try:
                    soup = BeautifulSoup(raw_html, 'html.parser')
                    for img_tag in soup.find_all('img', src=True):
                        src = urljoin(url, img_tag['src'].strip())
                        src_lower = src.lower()
                        if any(src_lower.endswith(ext) or ext in src_lower for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            if not any(k in src_lower for k in BANNED_IMAGE_TOKENS):
                                best_image = src
                                break
                except Exception:
                    pass

            # Deep Direct Fallback if Crawl4AI still missed the image
            if not best_image and url:
                try:
                    from haberler.ai_news_engine import extract_article_image_direct
                    best_image = extract_article_image_direct(url)
                except Exception:
                    pass

            category = Kategori.objects.filter(federasyon_website=fed).first()

            # Pre-download and format image immediately
            downloaded_img = None
            if best_image:
                try:
                    from haberler.services.news_scraper import NewsScrapingService
                    ns = NewsScrapingService()
                    downloaded_img = ns.download_and_process_image_fit(best_image, title, target_size=(1200, 675))
                except Exception as dl_err:
                    logger.warning(f"Could not pre-download image for {url}: {dl_err}")

            pending = BekleyenHaber(
                baslik=title,
                ozet=summary or title,
                icerik=content or title,
                kaynak_url=url,
                kaynak_resim_url=best_image,
                federasyon_website=fed,
                kategori=category,
                haber_tarihi=article_date
            )
            if downloaded_img:
                pending.resim.save(downloaded_img.name, downloaded_img, save=False)
            pending.save()

            # Otomatik Yapay Zeka Ozgunlestirme & Puanlama (Aninda Arka Planda Isler)
            try:
                import threading
                from haberler.ai_news_engine import ozgunlestir_haber
                threading.Thread(target=ozgunlestir_haber, args=(pending,), daemon=True).start()
                logger.info(f"Yapay zeka ozgunlestirme arka planda baslatildi: ID #{pending.id}")
            except Exception as ai_trig_err:
                logger.warning(f"AI trigger error: {ai_trig_err}")

            # Trigger Telegram Notifications (asynchronous & safe)
            try:
                from haberler.services.notification_service import NotificationService
                NotificationService().send_new_news_notifications([{
                    'id': pending.id,
                    'federation': fed.ad,
                    'title': title,
                    'url': url,
                    'image_url': best_image or (fed.logo.url if fed.logo else None),
                    'video_url': None,
                    'is_video': False,
                    'scraper_name': 'Crawl4AI Engine'
                }])
            except Exception as notif_err:
                logger.error(f"Telegram notification dispatch error: {notif_err}")

            self.stdout.write(self.style.SUCCESS(f"      ✨ INGESTED (ID: {pending.id}): {title[:55]}... [Image: {'PHOTO' if downloaded_img else ('LOGO' if fed.logo else 'NONE')}]"))
            return True

        except Exception as e:
            self.stdout.write(f"      ⚠️ Error processing article {url}: {e}")
            return False
