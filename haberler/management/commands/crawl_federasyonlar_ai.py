import asyncio
import os
import sys
import logging
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin, urlparse

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
    'turnuva-haberleri', 'default.aspx', 'egitim-kosesi', 'denklik',
    'projeler-ve-faaliyetler', 'arsiv', 'rekor', 'tesis', 'baskanimiz',
    'resource-limit', 'error', 'hata', '404', '500', '503', '508',
    'hemen-izle', 'taf-tv', 'tv-hemen', 'canli-yayin', 'video-izle',
    'ova_dep', 'ova_sev', 'youtube'
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
    'talep formu', 'başvuru formu', 'harç ve katılım', 'faaliyet programı',
    'faaliyet takvimi', 'kurs ve seminer haberleri', 'resmi turnuva haberleri',
    'uluslararası turnuva haberleri', 'başkanımız', 'bakanımız', 'dr. osman aşkın bak',
    'osman aşkın bak', 'genel sekreter', 'ana sayfa', 'kurumsal', 'iletişim',
    'misyon', 'vizyon', 'tarihçe', 'banka hesap', 'sicil lisans', 'tescil işlemleri',
    'divan tutanağı', 'olağan genel kurul', 'olağanüstü genel kurul', 'seçim duyurusu',
    'delege listesi', 'rehberi', 'kılavuzu', 'eğitim köşesi', 'denklik işlemleri',
    'projeler ve faaliyetler', 'sponsorluk', 'satın alma', 'ihale',
    'hakem el kitabı', 'hakem bilgi formu', 'telefon ve e-posta', 'sosyal medya hesapları',
    'kursu açılıyor', 'aday hakem', 'kademe', 'semineri duyurusu', 'antrenörlük kursu',
    'müsabaka sonuçları'
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

def extract_date_from_text(text):
    if not text:
        return None
    m = re.search(r'(\d{1,2})[-–\s]+(?:\d{1,2})?[-–\s]*([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\s+(202[0-9])', text)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        if month_name in MONTHS_TR:
            month = MONTHS_TR[month_name]
            try:
                return datetime(year, month, day, tzinfo=timezone.utc)
            except:
                pass
    
    m_num = re.search(r'(\d{1,2})[./](\d{1,2})[./](202[0-9])', text)
    if m_num:
        try:
            return datetime(int(m_num.group(3)), int(m_num.group(2)), int(m_num.group(1)), tzinfo=timezone.utc)
        except:
            pass
    return None

