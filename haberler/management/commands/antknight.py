from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite, BekleyenYetkiliHaberi, Kategori, Haber
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.contrib.auth.models import User
from urllib.parse import urljoin
import time
import re
import ftfy
import dateparser
from datetime import timedelta

class Command(BaseCommand):
    help = 'Antknight v2.2: Gelişmiş Haber Toplayıcı (Katı Tarih ve Başlık Kuralları)'

    BLACKLIST_TITLES = [
        'haberler', 'duyurular', 'anasayfa', 'home', 'iletişim', 'hakkımızda', 
        'vizyon', 'misyon', 'faaliyetler', 'galeri', 'video', 'fotoğraf', 
        'başkan', 'kurullar', 'talimatlar', 'statü', 'dokümanlar', 'bağlantılar',
        'sitemap', 'arşiv', 'rss', 'tümü', 'daha fazla', 'devamı', 'siteler',
        'thumb', 'logo', 'header', 'footer'
    ]

    def handle(self, *args, **options):
        self.stdout.write('🛡️  ANTKNIGHT: Haber Devriyesi Başlıyor (v2.2)...')
        self.stdout.write('   Kural 1: Sadece son 24 saat içindeki haberler çekilecek (Kesin).')
        self.stdout.write('   Kural 2: Jenerik veya çöp başlıklar atlanacak.')
        self.stdout.write('   Kural 3: Encoding düzeltilecek.')
        self.stdout.write('=' * 60)
        
        bot_user, _ = User.objects.get_or_create(
            username='antknight',
            defaults={
                'email': 'antknight@spor24.net',
                'first_name': 'Ant',
                'last_name': 'Knight',
                'is_active': True,
                'is_staff': True 
            }
        )
        
        federations = FederasyonWebsite.objects.filter(aktif=True)
        if not federations:
            self.stdout.write(self.style.WARNING('⚠️  Aktif federasyon bulunamadı.'))
            return
            
        total_found = 0
        skipped_old = 0
        skipped_nodate = 0
        skipped_duplicate = 0
        skipped_title = 0
        
        time_threshold = timezone.now() - timedelta(days=1)
        
        for federation in federations:
            self.stdout.write(f'\n🔍 Taranıyor: {federation.ad}')
            
            try:
                kategori = Kategori.objects.filter(federasyon_website=federation).first()
                if not kategori:
                     kategori = Kategori.objects.order_by('id').first()

                news_items = self._scrape_federation_news(federation)
                
                for news_data in news_items:
                    # 1. Encoding Fix
                    title = self._fix_encoding(news_data['title'])
                    
                    # 2. Başlık Filtresi
                    if not title or len(title) < 5:
                        skipped_title += 1
                        continue
                        
                    if title.lower() in self.BLACKLIST_TITLES:
                        skipped_title += 1
                        continue
                        
                    if federation.ad.lower() in title.lower() and len(title) < len(federation.ad) + 5:
                        # Sadece federasyon adı yazıyorsa muhtemelen logo alt textidir
                        skipped_title += 1
                        continue

                    # 3. Tarih Kontrolü (KATI)
                    news_date = news_data.get('date')
                    if not news_date:
                        # Tarih bulunamadı -> Güvenlik gereği eski kabul et ve atla
                        self.stdout.write(f'   ❓ [Tarih Yok] {title[:30]} -> Risk almamak için atlanıyor.')
                        skipped_nodate += 1
                        continue
                        
                    if timezone.is_naive(news_date):
                        news_date = timezone.make_aware(news_date)
                        
                    if news_date < time_threshold:
                        self.stdout.write(f'   ⏳ [Eski] {title[:30]} ({news_date.strftime("%d.%m %H:%M")})')
                        skipped_old += 1
                        continue

                    # 4. Mükerrer Kontrolü (URL ve Başlık ve İçerik URL)
                    if Haber.objects.filter(kaynak_url=news_data['url']).exists() or \
                       BekleyenYetkiliHaberi.objects.filter(baslik=title).exists() or \
                       BekleyenYetkiliHaberi.objects.filter(icerik__icontains=news_data['url']).exists():
                        self.stdout.write(f'   ♻️  [Mükerrer] {title[:30]}...')
                        skipped_duplicate += 1
                        continue

                    # 5. Kaydet
                    # İçerik encoding
                    content = self._fix_encoding(news_data['content']) if news_data.get('content') else ""
                    summary = self._fix_encoding(news_data['summary']) if news_data.get('summary') else title

                    bekleyen = BekleyenYetkiliHaberi(
                        baslik=title,
                        ozet=summary,
                        icerik=content,
                        kategori=kategori,
                        yazar=bot_user,
                        olusturma_tarihi=news_date
                    )
                    
                    bekleyen.icerik = f"<p><strong>Kaynak:</strong> <a href='{news_data['url']}' target='_blank'>{news_data['url']}</a></p><hr>" + bekleyen.icerik
                    bekleyen.save()
                    
                    if news_data.get('image_url'):
                        self._download_and_save_image(bekleyen, news_data['image_url'])

                    self.stdout.write(self.style.SUCCESS(f'   ✅ Havuza Atıldı: {title[:30]}... ({news_date.strftime("%d.%m")})'))
                    total_found += 1
                    time.sleep(0.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Hata ({federation.ad}): {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'\n🛡️  Tamamlandı. Yeni: {total_found}, Eski: {skipped_old}, Tarihsiz/Atlanan: {skipped_nodate}, Başlık Çöp: {skipped_title}, Mükerrer: {skipped_duplicate}'))

    def _fix_encoding(self, text):
        if not text: return ""
        return ftfy.fix_text(text).strip()

    def _scrape_federation_news(self, federation):
        news_items = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            try:
                response = requests.get(federation.haberler_url, headers=headers, timeout=30, verify=False)
            except:
                return []

            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            elements = soup.select(federation.haber_listesi_selector)
            if not elements:
                 elements = [a for a in soup.select("a[href]") if any(x in a.get('href', '') for x in ["/haber", "/duyuru", "/detay"])]

            # İlk 10 linki kontrol et, çünkü bazıları menü item olabilir
            unique_urls = set()
            count = 0
            
            for el in elements:
                if count >= 8: break # Max 8 haber kontrolü
                
                data = self._extract_data(el, federation)
                if data and data['url'] not in unique_urls:
                    unique_urls.add(data['url'])
                    
                    # Detaya git
                    detail_data = self._fetch_detail(data['url'])
                    if not detail_data.get('date'):
                         # Listeden tarih bulmaya çalış (bazı sitelerde listede tarih var)
                         date_in_list = self._find_date_in_element(el)
                         if date_in_list:
                             detail_data['date'] = date_in_list
                    
                    data.update(detail_data)
                    news_items.append(data)
                    count += 1
                    
        except Exception:
            pass
        return news_items

    def _find_date_in_element(self, element):
        try:
            text = element.get_text()
            date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', text)
            if date_match:
                 return dateparser.parse(date_match.group(0), settings={'DATE_ORDER': 'DMY'})
        except: pass
        return None

    def _extract_data(self, element, federation):
        try:
            if element.name == 'a': link = element
            else: link = element.select_one('a')
            
            if not link: return None
            
            href = link.get('href')
            if not href: return None
            
            full_url = urljoin(federation.ana_url, href)
            
            title = link.get_text(strip=True)
            if not title: title = link.get('title')
            if not title:
                img = link.select_one('img')
                if img: title = img.get('alt')
            
            return {
                'title': title, # Burada temizlemiyoruz, handle'da yapıyoruz
                'url': full_url,
                'summary': "",
                'date': None 
            }
        except:
            return None

    def _fetch_detail(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10, verify=False)
            
            if resp.encoding == 'ISO-8859-1':
                resp.encoding = resp.apparent_encoding
                
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            date_obj = None
            
            # 1. URL Tarihi
            url_date_match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', url)
            if url_date_match:
                try:
                    date_str = f"{url_date_match.group(3)}.{url_date_match.group(2)}.{url_date_match.group(1)}"
                    date_obj = dateparser.parse(date_str, settings={'DATE_ORDER': 'DMY'})
                except: pass

            # 2. Meta Tarihler
            if not date_obj:
                meta_tags = [
                    ('meta', {'property': 'article:published_time'}),
                    ('meta', {'itemprop': 'datePublished'}),
                    ('meta', {'name': 'date'}),
                    ('meta', {'name': 'DC.date.issued'}),
                    ('time', {'datetime': True})
                ]
                
                for tag, attrs in meta_tags:
                    el = soup.find(tag, attrs)
                    if el:
                        val = el.get('content') or el.get('datetime') or el.get_text()
                        if val:
                            date_obj = dateparser.parse(val)
                            if date_obj: break
            
            # 3. Regex (En son)
            if not date_obj:
                page_text = soup.get_text()[:4000] 
                date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', page_text)
                if date_match:
                    date_src = date_match.group(0)
                    date_obj = dateparser.parse(date_src, settings={'DATE_ORDER': 'DMY'})

            content_div = soup.select_one('article') or soup.select_one('.content') or soup.find('main') or soup.find('body')
            content = str(content_div) if content_div else ""
            
            img = soup.find('img') # Basit resim bulucu
            image_url = urljoin(url, img['src']) if img else None
            
            return {
                'content': content, 
                'image_url': image_url,
                'date': date_obj
            }
        except:
            return {'content': "", 'image_url': None, 'date': None}

    def _download_and_save_image(self, instance, image_url):
        try:
            from django.core.files.base import ContentFile
            resp = requests.get(image_url, timeout=10, verify=False)
            if resp.status_code == 200:
                file_name = f"news_{instance.id}.jpg"
                instance.resim.save(file_name, ContentFile(resp.content), save=True)
        except:
            pass
