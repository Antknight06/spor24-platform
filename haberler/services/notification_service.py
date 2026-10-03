import os
import requests
import logging
import json
from urllib.parse import quote, urlparse
from django.conf import settings
from haberler.models import BekleyenHaber

logger = logging.getLogger(__name__)

class TelegramNotificationService:
    _invalid_tokens = set()

    def _extract_token(self, url):
        try:
            if '/bot' in url:
                return url.split('/bot')[1].split('/')[0]
        except Exception:
            pass
        return None

    def _make_request(self, url, payload=None, files=None, is_json=True):
        import time
        token = self._extract_token(url)
        if token and token in self._invalid_tokens:
            return False

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if files:
                    response = requests.post(url, data=payload, files=files, timeout=10)
                elif is_json:
                    response = requests.post(url, json=payload, timeout=10)
                else:
                    response = requests.post(url, data=payload, timeout=10)
                
                # Check for 401 Unauthorized (invalid/expired bot token)
                if response.status_code == 401:
                    logger.warning(f"Telegram API 401 Unauthorized: Bot token is invalid or expired. Skipping all future retries.")
                    if token:
                        self._invalid_tokens.add(token)
                    return False

                # Check for 429 Rate Limit
                if response.status_code == 429:
                    retry_after = response.json().get('parameters', {}).get('retry_after', 5)
                    logger.warning(f"Telegram API 429 (Rate Limit). Attempt {attempt+1}/{max_retries}. Sleeping {retry_after}s before retry...")
                    time.sleep(retry_after + 1)
                    continue
                
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Telegram API request failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
        return False


    def send_message(self, token, chat_id, text, reply_markup=None):
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
            
        return self._make_request(url, payload=payload, is_json=True)

    def send_video(self, token, chat_id, video_url, caption, reply_markup=None):
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendVideo"
        payload = {
            "chat_id": chat_id,
            "video": video_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        return self._make_request(url, payload=payload, is_json=True)

    def send_photo(self, token, chat_id, photo_url, caption, reply_markup=None):
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        
        is_local = False
        local_path = None
        
        # 1. Check if photo_url is a local path or local URL
        if photo_url:
            if not photo_url.startswith(('http://', 'https://')):
                is_local = True
                local_path = photo_url
            else:
                parsed_url = urlparse(photo_url)
                netloc = parsed_url.netloc.lower()
                
                # Check if host is local
                is_local_host = any(x in netloc for x in ['localhost', '127.0.0.1', '192.168.', '10.'])
                site_url = getattr(settings, 'SITE_URL', '')
                parsed_site = urlparse(site_url)
                if parsed_site.netloc and parsed_site.netloc.lower() in netloc:
                    is_local_host = True
                    
                if is_local_host and '/media/' in parsed_url.path:
                    media_url_path = getattr(settings, 'MEDIA_URL', '/media/')
                    if parsed_url.path.startswith(media_url_path):
                        relative_path = parsed_url.path[len(media_url_path):]
                    else:
                        idx = parsed_url.path.find('/media/')
                        relative_path = parsed_url.path[idx + len('/media/'):]
                    
                    local_path = os.path.join(settings.MEDIA_ROOT, relative_path.replace('/', os.sep))
                    if os.path.exists(local_path):
                        is_local = True
                        
        # 2. If it is local, upload it as a file (multipart/form-data)
        if is_local and local_path:
            try:
                logger.info(f"Uploading local photo file to Telegram: {local_path}")
                payload = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                if reply_markup:
                    payload["reply_markup"] = json.dumps(reply_markup)
                
                with open(local_path, 'rb') as f:
                    files = {'photo': f}
                    return self._make_request(url, payload=payload, files=files)
            except Exception as e:
                logger.error(f"Error sending local photo file to Telegram: {e}")
        
        # 3. Otherwise, try sending it as a URL
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
            
        success = self._make_request(url, payload=payload, is_json=True)
        if success:
            return True
            
        # 4. Fallback: Download the remote photo and send it as a file upload
        if photo_url and photo_url.startswith(('http://', 'https://')) and token not in self._invalid_tokens:
            try:
                logger.info(f"Telegram photo URL failed. Downloading and uploading remote photo fallback: {photo_url}")
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                img_response = requests.get(photo_url, headers=headers, timeout=10, verify=False)
                img_response.raise_for_status()
                
                from io import BytesIO
                photo_file = BytesIO(img_response.content)
                photo_file.name = "photo.jpg"
                
                post_payload = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                if reply_markup:
                    post_payload["reply_markup"] = json.dumps(reply_markup)
                    
                files = {'photo': photo_file}
                return self._make_request(url, payload=post_payload, files=files)
            except Exception as fallback_err:
                logger.error(f"Fallback download/upload failed for {photo_url}: {fallback_err}")
        
        return False

    def send_video(self, token, chat_id, video_url, caption, reply_markup=None):
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendVideo"
        
        # Clean bytestart/byteend from video URL if it is from Instagram/Facebook CDN
        if video_url and video_url.startswith(('http://', 'https://')):
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(video_url)
            if 'fbcdn.net' in parsed.netloc or 'cdninstagram.com' in parsed.netloc:
                query_params = parse_qs(parsed.query)
                if 'bytestart' in query_params or 'byteend' in query_params:
                    query_params.pop('bytestart', None)
                    query_params.pop('byteend', None)
                    new_query = urlencode(query_params, doseq=True)
                    video_url = urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        new_query,
                        parsed.fragment
                    ))
                    logger.info(f"Cleaned Instagram video URL by removing chunking params: {video_url[:80]}...")
        
        is_local = False
        local_path = None
        
        # 1. Check if video_url is a local path or local URL
        if video_url:
            if not video_url.startswith(('http://', 'https://')):
                is_local = True
                local_path = video_url
            else:
                parsed_url = urlparse(video_url)
                netloc = parsed_url.netloc.lower()
                
                # Check if host is local
                is_local_host = any(x in netloc for x in ['localhost', '127.0.0.1', '192.168.', '10.'])
                site_url = getattr(settings, 'SITE_URL', '')
                parsed_site = urlparse(site_url)
                if parsed_site.netloc and parsed_site.netloc.lower() in netloc:
                    is_local_host = True
                    
                if is_local_host and '/media/' in parsed_url.path:
                    media_url_path = getattr(settings, 'MEDIA_URL', '/media/')
                    if parsed_url.path.startswith(media_url_path):
                        relative_path = parsed_url.path[len(media_url_path):]
                    else:
                        idx = parsed_url.path.find('/media/')
                        relative_path = parsed_url.path[idx + len('/media/'):]
                    
                    local_path = os.path.join(settings.MEDIA_ROOT, relative_path.replace('/', os.sep))
                    if os.path.exists(local_path):
                        is_local = True
                        
        # 2. If it is local, upload it as a file (multipart/form-data)
        if is_local and local_path:
            try:
                logger.info(f"Uploading local video file to Telegram: {local_path}")
                payload = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                if reply_markup:
                    payload["reply_markup"] = json.dumps(reply_markup)
                
                with open(local_path, 'rb') as f:
                    files = {'video': f}
                    return self._make_request(url, payload=payload, files=files)
            except Exception as e:
                logger.error(f"Error sending local video file to Telegram: {e}")
        
        # 3. Otherwise, try sending it as a URL
        payload = {
            "chat_id": chat_id,
            "video": video_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
            
        success = self._make_request(url, payload=payload, is_json=True)
        if success:
            return True
            
        # 4. Fallback: Download the remote video and send it as a file upload
        if video_url and video_url.startswith(('http://', 'https://')) and token not in self._invalid_tokens:
            try:
                logger.info(f"Telegram video URL failed. Checking size before download for: {video_url[:80]}...")
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                
                # Check video size first to avoid downloading/uploading huge files
                with requests.get(video_url, headers=headers, stream=True, timeout=15, verify=False) as head_r:
                    head_r.raise_for_status()
                    content_length = head_r.headers.get('Content-Length')
                    if content_length:
                        size_mb = int(content_length) / (1024 * 1024)
                        logger.info(f"Remote video size: {size_mb:.2f} MB")
                        if int(content_length) > 50 * 1024 * 1024:
                            logger.warning(f"Video size ({size_mb:.2f} MB) exceeds 50MB limit. Skipping download/upload.")
                            return False
                            
                logger.info(f"Downloading remote video: {video_url[:80]}...")
                vid_response = requests.get(video_url, headers=headers, timeout=40, verify=False)
                vid_response.raise_for_status()
                
                from io import BytesIO
                video_file = BytesIO(vid_response.content)
                video_file.name = "video.mp4"
                
                post_payload = {
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                if reply_markup:
                    post_payload["reply_markup"] = json.dumps(reply_markup)
                    
                files = {'video': video_file}
                return self._make_request(url, payload=post_payload, files=files)
            except Exception as fallback_err:
                logger.error(f"Fallback video download/upload failed for {video_url}: {fallback_err}")
        
    def send_media_group(self, token, chat_id, media_items):
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
        payload = {
            "chat_id": chat_id,
            "media": json.dumps(media_items)
        }
        return self._make_request(url, payload=payload, is_json=True)

class NotificationService:
    def __init__(self):
        self.telegram_service = TelegramNotificationService()
        self.configs = getattr(settings, 'TELEGRAM_CONFIGS', [])

    def send_new_news_notifications(self, new_news_list):
        """
        Sends notifications for newly added pending news items.
        Each news is sent as a separate card with photo (if available) or federation logo fallback.
        """
        if not new_news_list:
            return
            
        for news in new_news_list:
            news_id = news.get('id', '')
            federation = news.get('federation', 'Federasyon')
            title = news.get('title', 'Başlıksız')
            url = news.get('url', '#')
            image_url = news.get('image_url')
            
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
            
            # Fetch federation website for logo fallback
            federation_obj = None
            try:
                pending_news_obj = BekleyenHaber.objects.get(id=news_id)
                federation_obj = pending_news_obj.federasyon_website
            except Exception as get_err:
                logger.debug(f"Could not get BekleyenHaber or FederasyonWebsite for fallback logo: {get_err}")
            
            # Fallback to federation logo if image_url is missing
            if not image_url and federation_obj and federation_obj.logo:
                image_url = f"{site_url}{federation_obj.logo.url}"
                logger.info(f"Using federation logo as fallback for Telegram: {image_url}")
            
            video_url = news.get('video_url')
            is_video = news.get('is_video', False)
            scraper_name = news.get('scraper_name', 'Spor24 Scraper Worker')
            
            # Format the message card with HTML styling
            message_lines = [
                f"📰 <b>{federation}</b>\n",
                f"📌 <b>{title}</b>\n",
                f"🕷️ <i>Haberi Yakalayan: {scraper_name}</i>"
            ]
            message = "\n".join(message_lines)
            
            # Create inline keyboard for links and sharing
            share_title = f"Spor24: {title}"
            telegram_share_text = f"📰 *{title}*\n\n⚡ Spor24.net - Spor Haberleri"
            
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "📰 Kaynağa Git", "url": url},
                        {"text": "Onay Paneli", "url": f"{site_url}/admin/haberler/bekleyenhaber/{news_id}/change/"}
                    ],
                    [
                        {"text": "🟢 Telegram'dan Onayla", "callback_data": f"approve_webnews:{news_id}"}
                    ],
                    [
                        {"text": "🟢 WhatsApp", "url": f"https://api.whatsapp.com/send?text={quote(share_title)}%20{quote(url)}"},
                        {"text": "🐦 X (Twitter)", "url": f"https://twitter.com/intent/tweet?text={quote(share_title)}&url={quote(url)}"}
                    ],
                    [
                        {"text": "👥 Facebook", "url": f"https://www.facebook.com/sharer/sharer.php?u={quote(url)}"},
                        {"text": "✈️ Telegram", "url": f"https://t.me/share/url?url={quote(url)}&text={quote(telegram_share_text)}"}
                    ]
                ]
            }
            
            # Send to all configured channels/bots
            for config in self.configs:
                token = config.get("token")
                chat_id = config.get("chat_id")
                if token and chat_id:
                    success = False
                    
                    # 1. Attempt to send video if is_video is True and video_url exists
                    if is_video and video_url:
                        success = self.telegram_service.send_video(token, chat_id, video_url, message, reply_markup=reply_markup)
                        
                    # 2. Attempt to send photo if image_url exists and video sending was not done or failed
                    if not success and image_url:
                        success = self.telegram_service.send_photo(token, chat_id, image_url, message, reply_markup=reply_markup)
                    
                    # 3. Fallback to plain text message if no media or media sending failed
                    if not success:
                        fallback_message = message + f"\n🔗 <a href='{url}'>Orijinal Kaynak</a>"
                        success = self.telegram_service.send_message(token, chat_id, fallback_message, reply_markup=reply_markup)
                        
                    if success:
                        logger.info(f"Telegram notification sent for news id {news_id} to chat_id {chat_id}")
                    else:
                        logger.warning(f"Failed to send Telegram notification for news id {news_id}")
            
            # Rate limiting sleep between news cards
            import time
            time.sleep(1.2)

    def send_social_media_notifications(self, social_posts_list):
        """
        Sends notifications for newly added pending social media posts.
        Each post is sent as a separate card with photo (if available) or federation logo fallback.
        """
        if not social_posts_list:
            return
            
        from haberler.models import BekleyenSosyalMedyaHaberi
        for post in social_posts_list:
            post_id = post.get('id', '')
            platform = post.get('platform', 'instagram')
            federation = post.get('federation', 'Federasyon')
            title = post.get('title', 'Başlıksız')
            content = post.get('content', '')
            url = post.get('url', '#')
            image_url = post.get('image_url')
            
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
            
            # Fetch federation website for logo fallback
            federation_obj = None
            try:
                pending_post_obj = BekleyenSosyalMedyaHaberi.objects.get(id=post_id)
                federation_obj = pending_post_obj.federasyon_website
            except Exception as get_err:
                logger.debug(f"Could not get BekleyenSosyalMedyaHaberi for fallback logo: {get_err}")

            # Parse MEDIA_URLS from content comment if present
            import re
            media_urls = []
            comment_match = re.search(r'<!--MEDIA_URLS:\[(.*?)\]-->', content)
            if comment_match:
                media_urls = [x.strip() for x in comment_match.group(1).split(',') if x.strip()]
                content = re.sub(r'<!--MEDIA_URLS:\[.*?\]-->', '', content).strip()
            
            # Fallback to federation logo if image_url is missing
            if not image_url and federation_obj and federation_obj.logo:
                image_url = f"{site_url}{federation_obj.logo.url}"
                logger.info(f"Using federation logo as fallback for Telegram: {image_url}")
            
            # Platform badge formatting
            gonderi_tipi = post.get('gonderi_tipi')
            if not gonderi_tipi and pending_post_obj:
                gonderi_tipi = getattr(pending_post_obj, 'gonderi_tipi', 'post')
            else:
                gonderi_tipi = gonderi_tipi or 'post'

            platform_badges = {
                'instagram': '📸 <b>Instagram</b>',
                'twitter': '🐦 <b>X / Twitter</b>',
                'facebook': '👥 <b>Facebook</b>',
                'youtube': '🎥 <b>YouTube</b>',
            }
            platform_badge = platform_badges.get(platform, '📱 <b>Sosyal Medya</b>')
            
            type_suffixes = {
                'post': ' [Fotoğraf 🖼️]',
                'reel': ' [Video/Reel 🎥]',
                'story': ' [Hikaye ⏳]'
            }
            type_suffix = type_suffixes.get(gonderi_tipi, '')
            platform_badge = f"{platform_badge}{type_suffix}"
            
            import html as pyhtml
            import re
            
            pure_title = re.sub(r'<[^>]+>', '', str(title)).strip()
            pure_content = re.sub(r'<[^>]+>', '', str(content)).strip()
            pure_fed = re.sub(r'<[^>]+>', '', str(federation)).strip()
            
            safe_title = pyhtml.escape(pure_title)
            safe_content = pyhtml.escape(pure_content[:260] + ('...' if len(pure_content) > 260 else ''))
            safe_fed = pyhtml.escape(pure_fed)
            
            message_lines = [
                f"{platform_badge} | <b>{safe_fed}</b>\n",
                f"📌 <b>{safe_title}</b>\n",
                f"📝 {safe_content}"
            ]
            message = "\n".join(message_lines)
            
            # Create inline keyboard for links and sharing
            share_title = f"Spor24 Sosyal: {title}"
            telegram_share_text = f"📰 *{title}*\n\n⚡ Spor24.net - Spor Haberleri"
            
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "🔗 Kaynağa Git", "url": url},
                        {"text": "Onay Paneli", "url": f"{site_url}/admin/haberler/bekleyensosyalmedyahaberi/{post_id}/change/"}
                    ],
                    [
                        {"text": "🟢 Telegram'dan Onayla", "callback_data": f"approve_news:{post_id}"}
                    ],
                    [
                        {"text": "🟢 WhatsApp", "url": f"https://api.whatsapp.com/send?text={quote(share_title)}%20{quote(url)}"},
                        {"text": "🐦 X (Twitter)", "url": f"https://twitter.com/intent/tweet?text={quote(share_title)}&url={quote(url)}"}
                    ],
                    [
                        {"text": "👥 Facebook", "url": f"https://www.facebook.com/sharer/sharer.php?u={quote(url)}"},
                        {"text": "✈️ Telegram", "url": f"https://t.me/share/url?url={quote(url)}&text={quote(telegram_share_text)}"}
                    ]
                ]
            }

            # Build media group if multiple items
            has_media_group = len(media_urls) > 1
            media_items = []
            if has_media_group:
                for m_url in media_urls[:10]:
                    is_vid = ".mp4" in m_url.lower() or "video" in m_url.lower()
                    media_items.append({
                        "type": "video" if is_vid else "photo",
                        "media": m_url
                    })
                if media_items:
                    media_items[0]["caption"] = message
                    media_items[0]["parse_mode"] = "HTML"
            
            # Send to all configured channels/bots
            for config in self.configs:
                token = config.get("token")
                chat_id = config.get("chat_id")
                if token and chat_id:
                    success = False
                    
                    # 1. Attempt Media Group if available
                    if has_media_group and media_items:
                        logger.info(f"Sending media group for social post id {post_id} with {len(media_items)} items...")
                        success = self.telegram_service.send_media_group(token, chat_id, media_items)
                        if success:
                            # Send follow-up message with action buttons
                            btn_text = f"👉 <b>{federation}</b> gönderisi için onay/paylaşım butonları:"
                            self.telegram_service.send_message(token, chat_id, btn_text, reply_markup=reply_markup)
                    
                    # 2. Fallback to single photo or video
                    if not success and image_url:
                        if gonderi_tipi == 'reel':
                            success = self.telegram_service.send_video(token, chat_id, image_url, message, reply_markup=reply_markup)
                            if not success:
                                logger.info("Video sending failed/skipped for Reel. Trying photo fallback with federation logo...")
                                logo_url = None
                                if federation_obj and federation_obj.logo:
                                    logo_url = f"{site_url}{federation_obj.logo.url}"
                                if logo_url:
                                    success = self.telegram_service.send_photo(token, chat_id, logo_url, message, reply_markup=reply_markup)
                        else:
                            success = self.telegram_service.send_photo(token, chat_id, image_url, message, reply_markup=reply_markup)
                    
                    # 3. Fallback to plain text message
                    if not success:
                        fallback_message = message + f"\n🔗 <a href='{url}'>Orijinal Kaynak</a>"
                        success = self.telegram_service.send_message(token, chat_id, fallback_message, reply_markup=reply_markup)
                        
                    if success:
                        logger.info(f"Telegram notification sent for social post id {post_id} to chat_id {chat_id}")
                    else:
                        logger.warning(f"Failed to send Telegram notification for social post id {post_id}")
            
            # Rate limiting sleep between social cards
            import time
            time.sleep(1.2)

