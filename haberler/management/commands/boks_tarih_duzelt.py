from django.core.management.base import BaseCommand
from django.utils import timezone
from haberler.models import Haber
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

class Command(BaseCommand):
    help = 'Boks federasyonu haberlerinin tarihlerini düzeltir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recent',
            action='store_true',
            help='Sadece son 30 gündeki haberleri düzelt',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maksimum işlenecek haber sayısı (varsayılan: 50)',
        )

    def handle(self, *args, **options):
        self.stdout.write('🥊 BOKS HABERLERİ TARİH DÜZELTİCİ')
        self.stdout.write('=' * 50)
        
        # Boks haberlerini al
        boks_haberler = Haber.objects.filter(kategori__slug='boks')
        
        if options['recent']:
            # Son 30 gündeki haberler
            from datetime import timedelta
            cutoff_date = timezone.now() - timedelta(days=30)
            boks_haberler = boks_haberler.filter(olusturma_tarihi__gte=cutoff_date)
        
        boks_haberler = boks_haberler.order_by('-olusturma_tarihi')[:options['limit']]
        
        self.stdout.write(f'📰 {boks_haberler.count()} boks haberi işlenecek')
        
        if not boks_haberler.exists():
            self.stdout.write(self.style.WARNING('İşlenecek haber bulunamadı'))
            return
        
        # Tarih düzeltme işlemi
        updated_count = self.fix_boks_dates(boks_haberler)
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 {updated_count} haberin tarihi güncellendi!')
        )

    def fix_boks_dates(self, haberler):
        """Boks haberlerinin tarihlerini düzeltir"""
        
        updated_count = 0
        
        # Önce haber listesi sayfasından tarihleri çek
        list_dates = self.get_dates_from_news_list()
        
        if list_dates:
            self.stdout.write(f'📋 Haber listesinden {len(list_dates)} tarih bulundu')
            updated_count += self.update_dates_from_dict(haberler, list_dates, "Haber listesi")
        
        # Sonra her haber sayfasını kontrol et (sadece eşleşmeyenler için)
        unmatched_haberler = []
        for haber in haberler:
            if haber.kaynak_url not in list_dates:
                unmatched_haberler.append(haber)
        
        if unmatched_haberler:
            self.stdout.write(f'🔍 {len(unmatched_haberler)} haber için tek tek kontrol yapılıyor...')
            page_dates = self.get_dates_from_individual_pages(unmatched_haberler[:10])  # İlk 10'u
            updated_count += self.update_dates_from_dict(unmatched_haberler, page_dates, "Haber sayfası")
        
        return updated_count

    def get_dates_from_news_list(self):
        """Boks federasyonu haber listesinden tarihleri çeker"""
        
        base_url = 'https://www.turkboks.gov.tr'
        all_dates = {}
        
        # Haber listesi sayfaları
        list_urls = [
            f'{base_url}/haberler/',
            f'{base_url}/haberler/page/2/'
        ]
        
        for url in list_urls:
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    dates = self.extract_dates_from_list_page(soup, base_url)
                    all_dates.update(dates)
                
            except Exception as e:
                self.stdout.write(f'⚠️ {url} hatası: {e}')
            
            time.sleep(0.5)  # Rate limiting
        
        return all_dates

    def extract_dates_from_list_page(self, soup, base_url):
        """Haber listesi sayfasından tarihleri çıkarır"""
        
        dates = {}
        
        # Li elementlerini kontrol et (en başarılı yöntem)
        items = soup.select('li')
        
        for item in items:
            link = item.find('a')
            if not link or not link.get('href'):
                continue
            
            href = link.get('href')
            if not href or len(href) < 10:
                continue
            
            # Tam URL oluştur
            if href.startswith('/'):
                full_url = f"{base_url}{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Tarih ara
            date = self.find_date_in_element(item)
            if date:
                dates[full_url] = date
        
        return dates

    def get_dates_from_individual_pages(self, haberler):
        """Her haber sayfasını ziyaret ederek tarih çeker"""
        
        dates = {}
        
        for i, haber in enumerate(haberler, 1):
            self.stdout.write(f'   📰 {i}/{len(haberler)}: {haber.baslik[:40]}...')
            
            try:
                response = requests.get(haber.kaynak_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    date = self.extract_date_from_news_page(soup)
                    
                    if date:
                        dates[haber.kaynak_url] = date
                        self.stdout.write(f'      ✅ {date.strftime("%d.%m.%Y")}')
                    else:
                        self.stdout.write(f'      ⚠️ Tarih bulunamadı')
                else:
                    self.stdout.write(f'      ❌ HTTP {response.status_code}')
                    
            except Exception as e:
                self.stdout.write(f'      ❌ Hata: {e}')
            
            time.sleep(0.5)  # Rate limiting
        
        return dates

    def extract_date_from_news_page(self, soup):
        """Haber sayfasından tarih çıkarır"""
        
        # Time tag'leri kontrol et
        time_tags = soup.find_all('time')
        for time_tag in time_tags:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                try:
                    parsed_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    if 2020 <= parsed_date.year <= 2025:
                        return timezone.make_aware(parsed_date.replace(tzinfo=None))
                except:
                    continue
        
        # Meta tag'leri kontrol et
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[property="article:modified_time"]',
            'meta[name="date"]'
        ]
        
        for selector in meta_selectors:
            meta = soup.select_one(selector)
            if meta and meta.get('content'):
                try:
                    date_str = meta.get('content')
                    if 'T' in date_str:
                        parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        return timezone.make_aware(parsed_date.replace(tzinfo=None))
                except:
                    continue
        
        return None

    def find_date_in_element(self, element):
        """HTML elementinde tarih arar"""
        
        # Time tag
        time_tag = element.find('time')
        if time_tag:
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                try:
                    parsed_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    return timezone.make_aware(parsed_date.replace(tzinfo=None))
                except:
                    pass
        
        # Element metninden tarih çıkar
        text = element.get_text()
        return self.extract_date_from_text(text)

    def extract_date_from_text(self, text):
        """Metinden tarih çıkarır"""
        
        # Türkçe ay adları
        month_map = {
            'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4,
            'Mayıs': 5, 'Haziran': 6, 'Temmuz': 7, 'Ağustos': 8,
            'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12,
            'Oca': 1, 'Şub': 2, 'Mar': 3, 'Nis': 4,
            'May': 5, 'Haz': 6, 'Tem': 7, 'Ağu': 8,
            'Eyl': 9, 'Eki': 10, 'Kas': 11, 'Ara': 12
        }
        
        patterns = [
            r'(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+(\d{4})',
            r'(\d{1,2})\s+(Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Eyl|Eki|Kas|Ara)\s+(\d{4})',
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if len(match) == 3:
                        if match[1] in month_map:  # Türkçe ay adı
                            day, month_name, year = match
                            month = month_map[month_name]
                        else:  # Sayısal format
                            day, month, year = match
                        
                        year, month, day = int(year), int(month), int(day)
                        
                        if 2020 <= year <= 2025 and 1 <= month <= 12 and 1 <= day <= 31:
                            return timezone.make_aware(datetime(year, month, day))
                except:
                    continue
        
        return None

    def update_dates_from_dict(self, haberler, dates_dict, source_name):
        """Tarih sözlüğünden veritabanını günceller"""
        
        if not dates_dict:
            return 0
        
        updated_count = 0
        
        for haber in haberler:
            if haber.kaynak_url in dates_dict:
                new_date = dates_dict[haber.kaynak_url]
                old_date = haber.olusturma_tarihi
                
                # Tarih farklıysa güncelle (1 günden fazla fark varsa)
                if abs((old_date.replace(tzinfo=None) - new_date.replace(tzinfo=None)).days) > 1:
                    haber.olusturma_tarihi = new_date
                    haber.save()
                    updated_count += 1
                    
                    self.stdout.write(
                        f'   ✅ {haber.baslik[:40]}... '
                        f'({old_date.strftime("%d.%m.%Y")} → {new_date.strftime("%d.%m.%Y")})'
                    )
        
        if updated_count > 0:
            self.stdout.write(f'📊 {source_name}: {updated_count} haber güncellendi')
        
        return updated_count