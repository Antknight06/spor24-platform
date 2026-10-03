import re
from django.core.management.base import BaseCommand
from haberler.models import Haber, Kategori

class Command(BaseCommand):
    help = 'Clean unwanted text at the end of karate news articles'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning unwanted text at the end of karate news articles...')
        
        try:
            # Get the Karate category
            karate_category = Kategori.objects.get(ad='Karate')
            
            # Get all karate news
            karate_news = Haber.objects.filter(kategori=karate_category)
            
            self.stdout.write(f'Found {karate_news.count()} karate news articles to process...')
            
            # Define patterns to remove from the end of articles
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
                # New patterns to remove other news titles at the end of articles
                r'\s*\d{1,2}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s+\d{4}\s+\d{1,2}:\d{2}\s*$',
                r'\s*[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]{10,}?\s+\d{1,2}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s+\d{4}\s+\d{1,2}:\d{2}\s*$',
                # Pattern to remove lists of news titles that appear at the end
                r'\s*(?:[A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]{10,}?\s+\d{1,2}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]*\s+\d{4}\s+\d{1,2}:\d{2}\s*){3,}\s*$'
            ]
            
            cleaned_count = 0
            
            for news in karate_news:
                original_content = news.icerik
                
                # Apply each pattern to clean the content
                cleaned_content = original_content
                for pattern in unwanted_end_patterns:
                    cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
                
                # Also remove any remaining navigation-like text at the end
                cleaned_content = re.sub(r'\s*[A-ZÇĞİÖŞÜ]{2,}[\sA-ZÇĞİÖŞÜ]*\s*$', '', cleaned_content)
                
                # Save if content was changed
                if cleaned_content != original_content:
                    news.icerik = cleaned_content.strip()
                    news.save()
                    cleaned_count += 1
                    self.stdout.write(f'Cleaned: {news.baslik[:50]}...')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleaned {cleaned_count} karate news articles!'
                )
            )
            
        except Kategori.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Karate category not found!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning karate news: {str(e)}')
            )