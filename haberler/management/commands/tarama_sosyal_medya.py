import re
import sys
import json
import time
import requests
import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta

from haberler.models import FederasyonWebsite, BekleyenSosyalMedyaHaberi
from haberler.services.notification_service import NotificationService

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

class Command(BaseCommand):
    help = "Son 48 saatteki sosyal medya içeriklerini (YouTube, Twitter, Instagram) toplayıp Bekleyen Sosyal Medya havuzuna ekler."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Veritabanına kaydetmeden sadece bulunan gönderileri konsola yazdır'
        )
        parser.add_argument(
            '--hours',
            type=float,
            default=48.0,
            help='Kaç saat öncesine kadar olan gönderiler çekilsin (Varsayılan: 48)'
        )
        parser.add_argument(
            '--federation-ids',
            type=str,
            help='Sadece bu ID listesine sahip federasyonları tara (örn: 2,3,8)'
        )
        parser.add_argument(
            '--platforms',
            type=str,
            default='youtube,twitter,instagram',
            help='Taranacak platformlar (varsayılan: youtube,twitter,instagram)'
        )

    def log(self, message, style_func=None):
        if style_func:
            self.stdout.write(style_func(message))
        else:
            self.stdout.write(message)
        sys.stdout.flush()

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']
        now = timezone.now()
        cutoff_date = now - timedelta(hours=hours)

        self.log(f"\n🚀 SPOR24 SOSYAL MEDYA MOTORU BAŞLATILDI", self.style.SUCCESS)
        self.log(f"⏱️ Zaman Filtresi: Son {hours} saat (Cutoff: {cutoff_date.strftime('%d.%m.%Y %H:%M')})")
        self.log('=' * 65)

        federation_ids = options.get('federation_ids')
        if federation_ids:
            try:
                ids = [int(x.strip()) for x in federation_ids.split(',') if x.strip()]
                active_feds = FederasyonWebsite.objects.filter(id__in=ids)
                self.log(f"Hedef Federasyonlar (ID): {ids}")
            except ValueError:
                self.log("Geçersiz --federation-ids formatı!", self.style.ERROR)
                return
        else:
            active_feds = FederasyonWebsite.objects.filter(aktif=True)

        if not active_feds.exists():
            self.log("Taranacak federasyon bulunamadı.", self.style.WARNING)
            return

        target_platforms = [p.strip().lower() for p in options.get('platforms', '').split(',') if p.strip()]
        self.log(f"Aktif Platformlar: {', '.join(target_platforms).upper()} | Taranacak Federasyon: {active_feds.count()}\n")

        total_scanned = 0
        total_created = 0
        total_skipped = 0

        for fed in active_feds:
            fed_posts = []

            # 1. YOUTUBE
            if 'youtube' in target_platforms and fed.youtube_url:
                yt_posts = self.scrape_youtube(fed, cutoff_date)
                fed_posts.extend(yt_posts)

            # 2. X / TWITTER
            if 'twitter' in target_platforms and fed.x_url:
                tw_posts = self.scrape_twitter(fed, cutoff_date)
                fed_posts.extend(tw_posts)
                time.sleep(1.0) # Small delay to respect Twitter rate limits

            # 3. INSTAGRAM
            if 'instagram' in target_platforms and fed.instagram_url:
                ig_posts = self.scrape_instagram(fed, cutoff_date)
                fed_posts.extend(ig_posts)

            if not fed_posts:
                continue

            for post in fed_posts:
                total_scanned += 1
                post_id = post['post_id']
                
                # Deduplication check
                exists = BekleyenSosyalMedyaHaberi.objects.filter(paylasim_id=post_id).exists()
                if exists:
                    total_skipped += 1
                    continue

                if dry_run:
                    self.log(f"   [DRY-RUN] {post['platform'].upper()} -> {post['title'][:60]} ({post['paylasim_tarihi'].strftime('%d.%m %H:%M')})")
                    total_created += 1
                else:
                    img_url = post.get('image_url')
                    if not img_url or 'stock_images' in img_url:
                        self.log(f"   ⚠️ Atlandı (Görsel yok veya stok resim): {post['title'][:40]}")
                        continue

                    downloaded_img = None
                    try:
                        from haberler.services.news_scraper import NewsScrapingService
                        ns = NewsScrapingService()
                        downloaded_img = ns.download_and_process_image_fit(img_url, post['title'], target_size=(1200, 675))
                    except Exception as img_err:
                        self.log(f"   ⚠️ Görsel indirme başarısız ({post['title'][:30]}): {img_err}")

                    if not downloaded_img:
                        self.log(f"   🛑 Atlandı (Görsel kaydedilemedi): {post['title'][:40]}")
                        continue

                    try:
                        obj = BekleyenSosyalMedyaHaberi(
                            platform=post['platform'],
                            federasyon_website=fed,
                            paylasim_id=post_id,
                            baslik=post['title'][:200],
                            icerik=post['content'],
                            kaynak_url=post['url'][:500],
                            kaynak_resim_url=img_url[:600],
                            gonderi_tipi=post.get('gonderi_tipi', 'post'),
                            paylasim_tarihi=post['paylasim_tarihi']
                        )
                        obj.resim.save(downloaded_img.name, downloaded_img, save=False)
                        obj.save()
                        total_created += 1
                        badge = "🎥 YT" if post['platform'] == 'youtube' else "🐦 X" if post['platform'] == 'twitter' else "📸 IG"
                        self.log(f"   ✨ [{badge}] #{obj.id} eklendi: {fed.ad[:20]} - {obj.baslik[:45]} ({obj.paylasim_tarihi.strftime('%d.%m %H:%M')})", self.style.SUCCESS)
                    except Exception as err:
                        self.log(f"   ❌ Kayıt Hatası ({post['title'][:30]}): {err}", self.style.ERROR)

        self.log('\n' + '=' * 65)
        dry_str = " (DRY-RUN - Kaydedilmedi)" if dry_run else ""
        self.log(
            f"🎯 SOSYAL MEDYA TARAMASI TAMAMLANDI!{dry_str}\n"
            f"   * Toplam İncelenen Gönderi: {total_scanned}\n"
            f"   * Havuza Alınan Yeni İçerik (Son {hours} Saat): {total_created}\n"
            f"   * Atlanan (Mükerrer): {total_skipped}",
            self.style.SUCCESS
        )

    # =========================================================================
    # YOUTUBE HARVESTER
    # =========================================================================
    def scrape_youtube(self, fed, cutoff_date):
        posts = []
        yt_url = fed.youtube_url.strip()
        
        cache_key = f"yt_cid_{fed.id}"
        cid = cache.get(cache_key)
        
        if not cid:
            cid_match = re.search(r'(UC[\w-]{21,})', yt_url)
            if cid_match:
                cid = cid_match.group(1)
            else:
                try:
                    r = requests.get(yt_url, headers=HEADERS, timeout=5)
                    m = re.search(r'["\']channelId["\']:\s*["\'](UC[\w-]+)["\']', r.text)
                    if not m:
                        m = re.search(r'<meta itemprop="identifier" content="(UC[\w-]+)">', r.text)
                    if m:
                        cid = m.group(1)
                except Exception:
                    pass

            if cid:
                cache.set(cache_key, cid, timeout=86400 * 30)

        if not cid:
            return posts

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        try:
            res = requests.get(rss_url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'yt': 'http://www.youtube.com/xml/schemas/2015',
                    'media': 'http://search.yahoo.com/mrss/'
                }
                
                for entry in root.findall('atom:entry', ns)[:8]:
                    published_str = entry.find('atom:published', ns).text
                    pub_dt = datetime.datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    
                    if pub_dt < cutoff_date:
                        continue
                        
                    title = clean_text(entry.find('atom:title', ns).text)
                    video_id = entry.find('yt:videoId', ns).text
                    watch_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    media_group = entry.find('media:group', ns)
                    desc = ""
                    thumb_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                    if media_group is not None:
                        d_el = media_group.find('media:description', ns)
                        if d_el is not None and d_el.text:
                            desc = clean_text(d_el.text)
                        t_el = media_group.find('media:thumbnail', ns)
                        if t_el is not None:
                            thumb_url = t_el.attrib.get('url', thumb_url)

                    content = desc if desc else title
                    embed_code = f'\n<br><iframe width="100%" height="450" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="border-radius: 8px; margin-top: 15px;"></iframe>'
                    final_content = f"{content}\n{embed_code}"

                    posts.append({
                        'platform': 'youtube',
                        'post_id': f"yt_{video_id}",
                        'title': f"{fed.ad} - {title[:120]}",
                        'content': final_content,
                        'url': watch_url,
                        'image_url': thumb_url,
                        'paylasim_tarihi': pub_dt,
                        'gonderi_tipi': 'reel' if 'short' in watch_url else 'post'
                    })
        except Exception:
            pass

        return posts

    # =========================================================================
    # X / TWITTER HARVESTER (Syndication Timeline API + BeautifulSoup)
    # =========================================================================
    def scrape_twitter(self, fed, cutoff_date):
        posts = []
        raw_url = fed.x_url.strip().rstrip('/')
        handle = raw_url.split('/')[-1].split('?')[0]
        
        if not handle or handle.lower() in ['x.com', 'twitter.com', 'home']:
            return posts

        syn_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"
        try:
            res = requests.get(syn_url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                script_tag = soup.find('script', id='__NEXT_DATA__')
                if script_tag and script_tag.string:
                    data = json.loads(script_tag.string)
                    entries = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
                    
                    for entry in entries[:15]:
                        tweet = entry.get('content', {}).get('tweet', {})
                        created_str = tweet.get('created_at')
                        if not created_str:
                            continue
                            
                        dt = datetime.datetime.strptime(created_str, "%a %b %d %H:%M:%S %z %Y")
                        if timezone.is_naive(dt):
                            dt = timezone.make_aware(dt, datetime.timezone.utc)
                            
                        if dt < cutoff_date:
                            continue
                            
                        id_str = tweet.get('id_str')
                        full_text = clean_text(tweet.get('full_text') or tweet.get('text') or '')
                        
                        media_items = tweet.get('entities', {}).get('media', [])
                        image_url = None
                        if media_items:
                            image_url = media_items[0].get('media_url_https')
                            
                        if not image_url and fed.logo:
                            site_url = getattr(settings, 'SITE_URL', 'https://spor24.net').rstrip('/')
                            image_url = f"{site_url}{fed.logo.url}"

                        short_title = full_text.split('\n')[0].strip()[:90]
                        if not short_title:
                            short_title = f"{fed.ad} X Paylaşımı"

                        tweet_url = f"https://x.com/{handle}/status/{id_str}"

                        posts.append({
                            'platform': 'twitter',
                            'post_id': f"x_{id_str}",
                            'title': f"{fed.ad} - {short_title}",
                            'content': full_text,
                            'url': tweet_url,
                            'image_url': image_url,
                            'paylasim_tarihi': dt,
                            'gonderi_tipi': 'post'
                        })
        except Exception:
            pass

        return posts

    # =========================================================================
    # INSTAGRAM HARVESTER
    # =========================================================================
    def scrape_instagram(self, fed, cutoff_date):
        posts = []
        try:
            from haberler.services.social_media_scraper import SocialMediaScraperService
            scraper = SocialMediaScraperService()
            raw_posts = scraper.scrape_social_media('instagram', fed, days=2.0)
            if raw_posts:
                for p in raw_posts:
                    p_date = p.get('paylasim_tarihi')
                    if p_date and p_date >= cutoff_date:
                        posts.append(p)
        except Exception as e:
            pass
        return posts
