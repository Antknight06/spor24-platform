from django.core.management.base import BaseCommand
from haberler.models import Haber, FederasyonWebsite
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
import re
from datetime import datetime
from urllib.parse import urljoin
import time

class Command(BaseCommand):
    help = 'Federasyon sitelerinden doğru tarihleri çekip haberlerin tarihlerini düzelt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Güncellenecek maksimum haber sayısı (varsayılan: 50)'
        )
        parser.add_argument(
            '--federation-id',
            type=int,
            help='Belirli bir federasyon haberleri için (boş bırakılırsa tümü)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        federation_id = options.get('federation_id')
        
        self.stdout.write('📅 HABER TARİHLERİ DÜZELTME SİSTEMİ')
        self.stdout.write('=' * 50)
        
        # Kaynak URL'si olan haberleri al
        haberler_query = Haber.objects.filter(
            kaynak_url__isnull=False
        ).exclude(kaynak_url__exact='')
        
        if federation_id:
            haberler_query = haberler_query.filter(federasyon_website_id=federation_id)
        
        haberler = haberler_query.order_by('-id')[:limit]
        
        if not haberler:
            self.stdout.write(
                self.style.WARNING('⚠️  Kaynak URL\'si olan haber bulunamadı')
            )
            return
        
        total_updated = 0
        
        for haber in haberler:
            try:
                self.stdout.write(f'\n🔍 Kontrol ediliyor: {haber.baslik[:50]}...')
                
                # Tarih bilgisini federasyon sitesinden çek
                new_date = self._get_date_from_source(haber.kaynak_url)
                
                if new_date:
                    old_date = haber.olusturma_tarihi
                    haber.olusturma_tarihi = new_date
                    haber.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'   ✅ Güncellendi: {old_date.strftime("%d.%m.%Y")} → {new_date.strftime("%d.%m.%Y")}'
                        )
                    )
                    total_updated += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Tarih bulunamadı')
                    )
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Toplam {total_updated} haberin tarihi güncellendi!')
        )

    def _get_date_from_source(self, url):
        """Kaynak URL'den tarih bilgisini çek"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Farklı tarih selektörleri dene
            date_selectors = [
                '.date',
                '.tarih',
                'time',
                '.publish-date',
                '.news-date',
                '.article-date',
                '.post-date',
                '[datetime]',
                '.haber-tarih',
                '.entry-date'
            ]
            
            for selector in date_selectors:
                date_element = soup.select_one(selector)
                if date_element:
                    # datetime attribute'u kontrol et
                    datetime_attr = date_element.get('datetime')
                    if datetime_attr:
                        parsed_date = self._parse_iso_date(datetime_attr)
                        if parsed_date:
                            return parsed_date
                    
                    # Element metnini kontrol et
                    date_text = date_element.get_text(strip=True)
                    if date_text:
                        parsed_date = self._parse_turkish_date(date_text)
                        if parsed_date:
                            return parsed_date
            
            # Meta tag'lerden tarih bilgisi
            meta_date = soup.find('meta', property='article:published_time')
            if meta_date and meta_date.get('content'):
                parsed_date = self._parse_iso_date(meta_date['content'])
                if parsed_date:
                    return parsed_date
            
            # JSON-LD structured data
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    import json
                    data = json.loads(json_ld.string)
                    if isinstance(data, dict) and 'datePublished' in data:
                        parsed_date = self._parse_iso_date(data['datePublished'])
                        if parsed_date:
                            return parsed_date
                except:
                    pass
            
            # Sayfadaki tüm tarih benzeri metinleri ara
            all_text = soup.get_text()
            date_patterns = [
                r'(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s+(\d{4})',
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, all_text.lower())
                if matches:
                    # İlk bulunan tarihi al
                    date_match = matches[0]
                    parsed_date = self._parse_date_groups(date_match, pattern)
                    if parsed_date:
                        return parsed_date
            
            return None
        
        except Exception as e:
            return None

    def _parse_iso_date(self, date_string):
        """ISO 8601 tarih formatını parse et"""
        try:
            # Yaygın ISO formatları
            iso_formats = [
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d.%m.%Y %H:%M:%S',
                '%d.%m.%Y'
            ]
            
            # Z suffix'ini +00:00 ile değiştir
            if date_string.endswith('Z'):
                date_string = date_string[:-1] + '+00:00'
            
            for fmt in iso_formats:
                try:
                    dt = datetime.strptime(date_string.split('.')[0], fmt)
                    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None

    def _parse_turkish_date(self, date_text):
        """Türkçe tarih metnini parse et"""
        try:
            # Türkçe ay isimleri
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            date_text = date_text.lower().strip()
            
            # Farklı tarih formatları
            patterns = [
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 ocak 2024
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 15.01.2024
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 15/01/2024
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    parsed_date = self._parse_date_groups(groups, pattern)
                    if parsed_date:
                        return parsed_date
            
            return None
        
        except Exception:
            return None

    def _parse_date_groups(self, groups, pattern):
        """Tarih gruplarını parse et"""
        try:
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            if 'w+' in pattern:  # Türkçe ay adı formatı
                day, month_name, year = groups
                month = turkish_months.get(month_name.lower())
                if month:
                    dt = datetime(int(year), month, int(day))
                    return timezone.make_aware(dt)
            else:
                if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                    year, month, day = groups
                else:  # DD.MM.YYYY or DD/MM/YYYY
                    day, month, year = groups
                
                dt = datetime(int(year), int(month), int(day))
                return timezone.make_aware(dt)
            
            return None
        
        except Exception:
            return None