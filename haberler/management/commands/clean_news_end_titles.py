import re
from django.core.management.base import BaseCommand
from haberler.models import Haber

class Command(BaseCommand):
    help = 'Clean unwanted news titles at the end of all news articles'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning unwanted news titles at the end of all news articles...')
        
        try:
            # Get all news articles
            all_news = Haber.objects.all()
            
            self.stdout.write(f'Found {all_news.count()} news articles to process...')
            
            # Define patterns to remove from the end of articles
            # These are the specific patterns you mentioned in your query
            unwanted_end_patterns = [
                # Pattern for lists of news titles at the end of articles
                r'\s*Başkanımız Ercüment Taşdemir Madrid’de Dünya Karate Federasyonu Başkanı ile Bir Araya Geldi\s*\n.*2025/3 TEMEL EĞİTİM SINAV BAŞVURULARI BAŞLIYOR\s*\n.*Milli Takımımız Basel’de Zirvede\s*\n.*ULUSLARARASI MARMARA CUP KARATE ŞAMPİYONASI TAMAMLANDI\s*\n.*4. ve 5. KADEME ANTRENÖR KURSU\s*\n.*Türkiye Premier Ligi Rıdvan Gümüş Etabı Diyarbakır’da Tamamlandı\s*\n.*Türkiye Karate Premier Ligi Rıdvan Gümüş Etabı Diyarbakır’da Coşkuyla Başladı\s*',
                
                # Individual patterns for common news titles that appear at the end
                r'\s*Başkanımız Ercüment Taşdemir Madrid’de Dünya Karate Federasyonu Başkanı ile Bir Araya Geldi\s*$',
                r'\s*2025/3 TEMEL EĞİTİM SINAV BAŞVURULARI BAŞLIYOR\s*$',
                r'\s*Milli Takımımız Basel’de Zirvede\s*$',
                r'\s*ULUSLARARASI MARMARA CUP KARATE ŞAMPİYONASI TAMAMLANDI\s*$',
                r'\s*4. ve 5. KADEME ANTRENÖR KURSU\s*$',
                r'\s*Türkiye Premier Ligi Rıdvan Gümüş Etabı Diyarbakır’da Tamamlandı\s*$',
                r'\s*Türkiye Karate Premier Ligi Rıdvan Gümüş Etabı Diyarbakır’da Coşkuyla Başladı\s*$',
                
                # More general patterns for news titles at the end
                r'\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü0-9\s]*[A-ZÇĞİÖŞÜ][a-zçğıöşü0-9\s]*(?:BAŞLIYOR|TAMAMLANDI|BAŞLADI|ZİRVEDE|BİR ARAYA GELDİ)\s*$',
                
                # Pattern for multiple news titles appearing together at the end
                r'\s*(?:[A-ZÇĞİÖŞÜ][a-zçğıöşü0-9\s]*[A-ZÇĞİÖŞÜ][a-zçğıöşü0-9\s]*(?:BAŞLIYOR|TAMAMLANDI|BAŞLADI|ZİRVEDE|BİR ARAYA GELDİ)\s*\n){2,}',
                
                # Pattern to remove navigation sections at the end
                r'\s*DİĞER HABERLER.*$',
                r'\s*GENEL HABERLER.*$',
                r'\s*GÜNCEL DUYURULAR.*$',
                r'\s*ETKİNLİKLER.*$',
            ]
            
            cleaned_count = 0
            
            for news in all_news:
                original_content = news.icerik
                
                # Apply each pattern to clean the content
                cleaned_content = original_content
                for pattern in unwanted_end_patterns:
                    cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
                
                # Save if content was changed
                if cleaned_content != original_content:
                    news.icerik = cleaned_content.strip()
                    news.save()
                    cleaned_count += 1
                    self.stdout.write(f'Cleaned: {news.baslik[:50]}...')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleaned {cleaned_count} news articles!'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning news articles: {str(e)}')
            )