class Command(BaseCommand):
    help = "Crawl4AI Powered Intelligent Federation News Scraper with Strict Gatekeeper"

    def add_arguments(self, parser):
        parser.add_argument('--fed-id', type=int, help='Crawl a specific federation by ID')
        parser.add_argument('--limit', type=int, default=3, help='Max news per federation')

    def handle(self, *args, **options):
        fed_id = options.get('fed_id')
        limit = options.get('limit', 3)
        
        self.stdout.write(self.style.SUCCESS("🚀 Starting Crawl4AI Intelligent Federation News Pipeline..."))
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

    async def crawl_federation(self, crawler, fed, limit=3):
        self.stdout.write(f"\n🌐 [{fed.ad}] Scanning: {fed.haberler_url}")
        try:
            run_cfg = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000,
                delay_before_return_html=2.0
            )
            result = await crawler.arun(url=fed.haberler_url, config=run_cfg)
            if not result.success or (getattr(result, 'status_code', None) and result.status_code >= 400):
                self.stdout.write(self.style.WARNING(f"   ⚠️ Failed to crawl {fed.ad}: Status {getattr(result, 'status_code', 'Unknown')}"))
                return

            candidates = self.discover_news_links(result, fed)
            self.stdout.write(f"   🎯 Discovered {len(candidates)} high-probability news links. Processing up to {limit}...")

            added_count = 0
            for item in candidates:
                if added_count >= limit:
                    break
                created = await self.process_article(crawler, fed, item)
                if created:
                    added_count += 1

            self.stdout.write(self.style.SUCCESS(f"   ✅ Finished {fed.ad}: {added_count} new high-quality articles ingested."))

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
            # 1. URL Path Token Filter
            if any(token in path_lower for token in BANNED_PATH_TOKENS):
                continue

            # 2. Old Date Regex in URL (Filter out dates older than last 7 days of Sept 2026)
            if re.search(r'/202[0-5]/|/2026/0[1-8]/|/2026/09/0[1-9]/|/2026/09/1[0-9]/', path_lower):
                continue

            # 3. Already Exists Check
            if BekleyenHaber.objects.filter(kaynak_url=full_url).exists() or Haber.objects.filter(kaynak_url=full_url).exists():
                continue

            # 4. Text Length Check
            if len(text) < 15 or len(text.split()) < 3:
                continue

            # 5. Link Text Blacklist Check
            t_lower = text.lower()
            if any(token in t_lower for token in BANNED_TITLE_TOKENS):
                continue

            # Past years filter in text or URL
            if any(str(py) in t_lower or f"/{py}/" in path_lower for py in range(2010, 2026)):
                continue

            if any(f"{py} faaliyet" in t_lower for py in ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']):
                continue

            seen_urls.add(full_url)
            candidates.append({
                'title': text,
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

            raw_html = detail_res.html
            
            extracted_text = trafilatura.extract(raw_html, include_comments=False, include_tables=False)
            metadata = trafilatura.extract_metadata(raw_html)
            
            # Strict Date Gatekeeper (Last 7 days only: 2026-09-21 to present)
            article_date = None
            if metadata and metadata.date:
                try:
                    dt_str = str(metadata.date)[:10]
                    parsed_dt = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if parsed_dt.year < 2026:
                        self.stdout.write(f"      ⏭️ Skipping old article from {parsed_dt.year}: {item['title'][:40]}")
                        return False
                    
                    # 7-day freshness check
                    cutoff_dt = datetime(2026, 9, 21, tzinfo=timezone.utc)
                    if parsed_dt < cutoff_dt:
                        self.stdout.write(f"      ⏭️ Skipping article older than 7 days ({dt_str}): {item['title'][:40]}")
                        return False
                    article_date = parsed_dt
                except Exception as d_err:
                    pass

            title = (metadata.title if metadata and metadata.title and len(metadata.title) > 15 else item['title']).strip()
            
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

            # Text Event Date Gatekeeper: ALWAYS check if the text mentions an older event date (e.g. August or early September)
            detected_dt = extract_date_from_text(content[:600]) or extract_date_from_text(title)
            if detected_dt:
                cutoff_dt = datetime(2026, 9, 21, tzinfo=timezone.utc)
                if detected_dt.year < 2026 or detected_dt < cutoff_dt:
                    self.stdout.write(f"      ⏭️ Skipping article with old event date in text ({detected_dt.strftime('%Y-%m-%d')}): {title[:40]}")
                    return False
                article_date = detected_dt

            # Content Heuristics: Reject corporate/menu spam and server errors
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

            menu_indicators = ['taf mağaza', 'e-taf', 'giriş yap', 'ana sayfa kurumsal', 'yönetim kurulu üyeleri', 'çerez politikası', 'kişisel verilerin korunması']
            if any(mi in c_lower for mi in menu_indicators):
                self.stdout.write(f"      🛑 Rejecting institutional menu page: {title[:45]}")
                return False

            if len(content) < 80:
                self.stdout.write(f"      🛑 Rejecting content too short ({len(content)} chars): {title[:45]}")
                return False

            summary = content[:250] + ("..." if len(content) > 250 else "")

            # Strict Image Filtering
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

            # STRICT REQUIREMENT: DISCARD ARTICLE IF NO REAL NEWS PHOTO WAS EXTRACTED AND DOWNLOADED
            if not downloaded_img:
                self.stdout.write(f"      🛑 Rejecting article: NO REAL NEWS PHOTO ({title[:45]})")
                return False

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
