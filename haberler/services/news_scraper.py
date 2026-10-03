import requests
from bs4 import BeautifulSoup
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
from urllib.parse import urljoin, urlparse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import uuid
import os
from PIL import Image
import io

# Import models
from haberler.models import BekleyenHaber

logger = logging.getLogger(__name__)

class NewsScrapingService:
    """
    News scraping service for federation websites
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Disable SSL verification for specific federations that have SSL issues
        self.session.verify = False
        
    def scrape_federation_news(self, federation_website) -> List[Dict]:
        """
        Scrape news from a federation website
        
        Args:
            federation_website: FederasyonWebsite model instance
            
        Returns:
            List of dictionaries containing news data
        """
        try:
            logger.info(f"Scraping news from {federation_website.ad}")
            
            # Get the news page
            response = self.session.get(federation_website.haberler_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news items using the configured selector
            if not federation_website.haber_listesi_selector or not federation_website.haber_listesi_selector.strip():
                logger.warning(f"No news list selector configured for {federation_website.ad}")
                return []
                
            news_items = soup.select(federation_website.haber_listesi_selector)
            
            if not news_items:
                logger.warning(f"No news items found for {federation_website.ad} using selector: {federation_website.haber_listesi_selector}")
                return []
            
            scraped_news = []
            
            # Sadece son 4 saat içindeki haberleri çekmek için zaman sınırı
            time_limit = timezone.now() - timedelta(hours=4)
            logger.info(f"Filtering news after: {time_limit}")
            
            for item in news_items[:10]:  # Limit to 10 latest news
                try:
                    news_data = self._extract_news_data(item, federation_website)
                    if news_data:
                        # GOSBF için özel işlem - tarih kontrolü yapmadan ekle
                        if 'gosbf' in federation_website.ana_url.lower():
                            scraped_news.append(news_data)
                        # Güreş federasyonu için özel işlem - tarih kontrolü yapmadan ekle
                        elif 'tgf.tr' in federation_website.ana_url.lower():
                            scraped_news.append(news_data)
                        # Diğer federasyonlar için tarih kontrolü yap
                        elif news_data['date'] and news_data['date'] >= time_limit:
                            scraped_news.append(news_data)
                        elif not news_data['date']:
                            logger.info(f"Skipping news without date: {news_data['title']}")
                        else:
                            logger.info(f"Skipping old news: {news_data['title']} from {news_data['date']}")
                except Exception as e:
                    logger.error(f"Error extracting news item: {e}")
                    continue
                    
            logger.info(f"Successfully scraped {len(scraped_news)} news items from {federation_website.ad}")
            return scraped_news
            
        except requests.RequestException as e:
            logger.error(f"Request error for {federation_website.ad}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping {federation_website.ad}: {e}")
            return []
    
    def _extract_news_data(self, item, federation_website) -> Optional[Dict]:
        """
        Extract news data from a single news item element
        """
        try:
            # Check for empty selectors
            if not federation_website.haber_baslik_selector or not federation_website.haber_baslik_selector.strip():
                return None
            if not federation_website.haber_link_selector or not federation_website.haber_link_selector.strip():
                return None

            # Extract title
            title_element = item.select_one(federation_website.haber_baslik_selector)
            if not title_element:
                return None
            title = title_element.get_text(strip=True)
            
            # Extract link
            link_element = item.select_one(federation_website.haber_link_selector)
            if not link_element:
                return None
                
            # Get href attribute
            href = link_element.get('href')
            if not href:
                return None
                
            # Make absolute URL
            full_url = urljoin(federation_website.ana_url, href)
            
            # Kickboks için özel filtreleme
            if 'kickboks' in federation_website.ad.lower():
                # Gereksiz URL'leri filtrele
                skip_url_patterns = [
                    'sayfa/', 'page/', 'javascript:', 'facebook.com', 
                    'twitter.com', 'instagram.com', 'youtube.com', '#', 'mailto:'
                ]
                
                if any(pattern in full_url for pattern in skip_url_patterns):
                    return None
                
                # Gereksiz başlıkları filtrele
                skip_titles = [
                    'ANASAYFA', 'KURUMSAL', 'FEDERASYON BAŞKANI', 'FEDERASYON PERSONELİ',
                    'İL TEMSİLCİLERİ', 'TARİHÇE', 'HAKKIMIZDA', 'VİZYONUMUZ', 'MİSYONUMUZ',
                    'İLETİŞİM', 'HABERLER', 'DUYURULAR', 'GALERİ', 'LİNKLER', 'BAĞLANTILAR'
                ]
                
                if title.upper().strip() in skip_titles or len(title.strip()) < 5:
                    return None
                
                # Sadece gerçek haber içeriklerini al (daha esnek)
                valid_keywords = [
                    'şampiyon', 'turnuva', 'müsabaka', 'antrenör', 'kurs', 'eğitim',
                    'başkan', 'ziyaret', 'seçil', 'duyuru', 'önemli', 'federasyon',
                    'wako', 'uluslararası', 'milli', 'takım', 'sporcu', 'kick', 'boks',
                    'kamuoyu', 'temmuz', 'nisan', 'mart', 'izmir', 'ankara', 'türkiye'
                ]
                
                # En az 10 karakter olmalı ve geçerli kelime içermeli
                if len(title.strip()) < 10 and not any(keyword in title.lower() for keyword in valid_keywords):
                    return None
            
            # Extract summary if selector is provided
            summary = ""
            if federation_website.haber_ozet_selector:
                summary_element = item.select_one(federation_website.haber_ozet_selector)
                if summary_element:
                    summary = summary_element.get_text(strip=True)
            
            # Extract date if selector is provided
            news_date = None
            if federation_website.haber_tarih_selector:
                date_element = item.select_one(federation_website.haber_tarih_selector)
                if date_element:
                    date_text = date_element.get_text(strip=True)
                    news_date = self._parse_date(date_text)
            
            return {
                'title': title[:200],  # Limit title length
                'url': full_url,
                'summary': summary[:500] if summary else title[:500],  # Use title as summary if no summary
                'date': news_date,
                'federation_website': federation_website
            }
            
        except Exception as e:
            logger.error(f"Error extracting news data: {e}")
            return None
    
    def get_news_content(self, url: str) -> str:
        """
        Get full content of a news article with improved extraction
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try specific selectors for Turkish Karate Federation website first
            content_selectors = [
                '.page-content',           # Primary content container
                '.haber-detay-box',        # News detail box
                '.post-content',
                '.entry-content',
                '.article-content',
                '.news-content',
                'article',
                'main',
                '#content'
            ]
            
            content_element = None
            
            # Try to find the main content element
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # Use the first element with substantial content
                    for elem in elements:
                        text_content = elem.get_text(strip=True)
                        if len(text_content) > 150:  # Increased threshold to 150 characters
                            content_element = elem
                            break
                    # If no element with substantial content, use the first one
                    if not content_element and elements:
                        content_element = elements[0]
                    break
            
            # If no specific content element found, try to find content by identifying the main article area
            if not content_element:
                # Look for elements with class names that suggest they contain content
                content_candidates = soup.find_all(class_=re.compile(r'content|article|post|news|haber', re.I))
                for candidate in content_candidates:
                    text_content = candidate.get_text(strip=True)
                    if len(text_content) > 200:  # Higher threshold for content
                        content_element = candidate
                        break
            
            # If still no content element found, work with body but be more careful
            if not content_element:
                content_element = soup.find('body')
            
            if content_element:
                # More targeted removal of unwanted elements - only remove clear navigation/sidebar elements
                unwanted_selectors = [
                    'nav', 'header', 'footer', 'aside',
                    '.navigation', '.menu', '.sidebar', 
                    '.header', '.footer', '#menu', '#navigation', 
                    '#sidebar', '#header', '#footer', 
                    '.social-media', '.breadcrumb', '.pagination', 
                    '.comments', '.advertisement', '.ads', '.widget',
                    '.share-buttons', '.tags', '.category', '.author-box',
                    '.post-meta', '.entry-meta', '.logo', '.branding',
                    '.site-header', '.site-footer', '.main-navigation',
                    '.hizli-menu', '.footer',  # Specific to karate.gov.tr
                    '.bilgi-bankasi', '.baglantilar', '.banka-hesap',
                    '.duyurular', '.etkinlikler'
                ]
                
                for selector in unwanted_selectors:
                    for element in content_element.select(selector):
                        element.decompose()
                
                # Extract text content
                content = content_element.get_text(separator='\n', strip=True)
            else:
                # Fallback: get text from the whole page
                content = soup.get_text(separator='\n', strip=True)
            
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
            
            # Limit content length but with a more reasonable limit
            content = content[:15000]  # Increased to 15000 characters
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Error getting content from {url}: {e}")
            return ""
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse date from Turkish text
        """
        try:
            # Turkish month names
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            date_text = date_text.lower().strip()
            
            # Try different date patterns
            patterns = [
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 ocak 2024
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 15.01.2024
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 15/01/2024
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    if len(match.groups()) == 3:
                        if pattern == patterns[0]:  # Turkish month name
                            day, month_name, year = match.groups()
                            month = turkish_months.get(month_name)
                            if month:
                                return datetime(int(year), month, int(day))
                        else:
                            # Numeric date formats
                            if pattern == patterns[3]:  # YYYY-MM-DD
                                year, month, day = match.groups()
                            else:  # DD.MM.YYYY or DD/MM/YYYY
                                day, month, year = match.groups()
                            return datetime(int(year), int(month), int(day))
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_text}': {e}")
            return None
    
    def get_news_images(self, url: str) -> List[str]:
        """
        Extract image URLs from a news article with enhanced detection
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Enhanced selectors for news images - more comprehensive
            image_selectors = [
                # Main content images
                'article img',
                '.content img',
                '.post-content img',
                '.entry-content img',
                '.article-content img',
                '.news-content img',
                '.haber-content img',
                '.haber-detay img',
                '.haber-resim img',
                'main img',
                
                # Featured/hero images
                '.featured-image img',
                '.hero-image img',
                '.post-thumbnail img',
                '.thumbnail img',
                '.article-image img',
                '.news-image img',
                
                # Gallery and media
                '.gallery img',
                '.media img',
                '.photo img',
                '.image img',
                
                # Common CMS patterns
                '.wp-post-image',
                '.attachment-full',
                '.size-full',
                
                # Turkish news site patterns
                '.haber-foto img',
                '.haber-gorsel img',
                '.detay-resim img',
                '.icerik-resim img',
                
                # Generic high-quality image selectors
                'img[src*="upload"]',
                'img[src*="image"]',
                'img[src*="photo"]',
                'img[src*="picture"]',
                'img[src*="media"]',
                'img[src*="gallery"]',
                'img[src*="haber"]',
                'img[src*="news"]',
                
                # Data attributes for lazy loading
                'img[data-src]',
                'img[data-lazy-src]',
                'img[data-original]',
            ]
            
            image_urls = set()
            
            # Try each selector
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    # Get image source from various attributes
                    src = (img.get('src') or 
                          img.get('data-src') or 
                          img.get('data-lazy-src') or
                          img.get('data-original') or
                          img.get('data-srcset', '').split(',')[0].split(' ')[0])
                    
                    if src:
                        # Make absolute URL
                        full_url = urljoin(url, src)
                        # Enhanced validation
                        if self._is_valid_news_image_enhanced(img, src, full_url):
                            image_urls.add(full_url)
            
            # If no images found in content, try meta tags and headers
            if not image_urls:
                # Open Graph image
                meta_image = soup.find('meta', property='og:image')
                if meta_image and meta_image.get('content'):
                    image_urls.add(urljoin(url, meta_image['content']))
                
                # Twitter card image
                twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
                if twitter_image and twitter_image.get('content'):
                    image_urls.add(urljoin(url, twitter_image['content']))
                
                # Article schema image
                schema_images = soup.find_all('meta', attrs={'itemprop': 'image'})
                for schema_img in schema_images:
                    if schema_img.get('content'):
                        image_urls.add(urljoin(url, schema_img['content']))
            
            # Sort images by likely quality (larger images first)
            sorted_images = self._sort_images_by_quality(list(image_urls), soup)
            
            return sorted_images[:5]  # Return top 5 images
            
        except Exception as e:
            logger.error(f"Error extracting images from {url}: {e}")
            return []
    
    def _is_valid_news_image_enhanced(self, img_tag, src: str, full_url: str) -> bool:
        """
        Enhanced validation for news images
        """
        # Basic validation first
        if not self._is_valid_news_image(img_tag, src):
            return False
        
        src_lower = src.lower()
        full_url_lower = full_url.lower()
        
        # Additional quality indicators
        quality_indicators = [
            'upload', 'content', 'media', 'images', 'gallery',
            'haber', 'news', 'photo', 'picture', 'img',
            'large', 'big', 'full', 'original', 'high'
        ]
        
        # Boost score for quality indicators
        quality_score = sum(1 for indicator in quality_indicators 
                          if indicator in src_lower or indicator in full_url_lower)
        
        # Skip very low quality or system images
        low_quality_patterns = [
            'favicon', 'logo', 'icon', 'avatar', 'profile',
            'button', 'arrow', 'bg', 'background', 'pattern',
            'spacer', 'pixel', 'transparent', '1x1',
            'placeholder', 'loading', 'spinner'
        ]
        
        for pattern in low_quality_patterns:
            if pattern in src_lower:
                return False
        
        # Check image dimensions from attributes
        width = img_tag.get('width')
        height = img_tag.get('height')
        
        if width and height:
            try:
                w, h = int(width), int(height)
                # Skip very small images
                if w < 200 or h < 150:
                    return False
                # Prefer larger images
                if w >= 400 and h >= 300:
                    quality_score += 2
            except (ValueError, TypeError):
                pass
        
        # Must have at least some quality indicators
        return quality_score >= 1
    
    def _sort_images_by_quality(self, image_urls: List[str], soup) -> List[str]:
        """
        Sort images by estimated quality/relevance
        """
        scored_images = []
        
        for url in image_urls:
            score = 0
            url_lower = url.lower()
            
            # Find the img tag for this URL
            img_tag = None
            for img in soup.find_all('img'):
                img_src = (img.get('src') or 
                          img.get('data-src') or 
                          img.get('data-lazy-src') or
                          img.get('data-original', ''))
                if img_src and urljoin(soup.base or '', img_src) == url:
                    img_tag = img
                    break
            
            # Size indicators in URL
            if any(size in url_lower for size in ['large', 'big', 'full', 'original', 'xl', '1200', '800']):
                score += 10
            if any(size in url_lower for size in ['medium', 'md']):
                score += 5
            if any(size in url_lower for size in ['small', 'thumb', 'sm', '150', '200']):
                score -= 5
            
            # Quality indicators
            if any(qual in url_lower for qual in ['upload', 'content', 'media', 'haber', 'news']):
                score += 8
            if any(qual in url_lower for qual in ['gallery', 'photo', 'picture']):
                score += 6
            
            # Format preference
            if url_lower.endswith(('.jpg', '.jpeg')):
                score += 3
            elif url_lower.endswith('.png'):
                score += 2
            elif url_lower.endswith('.webp'):
                score += 1
            
            # Position in DOM (earlier = more important)
            if img_tag:
                # Images in article/content areas are more important
                parent_classes = ' '.join(img_tag.parent.get('class', []) if img_tag.parent else [])
                if any(cls in parent_classes.lower() for cls in ['content', 'article', 'post', 'haber']):
                    score += 15
                if any(cls in parent_classes.lower() for cls in ['featured', 'hero', 'main']):
                    score += 12
                
                # Alt text indicates importance
                alt_text = img_tag.get('alt', '').lower()
                if alt_text and len(alt_text) > 10:
                    score += 5
            
            scored_images.append((url, score))
        
        # Sort by score (highest first)
        scored_images.sort(key=lambda x: x[1], reverse=True)
        
        return [url for url, score in scored_images]
    
    def _is_valid_news_image(self, img_tag, src: str) -> bool:
        """
        Check if an image is likely a news article image
        """
        # Skip very small images
        width = img_tag.get('width')
        height = img_tag.get('height')
        
        if width and height:
            try:
                w, h = int(width), int(height)
                if w < 200 or h < 150:
                    return False
            except (ValueError, TypeError):
                pass
        
        # Skip common non-content images
        skip_patterns = [
            'logo', 'icon', 'avatar', 'profile', 'thumbnail',
            'banner', 'baner', 'advertisement', 'social', 'share',
            'pixel', 'tracking', '.gif', 'spacer'
        ]
        
        src_lower = src.lower()
        alt_text = (img_tag.get('alt') or '').lower()
        class_name = (img_tag.get('class') or [''])
        class_str = ' '.join(class_name).lower()
        
        for pattern in skip_patterns:
            if (pattern in src_lower or 
                pattern in alt_text or 
                pattern in class_str):
                return False
        
        # Must be a reasonable image format
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        return any(ext in src_lower for ext in valid_extensions)
    
    def download_and_process_image(self, image_url: str, news_title: str) -> Optional[ContentFile]:
        """
        Download and process an image for news article.
        Delegates to download_and_process_image_fit to guarantee 16:9 aspect ratio
        with ambient blur framing for portrait/vertical photos so heads are never cut off.
        """
        return self.download_and_process_image_fit(image_url, news_title)

    def download_and_process_image_fit(self, image_url: str, news_title: str, target_size=(1200, 675)) -> Optional[ContentFile]:
        """
        Download, process, and fit (crop/resize) an image to the exact aspect ratio/size without distortion.
        """
        try:
            response = self.session.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
            
            image_content = response.content
            
            try:
                from PIL import Image, ImageOps, ImageFilter, ImageEnhance
                image = Image.open(io.BytesIO(image_content))
                
                if image.mode in ('RGBA', 'P'):
                    image = image.convert('RGB')
                
                # World-standard sports image framing (16:9 target_size = 1200x675)
                target_w, target_h = target_size

                if image.height > image.width * 1.05:
                    # Vertical/portrait or square-leaning image (9:16, 3:4, 1:1, etc.)
                    # Create ambient 16:9 frame with blurred backdrop so athlete head/body is NEVER cut off!
                    bg = ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS)
                    bg = bg.filter(ImageFilter.GaussianBlur(radius=28))
                    bg = ImageEnhance.Brightness(bg).enhance(0.68)

                    # Scale portrait image to fit container height
                    scale = target_h / image.height
                    fg_w = int(image.width * scale)
                    fg_h = target_h
                    fg_resized = image.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

                    # Center foreground on blurred background
                    offset_x = (target_w - fg_w) // 2
                    bg.paste(fg_resized, (offset_x, 0))
                    fitted_image = bg
                else:
                    # Landscape image:
                    # Anchor crop at top 15% (centering=(0.5, 0.15)) so athlete heads and faces are NEVER cropped!
                    fitted_image = ImageOps.fit(image, target_size, centering=(0.5, 0.15), method=Image.Resampling.LANCZOS)
                
                # Apply official SPOR24.net watermark (at 60% opacity)
                try:
                    from .watermark import apply_spor24_watermark
                    fitted_image = apply_spor24_watermark(fitted_image)
                except Exception as wm_err:
                    logger.warning(f"Watermark apply failed: {wm_err}")

                # Save processed image
                output = io.BytesIO()
                fitted_image.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                file_extension = '.jpg'
                safe_title = slugify(news_title)[:30]
                unique_id = str(uuid.uuid4())[:8]
                filename = f"news_fit_{safe_title}_{unique_id}{file_extension}"
                
                return ContentFile(output.read(), name=filename)
                
            except Exception as img_error:
                logger.error(f"Error processing image fit: {img_error}")
                return None
            
        except Exception as e:
            logger.error(f"Error downloading image from {image_url}: {e}")
            return None

