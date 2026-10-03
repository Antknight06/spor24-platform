from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from haberler.models import FederasyonWebsite, BekleyenHaber
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests
from bs4 import BeautifulSoup
import time

class Command(BaseCommand):
    help = 'Mevcut bekleyen haberlerin tarihlerini günceller'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🔄 BEKLEYEN HABER TARİHLERİNİ GÜNCELLE\n')
        )
        self.stdout.write('=' * 50)
        
        # Get all pending news without haber_tarihi
        pending_news_without_date = BekleyenHaber.objects.filter(
            onaylandi=False, 
            reddedildi=False,
            haber_tarihi__isnull=True
        )
        
        if not pending_news_without_date.exists():
            self.stdout.write(
                self.style.WARNING('Tarihi olmayan bekleyen haber bulunamadı.')
            )
            return
        
        self.stdout.write(f'Güncellenecek haber sayısı: {pending_news_without_date.count()}')
        
        updated_count = 0
        
        # Process each pending news
        for pending_news in pending_news_without_date:
            try:
                # Get the website configuration
                website = pending_news.federasyon_website
                
                if not website.haber_tarih_selector:
                    continue
                
                # Fetch the news page
                response = requests.get(pending_news.kaynak_url, timeout=10)
                response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to extract date using the configured selectors
                selectors = website.haber_tarih_selector.split(',')
                date = None
                
                for selector in selectors:
                    selector = selector.strip()
                    date_element = soup.select_one(selector)
                    if date_element:
                        date_text = date_element.get_text(strip=True)
                        date = self.parse_date(date_text)
                        if date:
                            break
                
                # Update the pending news with the extracted date
                if date:
                    pending_news.haber_tarihi = date
                    pending_news.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {pending_news.baslik[:50]} - Tarih güncellendi: {date}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  {pending_news.baslik[:50]} - Tarih bulunamadı')
                    )
                
                # Be respectful to the servers - add a small delay
                time.sleep(0.5)
                
            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {pending_news.baslik[:50]} - Website erişim hatası: {e}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {pending_news.baslik[:50]} - İşleme hatası: {e}')
                )
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Güncelleme tamamlandı! {updated_count} haberin tarihi güncellendi.')
        )
    
    def parse_date(self, date_text):
        """Parse date text into datetime object"""
        if not date_text:
            return None
            
        try:
            # Clean the date text
            date_text = date_text.strip()
            
            # Try common Turkish date formats
            import re
            from django.utils.dateparse import parse_datetime, parse_date
            from django.utils import timezone as dj_timezone
            import datetime
            
            # Try the format used by Kickboks: DD-MM-YYYY
            kickboks_pattern = r'(\d{1,2})-(\d{1,2})-(\d{4})'
            match = re.match(kickboks_pattern, date_text)
            if match:
                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                dt = datetime.datetime(year, month, day)
                return dj_timezone.make_aware(dt)
                
            # Try ISO format first
            dt = parse_datetime(date_text)
            if dt:
                return dj_timezone.make_aware(dt) if dj_timezone.is_naive(dt) else dt
            
            # Try date only format
            d = parse_date(date_text)
            if d:
                return dj_timezone.make_aware(datetime.datetime.combine(d, datetime.datetime.min.time()))
            
            # Try common Turkish formats
            # Format: 24.09.2025 or 24.09.2025 13:00
            turkish_pattern1 = r'(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2}))?'
            match = re.match(turkish_pattern1, date_text)
            if match:
                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if match.group(4):  # Time is present
                    hour, minute = int(match.group(4)), int(match.group(5))
                    dt = datetime.datetime(year, month, day, hour, minute)
                else:
                    dt = datetime.datetime(year, month, day)
                return dj_timezone.make_aware(dt)
            
            # Format: 24 Eylül 2025 or 24 Eylül 2025 13:00
            months_tr = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            for month_name, month_num in months_tr.items():
                if month_name in date_text.lower():
                    # Extract day and year
                    parts = date_text.split()
                    day = None
                    year = None
                    for part in parts:
                        if part.isdigit():
                            if len(part) == 4:  # Year
                                year = int(part)
                            elif len(part) <= 2:  # Day
                                day = int(part)
                    
                    if day and year:
                        # Extract time if present
                        hour, minute = 0, 0
                        time_match = re.search(r'(\d{1,2}):(\d{2})', date_text)
                        if time_match:
                            hour, minute = int(time_match.group(1)), int(time_match.group(2))
                        
                        dt = datetime.datetime(year, month_num, day, hour, minute)
                        return dj_timezone.make_aware(dt)
            
        except Exception:
            pass
        
        return None