from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite
from haberler.services.news_scraper import NewsImportService
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
import re
from datetime import datetime

class Command(BaseCommand):
    help = 'karate.gov.tr sitesinden haberleri çeker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test modunda çalışır, veritabanına kaydetmez'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Çekilecek haber sayısı (varsayılan: 10)'
        )

    def handle(self, *args, **options):
        try:
            # karate.gov.tr federasyonunu al
            federation = FederasyonWebsite.objects.get(
                ad='Türkiye Karate Federasyonu (Resmi)'
            )
        except FederasyonWebsite.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    '❌ karate.gov.tr federasyonu bulunamadı. '
                    'Önce şu komutu çalıştırın: python ANT_News\\manage.py karate_gov_tr_ekle'
                )
            )
            return

        test_mode = options['test']
        limit = options['limit']
        
        if test_mode:
            self.stdout.write(
                self.style.WARNING('🧪 TEST MODU - Veritabanına kayıt yapılmayacak')
            )
        
        self.stdout.write(f'🔄 {federation.ad} sitesinden haberler çekiliyor...')
        self.stdout.write(f'📊 Limit: {limit} haber')
        
        # Özel karate.gov.tr scraper
        news_data = self.scrape_karate_gov_tr(federation, limit)
        
        if test_mode:
            # Test modunda sadece bulunan haberleri göster
            self.stdout.write(f'\n📝 Bulunan haberler ({len(news_data)}):\n')
            for i, news in enumerate(news_data, 1):
                self.stdout.write(f'{i}. {news["title"]}')
                self.stdout.write(f'   📅 {news["date"] or "Tarih bulunamadı"}')
                self.stdout.write(f'   🔗 {news["url"]}')
                if news["summary"]:
                    summary = news["summary"][:100] + "..." if len(news["summary"]) > 100 else news["summary"]
                    self.stdout.write(f'   📄 {summary}')
                self.stdout.write('')
        else:
            # Gerçek import işlemi
            import_service = NewsImportService()
            imported_count = 0
            
            for news in news_data:
                try:
                    # Haberi import et (NewsImportService'daki mantığı kullan)
                    from haberler.models import Haber, Kategori
                    from django.contrib.auth.models import User
                    from django.utils.text import slugify
                    
                    # Bot kullanıcı al/oluştur
                    bot_user, _ = User.objects.get_or_create(
                        username='karatebot',
                        defaults={
                            'email': 'karatebot@netspor.com',
                            'first_name': 'Karate',
                            'last_name': 'Bot',
                            'is_active': True
                        }
                    )
                    
                    # Kategori al
                    kategori = federation.kategori_set.first()
                    if not kategori:
                        kategori, _ = Kategori.objects.get_or_create(
                            slug='karate',
                            defaults={
                                'ad': 'Karate',
                                'aciklama': 'Karate haberleri',
                                'federasyon_website': federation
                            }
                        )
                    
                    # Haber zaten var mı kontrol et
                    if Haber.objects.filter(kaynak_url=news['url']).exists():
                        continue
                    
                    # Benzersiz slug oluştur
                    base_slug = slugify(news['title'])
                    slug = base_slug
                    counter = 1
                    while Haber.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    
                    # Get full content using the scraping service
                    full_content = import_service.scraping_service.get_news_content(news['url'])
                    if not full_content:
                        full_content = news['summary'] if news['summary'] else news['title']
                    
                    # Tarih formatını düzenle
                    olusturma_tarihi = timezone.now()
                    if news['date']:
                        # Türkçe tarih formatlarını düzenle
                        turkish_months = {
                            'Ocak': '01', 'Şubat': '02', 'Mart': '03', 'Nisan': '04',
                            'Mayıs': '05', 'Haziran': '06', 'Temmuz': '07', 'Ağustos': '08',
                            'Eylül': '09', 'Ekim': '10', 'Kasım': '11', 'Aralık': '12'
                        }
                        
                        # Tarih desenini bul ve düzenle
                        date_pattern = r'(\d{1,2})\s+([A-Za-zğüşöçİĞÜŞÖÇ]+)\s+(\d{4})\s+(\d{1,2}):(\d{2})'
                        match = re.search(date_pattern, news['date'])
                        if match:
                            day, month, year, hour, minute = match.groups()
                            # Türkçe ay ismini sayıya çevir
                            if month in turkish_months:
                                month_num = turkish_months[month]
                                # Django tarih formatına çevir
                                date_str = f"{year}-{month_num}-{day.zfill(2)} {hour.zfill(2)}:{minute}"
                                try:
                                    olusturma_tarihi = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                                except:
                                    olusturma_tarihi = timezone.now()
                    
                    # Haberi oluştur
                    haber = Haber.objects.create(
                        baslik=news['title'][:200],
                        slug=slug,
                        ozet=news['summary'][:500] if news['summary'] else news['title'][:500],
                        icerik=full_content,
                        kategori=kategori,
                        yazar=bot_user,
                        kaynak_url=news['url'],
                        federasyon_website=federation,
                        otomatik_eklendi=True,
                        yayinlandi=True,
                        olusturma_tarihi=olusturma_tarihi
                    )
                    
                    imported_count += 1
                    self.stdout.write(f'✅ İmport edildi: {news["title"][:50]}...')
                    
                except Exception as e:
                    self.stdout.write(f'❌ Hata: {news["title"][:50]}... - {str(e)}')
            
            # Son tarama zamanını güncelle
            federation.son_tarama = timezone.now()
            federation.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 İşlem tamamlandı! {imported_count} haber import edildi.'
                )
            )

    def scrape_karate_gov_tr(self, federation, limit):
        """karate.gov.tr için özelleştirilmiş scraper"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        news_list = []
        
        # Farklı kategorilerden haber çek
        categories = [
            'https://karate.gov.tr/haber-kategori/federasyon',
            'https://karate.gov.tr/haber-kategori-etkinlikler/4',
            'https://karate.gov.tr/haberler'
        ]
        
        for category_url in categories:
            try:
                self.stdout.write(f'📡 Taranan URL: {category_url}')
                response = session.get(category_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Debug: Sayfanın başlığını yazdır
                page_title = soup.find('title')
                if page_title:
                    self.stdout.write(f'📄 Sayfa başlığı: {page_title.get_text(strip=True)}')
                
                # Haber linklerini bul - karate.gov.tr'nin yapısına göre
                # Önce class'a göre ara
                haber_elements = soup.select('.haber-item, .news-item, .article, .post, .haber-box')
                
                if not haber_elements:
                    # İkinci yöntem: tüm a etiketlerini kontrol et
                    all_links = soup.find_all('a', href=True)
                    self.stdout.write(f'🔍 Toplam {len(all_links)} link bulundu')
                    
                    haber_count = 0
                    for link in all_links:
                        href = link.get('href', '')
                        
                        # Haber URL'lerini tanımla - daha esnek arama
                        if (('/haber/' in href or '/duyuru/' in href or 
                             'haber-kategori' in href or href.startswith('/haber') or
                             any(keyword in href.lower() for keyword in ['haberler', 'duyuru', 'etkinlik'])) 
                            and href not in [item['url'] for item in news_list]):
                            # Haber başlığı
                            title = link.get_text(strip=True)
                            
                            # Başlık kontrolü - çok kısa veya boş başlıkları filtrele
                            if not title or len(title) < 5:
                                # Eğer link içinde başlık yoksa, parent elementlerden ara
                                parent = link.parent
                                if parent:
                                    title = parent.get_text(strip=True)
                            
                            if not title or len(title) < 5:
                                continue
                                
                            # Tam URL oluştur
                            if href.startswith('/'):
                                full_url = f"https://karate.gov.tr{href}"
                            elif href.startswith('http'):
                                full_url = href
                            else:
                                full_url = f"https://karate.gov.tr/{href}"
                            
                            # Tarih bilgisi arama (linkin yakınında)
                            date_text = None
                            
                            # Link'in parent elementlerinde tarih ara
                            parent = link.parent
                            for _ in range(3):  # 3 seviye yukarı çık
                                if parent:
                                    text = parent.get_text()
                                    # Türkçe tarih formatlarını ara
                                    date_patterns = [
                                        r'\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}',
                                        r'\d{1,2}\.\d{1,2}\.\d{4}',
                                        r'\d{1,2}/\d{1,2}/\d{4}'
                                    ]
                                    
                                    for pattern in date_patterns:
                                        match = re.search(pattern, text, re.IGNORECASE)
                                        if match:
                                            date_text = match.group(0)
                                            break
                                    
                                    if date_text:
                                        break
                                    parent = parent.parent
                            
                            news_list.append({
                                'title': title[:200],  # Başlığı kısıtla
                                'url': full_url,
                                'summary': title,  # Şimdilik başlığı özet olarak kullan
                                'date': date_text
                            })
                            
                            haber_count += 1
                            self.stdout.write(f'✅ Haber bulundu: {title[:50]}...')
                            
                            if len(news_list) >= limit:
                                break
                else:
                    # Class'a göre bulunan elementlerden haberleri çıkar
                    self.stdout.write(f'🔍 {len(haber_elements)} haber elementi bulundu')
                    
                    for element in haber_elements[:limit]:
                        # Başlık bul
                        title_elem = element.select_one('h3, h4, .title, .baslik')
                        if not title_elem:
                            title_elem = element.find(['h3', 'h4'])
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue
                            
                        # Link bul
                        link_elem = element.find('a', href=True)
                        if not link_elem:
                            continue
                            
                        href = link_elem.get('href')
                        if not href:
                            continue
                            
                        # Tam URL oluştur
                        if href.startswith('/'):
                            full_url = f"https://karate.gov.tr{href}"
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            full_url = f"https://karate.gov.tr/{href}"
                            
                        # Tarih bilgisi
                        date_text = None
                        date_elem = element.select_one('.date, .tarih')
                        if date_elem:
                            date_text = date_elem.get_text(strip=True)
                        
                        news_list.append({
                            'title': title[:200],
                            'url': full_url,
                            'summary': title,
                            'date': date_text
                        })
                        
                        self.stdout.write(f'✅ Haber bulundu: {title[:50]}...')
                        
                        if len(news_list) >= limit:
                            break
                
                self.stdout.write(f'📊 {category_url} - {len([n for n in news_list if category_url in n["url"]])} haber bulundu')
                
                if len(news_list) >= limit:
                    break
                    
            except Exception as e:
                self.stdout.write(f'⚠️ {category_url} çekilirken hata: {str(e)}')
                continue
        
        return news_list[:limit]