class NewsImportService:
    """
    Service to import scraped news into the database
    """
    
    def __init__(self):
        self.scraping_service = NewsScrapingService()
        # Initialize JS scraping service for JavaScript-protected sites
        try:
            from haberler.services.js_news_scraper import JSNewsScrapingService
            self.js_scraping_service = JSNewsScrapingService()
        except ImportError:
            self.js_scraping_service = None
            logger.warning("JSNewsScrapingService not available. JavaScript-protected sites will not be scraped.")
        
    def import_federation_news(self, federation_website, kategori=None):
        """
        Import news from a federation website
        """
        try:
            # Check if this is a JavaScript-protected site that needs special handling
            js_protected_sites = ['judo.org.tr', 'kravmagafederasyonu.org.tr']
            use_js_scraper = any(site in federation_website.haberler_url for site in js_protected_sites) and self.js_scraping_service
            
            if use_js_scraper:
                logger.info(f"Using JavaScript scraping service for {federation_website.ad}")
                news_items = self.js_scraping_service.scrape_federation_news(federation_website)
            else:
                logger.info(f"Using standard scraping service for {federation_website.ad}")
                news_items = self.scraping_service.scrape_federation_news(federation_website)
            
            if not news_items:
                logger.warning(f"No news items found for {federation_website.ad}")
                return 0  # Return 0 imported items
            
            # Filter news by time (only import news from the last 4 hours for automatic scraping)
            time_threshold = timezone.now() - timedelta(hours=4)
            filtered_news = []
            
            for item in news_items:
                # Only filter by date for automatic scraping, not manual
                if hasattr(self, 'is_manual') and self.is_manual:
                    # For manual scraping, include all news
                    filtered_news.append(item)
                else:
                    # For automatic scraping, only include recent news
                    if item.get('date'):
                        # Ensure both datetimes are timezone-aware for comparison
                        news_date = item['date']
                        if news_date.tzinfo is None:
                            # Make timezone-naive datetime timezone-aware
                            news_date = timezone.make_aware(news_date)
                        
                        # Compare with timezone-aware threshold
                        if news_date > time_threshold:
                            filtered_news.append(item)
                    elif not item.get('date'):
                        # If no date, include it (might be a new item)
                        filtered_news.append(item)
            
            logger.info(f"Found {len(filtered_news)} news items for {federation_website.ad} after filtering")
            
            # Save news items to database
            saved_count = 0
            for item in filtered_news:
                try:
                    # Check if news already exists
                    if BekleyenHaber.objects.filter(kaynak_url=item['url']).exists():
                        logger.info(f"Skipping existing news: {item['title']}")
                        continue
                    
                    # Create pending news entry
                    bekleyen_haber = BekleyenHaber.objects.create(
                        baslik=item['title'],
                        ozet=item['summary'],
                        icerik=item['summary'],  # Will be updated with full content later
                        kaynak_url=item['url'],
                        federasyon_website=federation_website,
                        olusturma_tarihi=item.get('date') or timezone.now()
                    )
                    
                    saved_count += 1
                    logger.info(f"Saved pending news: {item['title']}")
                    
                except Exception as e:
                    logger.error(f"Error saving news '{item['title']}': {e}")
                    continue
            
            logger.info(f"Successfully saved {saved_count} news items from {federation_website.ad}")
            return saved_count  # Return the count of imported items
            
        except Exception as e:
            logger.error(f"Error importing news from {federation_website.ad}: {e}")
            return 0  # Return 0 imported items on error

    def create_kickboks_default_image(self, haber):
        """Create default kickboks image for news"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Image dimensions
            width, height = 800, 400
            
            # Kickboks theme colors
            bg_color = (142, 68, 173)  # Purple
            text_color = (255, 255, 255)  # White
            accent_color = (255, 215, 0)  # Gold
            
            # Create image
            img = Image.new('RGB', (width, height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Gradient effect
            for y in range(height):
                alpha = y / height
                color = tuple(int(bg_color[i] * (1 - alpha * 0.3)) for i in range(3))
                draw.line([(0, y), (width, y)], fill=color)
            
            # Load fonts
            try:
                font_large = ImageFont.truetype("arial.ttf", 36)
                font_medium = ImageFont.truetype("arial.ttf", 28)
                font_small = ImageFont.truetype("arial.ttf", 20)
            except:
                try:
                    font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
                    font_medium = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
                    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
                except:
                    font_large = ImageFont.load_default()
                    font_medium = ImageFont.load_default()
                    font_small = ImageFont.load_default()
            
            # "KICKBOKS" text
            kickboks_text = "KICKBOKS"
            bbox = draw.textbbox((0, 0), kickboks_text, font=font_large)
            kickboks_width = bbox[2] - bbox[0]
            kickboks_x = (width - kickboks_width) // 2
            draw.text((kickboks_x, 40), kickboks_text, fill=accent_color, font=font_large)
            
            # Title text (multi-line)
            title = haber.baslik
            if len(title) > 60:
                title = title[:60] + "..."
            
            # Split title into lines
            words = title.split()
            lines = []
            current_line = []
            max_width = width - 80  # Margins
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font_medium)
                if bbox[2] - bbox[0] <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw lines (max 3 lines)
            y_offset = 120
            for line in lines[:3]:
                bbox = draw.textbbox((0, 0), line, font=font_medium)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                draw.text((x, y_offset), line, fill=text_color, font=font_medium)
                y_offset += 35
            
            # Federation text at bottom
            federation_text = "Türkiye Kickboks Federasyonu"
            bbox = draw.textbbox((0, 0), federation_text, font=font_small)
            fed_width = bbox[2] - bbox[0]
            fed_x = (width - fed_width) // 2
            draw.text((fed_x, height - 60), federation_text, fill=text_color, font=font_small)
            
            # Decorative elements
            square_size = 15
            draw.rectangle([20, 20, 20 + square_size, 20 + square_size], fill=accent_color)
            draw.rectangle([width - 35, 20, width - 20, 20 + square_size], fill=accent_color)
            draw.rectangle([20, height - 35, 20 + square_size, height - 20], fill=accent_color)
            draw.rectangle([width - 35, height - 35, width - 20, height - 20], fill=accent_color)
            
            # Decorative line
            line_y = height - 100
            draw.line([(width//4, line_y), (3*width//4, line_y)], fill=accent_color, width=2)
            
            # Save image
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=90)
            
            filename = f"kickboks_default_{haber.id}.jpg"
            haber.resim.save(
                filename,
                ContentFile(output.getvalue()),
                save=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating default kickboks image: {e}")
            return False
    
    def create_boks_default_image(self, haber):
        """Create default boks image for news"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Image dimensions
            width, height = 800, 400
            
            # Boks theme colors
            bg_color = (220, 53, 69)  # Red
            text_color = (255, 255, 255)  # White
            accent_color = (255, 215, 0)  # Gold
            
            # Create image
            img = Image.new('RGB', (width, height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Gradient effect
            for y in range(height):
                alpha = y / height
                color = tuple(int(bg_color[i] * (1 - alpha * 0.3)) for i in range(3))
                draw.line([(0, y), (width, y)], fill=color)
            
            # Load fonts
            try:
                font_large = ImageFont.truetype("arial.ttf", 36)
                font_medium = ImageFont.truetype("arial.ttf", 28)
                font_small = ImageFont.truetype("arial.ttf", 20)
            except:
                try:
                    font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
                    font_medium = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
                    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
                except:
                    font_large = ImageFont.load_default()
                    font_medium = ImageFont.load_default()
                    font_small = ImageFont.load_default()
            
            # "BOKS" text
            boks_text = "BOKS"
            bbox = draw.textbbox((0, 0), boks_text, font=font_large)
            boks_width = bbox[2] - bbox[0]
            boks_x = (width - boks_width) // 2
            draw.text((boks_x, 40), boks_text, fill=accent_color, font=font_large)
            
            # Title text (multi-line)
            title = haber.baslik
            if len(title) > 60:
                title = title[:60] + "..."
            
            # Split title into lines
            words = title.split()
            lines = []
            current_line = []
            max_width = width - 80  # Margins
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font_medium)
                if bbox[2] - bbox[0] <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw lines (max 3 lines)
            y_offset = 120
            for line in lines[:3]:
                bbox = draw.textbbox((0, 0), line, font=font_medium)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                draw.text((x, y_offset), line, fill=text_color, font=font_medium)
                y_offset += 35
            
            # Federation text at bottom
            federation_text = "Türkiye Boks Federasyonu"
            bbox = draw.textbbox((0, 0), federation_text, font=font_small)
            fed_width = bbox[2] - bbox[0]
            fed_x = (width - fed_width) // 2
            draw.text((fed_x, height - 60), federation_text, fill=text_color, font=font_small)
            
            # Decorative elements
            square_size = 15
            draw.rectangle([20, 20, 20 + square_size, 20 + square_size], fill=accent_color)
            draw.rectangle([width - 35, 20, width - 20, 20 + square_size], fill=accent_color)
            draw.rectangle([20, height - 35, 20 + square_size, height - 20], fill=accent_color)
            draw.rectangle([width - 35, height - 35, width - 20, height - 20], fill=accent_color)
            
            # Decorative line
            line_y = height - 100
            draw.line([(width//4, line_y), (3*width//4, line_y)], fill=accent_color, width=2)
            
            # Boxing gloves (simple)
            glove_x, glove_y = 50, height // 2 - 30
            draw.ellipse([glove_x, glove_y, glove_x + 40, glove_y + 60], fill=accent_color)
            draw.ellipse([glove_x + 5, glove_y + 5, glove_x + 35, glove_y + 55], fill=bg_color)
            
            # Right side glove
            glove_x2 = width - 90
            draw.ellipse([glove_x2, glove_y, glove_x2 + 40, glove_y + 60], fill=accent_color)
            draw.ellipse([glove_x2 + 5, glove_y + 5, glove_x2 + 35, glove_y + 55], fill=bg_color)
            
            # Save image
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=90)
            
            filename = f"boks_default_{haber.id}.jpg"
            haber.resim.save(
                filename,
                ContentFile(output.getvalue()),
                save=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating default boks image: {e}")
            return False