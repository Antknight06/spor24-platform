import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from urllib.parse import urljoin, urlparse
import time

class Command(BaseCommand):
    help = 'Türkiye Wushu Kung Fu Federasyonu haberlerini keşfeder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Keşfedilecek maksimum haber sayısı (varsayılan: 50)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write('🔍 TÜRKİYE WUSHU KUNG FU FEDERASYONU HABERLERİ KEŞFETME')
        self.stdout.write('=' * 70)
        
        # URLs to check
        urls_to_check = [
            'https://twkf.gov.tr/tum-duyurular/',
            'https://twkf.gov.tr/haberler/',
            'https://twkf.gov.tr/duyurular/',
            'https://twkf.gov.tr/',
        ]
        
        all_articles = set()  # Use set to avoid duplicates
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for base_url in urls_to_check:
            try:
                self.stdout.write(f'\n🌐 Kontrol ediliyor: {base_url}')
                response = requests.get(base_url, headers=headers, timeout=30, verify=False)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all links that might be articles
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href')
                    if not href:
                        continue
                        
                    # Check if the link looks like a Wushu article
                    if any(keyword in href.lower() for keyword in ['duyuru', 'haber', 'news', 'announcement']):
                        # Convert to absolute URL
                        full_url = urljoin(base_url, href)
                        
                        # Parse the URL to check if it's from the same domain
                        parsed_url = urlparse(full_url)
                        if 'twkf.gov.tr' in parsed_url.netloc:
                            # Only add URLs that look like article pages (not category pages)
                            if not any(exclude in full_url.lower() for exclude in ['tum-duyurular', 'haberler', 'duyurular', 'category']):
                                all_articles.add(full_url)
                                self.stdout.write(f'   ✅ Bulundu: {full_url}')
                                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(f'   ❌ Hata: {e}')
                continue
        
        self.stdout.write(f'\n📊 Toplam benzersiz makale bulundu: {len(all_articles)}')
        
        # Save to file
        with open('wushu_haber_linkleri.txt', 'w', encoding='utf-8') as f:
            f.write("# Türkiye Wushu Kung Fu Federasyonu Haber Linkleri\n")
            f.write("# Format: URL\n")
            f.write("=" * 60 + "\n\n")
            
            for url in list(all_articles)[:limit]:
                f.write(f"{url}\n")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! {min(len(all_articles), limit)} haber linki wushu_haber_linkleri.txt dosyasına kaydedildi.'
            )
        )
        
        # Show first 10 articles
        self.stdout.write('\n📋 İlk 10 keşfedilen haber:')
        self.stdout.write('=' * 60)
        for i, url in enumerate(list(all_articles)[:10], 1):
            self.stdout.write(f"{i:2d}. {url}")