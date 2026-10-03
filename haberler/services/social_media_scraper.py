import os
import json
import time
import random
import datetime
import requests
import html
import urllib3
from django.utils import timezone
from django.conf import settings
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SocialMediaScraperService:
    def __init__(self):
        # Configuration mapping: Federation ID to social media handles
        self.federation_handles = {
            'Taekwondo': {
                'instagram': 'turkiyetaekwondofed',
                'twitter': 'tkdfed',
                'facebook': 'turkiyetaekwondofed'
            },
            'Karate': {
                'instagram': 'turkiyekaratefed',
                'twitter': 'karatefed',
                'facebook': 'karatefed'
            },
            'Güreş': {
                'instagram': 'trguresfed',
                'twitter': 'trguresfed',
                'facebook': 'trguresfed'
            },
            'Wushu': {
                'instagram': 'turkiyewushukungfufed',
                'twitter': 'twkf_social',
                'facebook': 'twkf.org'
            },
            'Kickboks': {
                'instagram': 'turkiyekickboksfederasyonu',
                'twitter': 'kickboksfed',
                'facebook': 'kickboks.gov.tr'
            },
            'Muaythai': {
                'instagram': 'turkiyemuaythaifed',
                'twitter': 'muaythaifed',
                'facebook': 'muaythaifed'
            },
            'Judo': {
                'instagram': 'turkiyujudofed',
                'twitter': 'turkiyujudofed',
                'facebook': 'turkiyujudofed'
            }
        }
        
        # Sample realistic post templates for simulation mode
        self.post_templates = {
            'instagram': [
                "Şampiyonlar sahnede! 🥋 {federation} tarafından düzenlenen büyük turnuva tüm hızıyla devam ediyor. Sporcularımızın hırsı göz dolduruyor! #spor #sampiyon #turnuva",
                "Milli Takım seçmelerimiz tamamlandı! 🇹🇷 Kadroya giren tüm sporcularımızı tebrik eder, uluslararası arenada başarılar dileriz. Detaylar hikayemizde! #millitakim #turkiye",
                "Yeni eğitim seminerimiz başlıyor. Antrenör ve hakemlerimiz için düzenlenen gelişim programı kayıtları açılmıştır. Detaylı bilgi profildeki linkte. 📚 #egitim #antrenor",
                "Tebrikler! 🥇 Sporcumuz uluslararası Grand Prix müsabakalarında altın madalya kazanarak bayrağımızı dalgalandırdı! Gururluyuz! #altinmadalya #gurur #basari"
            ],
            'twitter': [
                "Milli Takımımız hazırlık kampını tamamladı! Sporcularımız önümüzdeki hafta başlayacak şampiyona için hazır. Son detaylar web sitemizde. 🥋🇹🇷",
                "Turnuvanın 2. gün sonuçları açıklandı! Dereceye giren kulüplerimizi ve teknik heyetlerimizi tebrik ederiz. Sonuç listesi için tıklayın ⬇️",
                "Federasyon Başkanımız, yeni sezon öncesi kulüp temsilcileriyle bir araya gelerek istişare toplantısını gerçekleştirdi. Hayırlı bir sezon dileriz.",
                "Bugün de madalyalarla dönüyoruz! Müsabakalar sonucunda sporcularımız 1 Gümüş 🥈 ve 2 Bronz 🥉 madalya elde etti. Tebrikler çocuklar!"
            ],
            'facebook': [
                "Büyük heyecan başlıyor! Federasyonumuzun 2026 yılı faaliyet takviminde yer alan Gençler Türkiye Şampiyonası katılım şartları ve kayıt formu yayınlanmıştır. Tüm kulüp ve sporcularımıza başarılar dileriz.",
                "Kulüplerarası Lig müsabakaları teknik toplantısı federasyon merkezimizde gerçekleştirildi. Toplantı kararları ve fikstür detaylarına resmi sitemizden ulaşabilirsiniz. 🤝",
                "Spor Genel Müdürlüğü koordinasyonunda yürütülen gelişim projemizin ilk etabı başarıyla tamamlandı. Emeği geçen tüm antrenörlerimize teşekkür ederiz. 📸",
                "Avrupa Şampiyonası hazırlıkları kapsamında kamp kadromuz açıklanmıştır. Sporcularımızın antrenman görüntüleri ve kamp programı detayları için sayfamızı takip etmeye devam edin."
            ]
        }

    def get_simulated_image_for_federation(self, federation_website):
        """Resolves a branch-specific simulated image path from local stock images"""
        from django.utils.text import slugify
        from django.conf import settings
        
        # Helper to normalize names for accurate matching (Turkish -> English chars)
        def normalize_name(text):
            if not text:
                return ""
            text = text.lower()
            translations = {
                'ı': 'i', 'ö': 'o', 'ü': 'u', 'ş': 's', 'ç': 'c', 'ğ': 'g',
                'â': 'a', 'î': 'i', 'û': 'u'
            }
            for tr_char, en_char in translations.items():
                text = text.replace(tr_char, en_char)
            return text
        
        category_slug = 'genel'
        if federation_website.kategori_set.exists():
            category_slug = federation_website.kategori_set.first().slug
            # Normalization
            if category_slug == 'muay-thai':
                category_slug = 'muaythai'
            elif category_slug in ['atclk', 'aticilik']:
                category_slug = 'aticilik'
            elif category_slug == 'dagclk':
                category_slug = 'dagcilik'
        else:
            category_slug = slugify(federation_website.ad)
            
        media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else os.path.join(settings.BASE_DIR, 'media')
        stock_root = os.path.join(media_root, 'stock_images')
        stock_dir = os.path.join(stock_root, category_slug)
        
        if not os.path.exists(stock_dir):
            # Dynamic match by searching available subdirectories in stock_images
            available_folders = []
            if os.path.exists(stock_root):
                try:
                    available_folders = [f for f in os.listdir(stock_root) if os.path.isdir(os.path.join(stock_root, f))]
                except Exception:
                    pass
            
            fed_ad_normalized = normalize_name(federation_website.ad)
            matched = False
            for folder in available_folders:
                folder_normalized = normalize_name(folder)
                if folder_normalized and folder_normalized in fed_ad_normalized:
                    category_slug = folder
                    stock_dir = os.path.join(stock_root, category_slug)
                    matched = True
                    break
            
            if not matched:
                # If still not matched, try fallback by hardcoded keywords
                for fallback_slug in ['boks', 'gures', 'judo', 'karate', 'taekwondo', 'kickboks', 'atletizm', 'yuzme']:
                    if fallback_slug in fed_ad_normalized:
                        category_slug = fallback_slug
                        stock_dir = os.path.join(stock_root, category_slug)
                        matched = True
                        break
                        
            if not matched:
                category_slug = 'genel'  # fallback to general sport folder
        
        image_num = random.randint(1, 10)
        return f"/media/stock_images/{category_slug}/{image_num}.jpg"


    def get_handles_for_federation(self, federation_website):
        handles = {'instagram': '', 'twitter': '', 'facebook': ''}
        import re
        
        # 1. Direct fields from FederasyonWebsite
        if federation_website.instagram_url:
            m = re.search(r'instagram\.com/([a-zA-Z0-9_\.]+)', federation_website.instagram_url)
            if m:
                handles['instagram'] = m.group(1).strip('/')
        if federation_website.x_url:
            m = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', federation_website.x_url)
            if m:
                handles['twitter'] = m.group(1).strip('/')
        if federation_website.facebook_url:
            m = re.search(r'facebook\.com/([a-zA-Z0-9_\.]+)', federation_website.facebook_url)
            if m:
                handles['facebook'] = m.group(1).strip('/')
                
        # 2. Check FederasyonSosyalMedya model
        try:
            sosyal = federation_website.sosyal_medya
            if not handles['instagram'] and sosyal.instagram_kullanici_adi:
                handles['instagram'] = sosyal.instagram_kullanici_adi
            if not handles['twitter'] and sosyal.x_sayfasi:
                handles['twitter'] = sosyal.x_sayfasi
            if not handles['facebook'] and sosyal.facebook_sayfasi:
                handles['facebook'] = sosyal.facebook_sayfasi
        except Exception:
            pass

        # 3. Fallback to dictionary
        if not handles['instagram'] or not handles['twitter']:
            fallback = self._get_legacy_handles(federation_website.ad)
            if not handles['instagram']:
                handles['instagram'] = fallback.get('instagram', '')
            if not handles['twitter']:
                handles['twitter'] = fallback.get('twitter', '')

        return handles

    def _get_legacy_handles(self, fed_name):
        for key, val in self.federation_handles.items():
            if key.lower() in fed_name.lower():
                return val
        return {
            'instagram': fed_name.lower().replace(' ', ''),
            'twitter': fed_name.lower().replace(' ', ''),
            'facebook': fed_name.lower().replace(' ', '')
        }

    def scrape_social_media(self, platform, federation_website, days=7):
        """
        Attempts active scraping of Instagram posts using Playwright to bypass all bot blocks and list posts.
        Falls back to realistic high-quality posts within the last 48 hours if blocked by Instagram login/429.
        """
        cutoff = timezone.now() - datetime.timedelta(days=days)
        
        if platform == 'instagram':
            handles = self.get_handles_for_federation(federation_website)
            handle = handles.get('instagram')
            if handle:
                try:
                    cookie_file = os.path.join(settings.BASE_DIR, 'instagram_cookies.json')
                    posts = []
                    
                    if os.path.exists(cookie_file):
                        with open(cookie_file, 'r') as f:
                            cookies = json.load(f)
                        
                        with sync_playwright() as p:
                            browser = p.chromium.launch(headless=True)
                            context = browser.new_context(
                                viewport={'width': 1280, 'height': 800},
                                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                            )
                            context.add_cookies(cookies)
                            page = context.new_page()
                        
                        # Intercept network responses to find direct video urls
                        intercepted_videos = {}
                        def handle_response(response):
                            try:
                                url = response.url
                                content_type = response.headers.get('content-type', '')
                                if 'video' in content_type or '.mp4' in url.lower():
                                    intercepted_videos[time.time()] = url
                            except:
                                pass
                                
                        page.on("response", handle_response)
                        
                        # Profil sayfasina git
                        page.goto(f'https://www.instagram.com/{handle}/', wait_until='domcontentloaded')
                        time.sleep(4)
                        
                        # 1. Takip Kontrolu ve Otomatik Takip
                        try:
                            follow_btn = page.locator("button:has-text('Follow'), button:has-text('Takip Et'), button:has-text('Takip et')")
                            if follow_btn.count() > 0 and follow_btn.first.is_visible():
                                print(f"[INFO] {handle} takip edilmiyor. Takip et butonuna tiklaniyor...")
                                follow_btn.first.click()
                                time.sleep(2)
                        except Exception as follow_err:
                            print(f"[DEBUG] Takip etme hatasi: {follow_err}")
                            
                        # 2. Gonderi Kutularini Bul ve Sirayla Tikla
                        post_locators = page.locator('a[href*="/p/"], a[href*="/reel/"]')
                        post_count = min(post_locators.count(), 6) # En son 6 gonderiyi inceleyelim
                        
                        print(f"[INFO] {handle} profilinde {post_locators.count()} gonderi bulundu. En son {post_count} gonderi inceleniyor...")
                        
                        for i in range(post_count):
                            try:
                                # Clear intercepted videos for the next post
                                intercepted_videos.clear()
                                
                                # Elementi bulup tiklayalim
                                post_locators.nth(i).click()
                                time.sleep(3) # Modalın yuklenmesini bekle
                                
                                # Modal DOM'unu parse edelim
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(page.content(), 'html.parser')
                                dialog = soup.find('div', role='dialog')
                                
                                if dialog:
                                    # Tarih
                                    time_tag = dialog.find('time')
                                    if time_tag and time_tag.get('datetime'):
                                        dt_str = time_tag.get('datetime')
                                        post_date = datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                                        
                                        # Zaman siniri kontrolu
                                        if post_date < cutoff:
                                            print(f"   Gönderi ({post_date}) cutoff suresinden ({cutoff}) eski. Dongu sonlandiriliyor.")
                                            page.keyboard.press("Escape")
                                            time.sleep(1)
                                            break
                                            
                                        # Metin (Caption)
                                        caption = ""
                                        h1_tag = dialog.find('h1')
                                        if h1_tag:
                                            caption = h1_tag.get_text().strip()
                                        
                                        first_line = caption.split('\n')[0].strip() if caption else f"{federation_website.ad} Instagram Paylaşımı"
                                        title = first_line[:100] + ("..." if len(first_line) > 100 else "")
                                        

                                        carousel_media = []
                                        is_video = False
                                        
                                        # Carousel loop to gather multiple images/videos
                                        for slide_idx in range(10): # max 10 slides
                                            soup = BeautifulSoup(page.content(), 'html.parser')
                                            dialog = soup.find('div', role='dialog')
                                            if not dialog:
                                                break
                                            
                                            # Extract images
                                            imgs = dialog.find_all('img')
                                            for img in imgs:
                                                src = img.get('src')
                                                alt_text = img.get('alt', '')
                                                if src and src.startswith('http'):
                                                    if 'profile picture' not in alt_text.lower() and handle.lower() not in alt_text.lower():
                                                        if src not in carousel_media:
                                                            carousel_media.append(src)
                                            
                                            # Extract videos
                                            video_tags = dialog.find_all('video')
                                            if video_tags:
                                                is_video = True
                                                for v_tag in video_tags:
                                                    v_src = v_tag.get('src')
                                                    if v_src and v_src.startswith('http') and not v_src.startswith('blob:'):
                                                        if v_src not in carousel_media:
                                                            carousel_media.append(v_src)
                                                            
                                                # Fallback to intercepted video URLs if no direct http URL found on tag
                                                if intercepted_videos:
                                                    sorted_times = sorted(intercepted_videos.keys(), reverse=True)
                                                    for t in sorted_times:
                                                        vid_url = intercepted_videos[t]
                                                        if vid_url not in carousel_media:
                                                            carousel_media.append(vid_url)
                                                            
                                            # Click Next button if exists
                                            try:
                                                next_btn = page.locator("div[role='dialog'] button[aria-label='Next'], div[role='dialog'] button[aria-label='İleri']")
                                                if next_btn.count() > 0 and next_btn.first.is_visible():
                                                    next_btn.first.click()
                                                    time.sleep(1.2) # Wait for slide to load
                                                else:
                                                    break
                                            except Exception:
                                                break
                                                
                                        # The primary image_url is the first media found
                                        image_url = carousel_media[0] if carousel_media else ""
                                        
                                        # Clean blob link fallbacks
                                        if image_url and image_url.startswith('blob:'):
                                            image_url = ""
                                            
                                        # Fallback Logo
                                        if not image_url and federation_website.logo:
                                            site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
                                            image_url = f"{site_url}{federation_website.logo.url}"
                                            
                                        # Append extra media URLs to the content as hidden comment
                                        final_content = caption or title
                                        if len(carousel_media) > 1:
                                            final_content += f"\n<!--MEDIA_URLS:[{','.join(carousel_media)}]-->"
                                            
                                        # URL
                                        current_url = page.url
                                        shortcode = current_url.split('/p/')[-1].split('/')[0] if '/p/' in current_url else current_url.split('/reel/')[-1].split('/')[0]
                                        
                                        posts.append({
                                            'platform': 'instagram',
                                            'federation_id': federation_website.id,
                                            'post_id': f"real_insta_{shortcode}",
                                            'title': title,
                                            'content': final_content,
                                            'url': current_url,
                                            'image_url': image_url,
                                            'paylasim_tarihi': post_date,
                                            'gonderi_tipi': 'reel' if is_video else 'post'
                                        })
                                        print(f"   [EKLEDİ] Shortcode: {shortcode} | Tarih: {post_date}")
                                    else:
                                        print("   [UYARI] Modal icinde zaman etiketi bulunamadi.")
                                        
                                # Modali kapat
                                page.keyboard.press("Escape")
                                time.sleep(1.5)

                            except Exception as post_err:
                                print(f"   [HATA] Gonderi {i} incelenirken hata olustu: {post_err}")
                                # Kapatmayi dene
                                try:
                                    page.keyboard.press("Escape")
                                    time.sleep(1)
                                except:
                                    pass
                                    
                        browser.close()
                    
                    if posts:
                        return posts
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Playwright Instagram scraping failed for {handle}: {e}")

                # Strictly Real Data Only: No fake or simulated content should ever be generated
                return []
                    
        return []

    def generate_simulated_post(self, platform, federation_website, days_ago=0.0):
        """Generates realistic post data for the given federation website and social platform"""
        handles = self.get_handles_for_federation(federation_website)
        handle = handles.get(platform, federation_website.ad.lower().replace(' ', ''))
        
        # Pick template and format it
        templates = self.post_templates.get(platform, self.post_templates['instagram'])
        raw_template = random.choice(templates)
        content = raw_template.format(federation=federation_website.ad)
        
        # Determine gonderi_tipi
        gonderi_tipi = 'post'
        if platform == 'instagram':
            gonderi_tipi = random.choice(['post', 'reel', 'story'])
            
        # Customize simulated post URL depending on type
        if platform == 'instagram' and gonderi_tipi == 'story':
            url_type = "stories/"
        elif platform == 'instagram' and gonderi_tipi == 'reel':
            url_type = "reel/"
        else:
            url_type = "p/"
            
        # Unique post parameters
        paylasim_tarihi = timezone.now() - datetime.timedelta(days=days_ago)
        timestamp = int(paylasim_tarihi.timestamp())
        post_id = f"{platform}_{handle}_{gonderi_tipi}_{timestamp}_{random.randint(100, 999)}"
        
        # Construct post URLs to point to official profiles to prevent 404 / login walls
        platform_base_urls = {
            'instagram': f"https://www.instagram.com/{handle}/",
            'twitter': f"https://x.com/{handle}/",
            'facebook': f"https://www.facebook.com/{handle}/"
        }
        url = platform_base_urls.get(platform, 'https://social.com/')
        
        # Add badge in title for reels/stories
        type_badges = {
            'post': 'Fotoğraf',
            'reel': 'Reel Video',
            'story': 'Hikaye'
        }
        title = f"{federation_website.ad} - {platform.upper()} {type_badges.get(gonderi_tipi, 'Paylaşımı')}"
        image_url = self.get_simulated_image_for_federation(federation_website)
        
        return {
            'platform': platform,
            'federation_id': federation_website.id,
            'post_id': post_id,
            'title': title,
            'content': content,
            'url': url,
            'image_url': image_url,
            'paylasim_tarihi': paylasim_tarihi,
            'gonderi_tipi': gonderi_tipi
        }
