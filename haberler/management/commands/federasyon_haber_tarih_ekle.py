from django.core.management.base import BaseCommand
from haberler.models import Haber
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
import re
from datetime import datetime
import time

class Command(BaseCommand):
    help = 'Federasyondan alınan tüm haberler için tarihleri çekip ekle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Güncellenecek maksimum haber sayısı (varsayılan: 100)'
        )
        parser.add_argument(
            '--federation-domain',
            type=str,
            default='karate.gov.tr',
            help='Hangi federasyonun haberleri için tarih çekilecek (varsayılan: karate.gov.tr)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        federation_domain = options['federation_domain']
        
        self.stdout.write('📅 FEDERASYON HABERLERİ İÇİN TARİH EKLEME SİSTEMİ')
        self.stdout.write('=' * 55)
        self.stdout.write(f'🌐 Federasyon: {federation_domain}')
        
        # Belirtilen federasyondan alınan haberleri bul
        haberler = Haber.objects.filter(
            kaynak_url__icontains=federation_domain,
            kaynak_url__isnull=False
        ).exclude(kaynak_url__exact='').order_by('-id')[:limit]
        
        if not haberler:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {federation_domain} adresinden alınan haber bulunamadı')
            )
            return
        
        self.stdout.write(f'🔍 {haberler.count()} haber işlenecek')
        
        total_updated = 0
        
        for i, haber in enumerate(haberler, 1):
            try:
                self.stdout.write(f'\n[{i}/{haberler.count()}] 🔍 Kontrol ediliyor: {haber.baslik[:50]}...')
                self.stdout.write(f'🔗 Kaynak: {haber.kaynak_url}')
                
                # Tarih bilgisini federasyon sitesinden çek
                new_date = self._get_date_from_source(haber.kaynak_url)
                
                if new_date:
                    old_date = haber.olusturma_tarihi
                    haber.olusturma_tarihi = new_date
                    haber.save(update_fields=['olusturma_tarihi'])
                    
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
                time.sleep(1)
                
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
            
            # Önce .tarih elementini kontrol et (yayın tarihi için daha güvenilir)
            tarih_element = soup.select_one('.tarih')
            if tarih_element:
                date_text = tarih_element.get_text(strip=True)
                if date_text:
                    # Tarihi temizle (iconları kaldır)
                    import re
                    date_text = re.sub(r'\s+', ' ', date_text).strip()
                    parsed_date = self._parse_turkish_date(date_text)
                    if parsed_date:
                        self.stdout.write(f'   📅 .tarih elementi ile bulundu: {parsed_date}')
                        return parsed_date
            
            # Sonra diğer date elementlerini kontrol et
            date_selectors = [
                'time',
                '.publish-date',
                '.news-date',
                '.article-date',
                '.post-date',
                '[datetime]',
                '.haber-tarih',
                '.entry-date',
                '.published',
                '.post-time',
                '.timestamp',
                '.date'  # En sona taşıdık çünkü birden fazla olabilir
            ]
            
            # Önce belirli elementlerde ara
            for selector in date_selectors:
                date_elements = soup.select(selector)
                for date_element in date_elements:
                    # datetime attribute'u kontrol et
                    datetime_attr = date_element.get('datetime')
                    if datetime_attr:
                        parsed_date = self._parse_iso_date(datetime_attr)
                        if parsed_date:
                            self.stdout.write(f'   📅 DateTime attribute ile bulundu: {parsed_date}')
                            return parsed_date
                    
                    # Element metnini kontrol et
                    date_text = date_element.get_text(strip=True)
                    if date_text:
                        parsed_date = self._parse_turkish_date(date_text)
                        if parsed_date:
                            self.stdout.write(f'   📅 Element text ile bulundu: {parsed_date}')
                            return parsed_date
            
            # Meta tag'lerden tarih bilgisi
            meta_dates = [
                ('meta', {'property': 'article:published_time'}),
                ('meta', {'name': 'publish-date'}),
                ('meta', {'name': 'date'}),
                ('meta', {'property': 'og:article:published_time'}),
                ('meta', {'name': 'article:published_time'})
            ]
            
            for tag, attrs in meta_dates:
                meta_dates_found = soup.find_all(tag, attrs=attrs)
                for meta_date in meta_dates_found:
                    if meta_date.get('content'):
                        parsed_date = self._parse_iso_date(meta_date['content'])
                        if parsed_date:
                            self.stdout.write(f'   📅 Meta tag ile bulundu: {parsed_date}')
                            return parsed_date
            
            # JSON-LD structured data
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for json_ld in json_ld_scripts:
                try:
                    import json
                    data = json.loads(json_ld.string)
                    # Tek bir obje veya liste olabilir
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        if isinstance(item, dict):
                            # Farklı anahtarlar altında tarih bilgisi olabilir
                            date_keys = ['datePublished', 'dateCreated', 'publishDate', 'date']
                            for key in date_keys:
                                if key in item:
                                    parsed_date = self._parse_iso_date(item[key])
                                    if parsed_date:
                                        self.stdout.write(f'   📅 JSON-LD ile bulundu: {parsed_date}')
                                        return parsed_date
                except:
                    pass
            
            # Tüm sayfada tarih ara - en iyi tarihi bulmak için
            all_text = soup.get_text()
            extracted_date = self._extract_first_valid_date(all_text)
            if extracted_date:
                self.stdout.write(f'   📅 Sayfa metni ile bulundu: {extracted_date}')
                return extracted_date
            
            self.stdout.write(f'   ⚠️  Tarih bulunamadı')
            return None
        
        except Exception as e:
            self.stdout.write(f'   ❌ Tarih çekme hatası: {e}')
            return None

    def _extract_first_valid_date(self, text):
        """Metin içindeki ilk geçerli tarihi çıkar"""
        # Tarih pattern'leri - zaman bilgisiyle
        date_patterns = [
            r'(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s+(\d{4})\s+(\d{1,2}):(\d{2})',  # 15 ocak 2024 14:30
            r'(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s+(\d{4})',  # 15 ocak 2024
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})',  # 15.01.2024 14:30
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 15.01.2024
            r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})',  # 15/01/2024 14:30
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 15/01/2024
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})',  # 2024-01-15 14:30
            r'(\d{4})-(\d{1,2})-(\d{1,2})'  # 2024-01-15
        ]
        
        # Bugünün tarihi
        today = timezone.now().date()
        
        # Tüm tarihleri topla
        all_dates = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    parsed_date = self._parse_date_groups_with_time(match, pattern)
                    if parsed_date:
                        # Tarihin合理性 kontrolü - çok yakın geçmişte olmalı
                        date_obj = parsed_date.date()
                        # 5 yıldan eski veya gelecekteki tarihleri reddet
                        if date_obj.year >= (today.year - 5) and date_obj <= today:
                            all_dates.append((parsed_date, date_obj))
                except:
                    continue
        
        # Tarihleri sırala ve en eski uygun tarihi seç
        if all_dates:
            # Tarihi en yeniden en eskiye sırala
            all_dates.sort(key=lambda x: x[1])
            # İlk tarihi (en eski) döndür
            return all_dates[0][0]
        
        return None

    def _parse_iso_date(self, date_string):
        """ISO 8601 tarih formatını parse et"""
        try:
            # Yaygın ISO formatları - zaman bilgisiyle
            iso_formats = [
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%d.%m.%Y %H:%M:%S',
                '%d.%m.%Y %H:%M',
                '%d.%m.%Y',
                '%m/%d/%Y',
                '%d/%m/%Y'
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
            
            # Farklı tarih formatları - zaman bilgisiyle
            patterns = [
                r'(\d{1,2})\s+(\w+)\s+(\d{4})\s+(\d{1,2}):(\d{2})',  # 15 ocak 2024 14:30
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 ocak 2024
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})',  # 15.01.2024 14:30
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 15.01.2024
                r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})',  # 15/01/2024 14:30
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 15/01/2024
                r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})',  # 2024-01-15 14:30
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    parsed_date = self._parse_date_groups_with_time(groups, pattern)
                    if parsed_date:
                        return parsed_date
            
            return None
        
        except Exception:
            return None

    def _parse_date_groups_with_time(self, groups, pattern):
        """Tarih ve zaman gruplarını parse et"""
        try:
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            # Zaman bilgisiyle mi?
            has_time = ':(' in pattern or len(groups) >= 5
            
            if any(month in ''.join(groups).lower() for month in turkish_months.keys()):  # Türkçe ay adı formatı
                if has_time and len(groups) >= 5:  # Gün, ay, yıl, saat, dakika
                    day, month_name, year, hour, minute = groups
                    month = turkish_months.get(month_name.lower())
                    if month:
                        dt = datetime(int(year), month, int(day), int(hour), int(minute))
                        return timezone.make_aware(dt)
                else:  # Sadece tarih
                    day, month_name, year = groups[:3]
                    month = turkish_months.get(month_name.lower())
                    if month:
                        dt = datetime(int(year), month, int(day))
                        return timezone.make_aware(dt)
            else:
                if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                    if has_time and len(groups) >= 5:  # Yıl, ay, gün, saat, dakika
                        year, month, day, hour, minute = groups
                        dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                        return timezone.make_aware(dt)
                    else:  # Sadece tarih
                        year, month, day = groups[:3]
                        dt = datetime(int(year), int(month), int(day))
                        return timezone.make_aware(dt)
                else:  # DD.MM.YYYY
                    if has_time and len(groups) >= 5:  # Gün, ay, yıl, saat, dakika
                        day, month, year, hour, minute = groups
                        dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                        return timezone.make_aware(dt)
                    else:  # Sadece tarih
                        day, month, year = groups[:3]
                        dt = datetime(int(year), int(month), int(day))
                        return timezone.make_aware(dt)
            
            return None
        
        except Exception:
            return None

    def _parse_date_groups(self, groups, pattern):
        """Tarih gruplarını parse et (geriye dönük uyumluluk için)"""
        try:
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            if any(month in ''.join(groups).lower() for month in turkish_months.keys()):  # Türkçe ay adı formatı
                day, month_name, year = groups[:3]  # Sadece ilk 3 grubu al
                month = turkish_months.get(month_name.lower())
                if month:
                    dt = datetime(int(year), month, int(day))
                    return timezone.make_aware(dt)
            else:
                if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                    year, month, day = groups[:3]  # Sadece ilk 3 grubu al
                else:  # DD.MM.YYYY or DD/MM/YYYY
                    day, month, year = groups[:3]  # Sadece ilk 3 grubu al
                
                dt = datetime(int(year), int(month), int(day))
                return timezone.make_aware(dt)
            
            return None
        
        except Exception:
            return None
