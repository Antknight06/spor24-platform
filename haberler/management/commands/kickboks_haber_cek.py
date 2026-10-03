from django.core.management.base import BaseCommand
from django.utils import timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from haberler.models import FederasyonWebsite, Kategori, Haber
from django.contrib.auth.models import User
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Kickboks Federasyonu sitesinden haberleri çeker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-images',
            action='store_true',
            help='Haberlerin fotoğraflarını da çek',
        )
        parser.add_argument(
            '--max-news',
            type=int,
            default=20,
            help='Maksimum çekilecek haber sayısı (varsayılan: 20)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🥊 KICKBOKS FEDERASYONU HABER ÇEKİCİ\n')
        )
        self.stdout.write('=' * 50)
        
        try:
            federasyon = FederasyonWebsite.objects.get(ad__icontains='Kickboks')
            self.stdout.write(f"✅ Federasyon: {federasyon.ad}")
        except FederasyonWebsite.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("❌ Kickboks federasyonu bulunamadı!")
            )
            return
        
        # Çekilecek URL'ler
        urls_to_scrape = [
            {
                'url': federasyon.haberler_url,
                'name': 'Haberler',
                'type': 'haber'
            },
            {
                'url': 'https://kickboks.gov.tr/kategori/2-duyuru.html',
                'name': 'Duyurular', 
                'type': 'duyuru'
            }
        ]
        
        total_processed = 0
        max_news = options['max_news']
        
        for url_info in urls_to_scrape:
            self.stdout.write(f"\n📰 {url_info['name']} sayfası işleniyor...")
            self.stdout.write(f"🔗 URL: {url_info['url']}")
            
            try:
                response = requests.get(url_info['url'], timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code != 200:
                    self.stdout.write(
                        self.style.WARNING(f"❌ Erişim hatası: {response.status_code}")
                    )
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.select('li')
                
                self.stdout.write(f"🔍 {len(news_items)} li elementi bulundu")
                
                processed_count = 0
                
                for i, item in enumerate(news_items):
                    if processed_count >= max_news // 2:  # Her URL için yarısı kadar
                        break
                        
                    try:
                        # Link bul
                        link_elem = item.find('a')
                        if not link_elem:
                            continue
                        
                        href = link_elem.get('href', '')
                        if not href:
                            continue
                        
                        # Tam URL oluştur
                        full_url = urljoin(url_info['url'], href)
                        
                        # Başlık al
                        title = link_elem.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue
                        
                        # Haber benzeri içerik kontrolü
                        if not any(keyword in title.lower() for keyword in 
                                  ['haber', 'duyuru', 'şampiyon', 'turnuva', 'müsabaka', 'federasyon', 
                                   'başkan', 'antrenör', 'sporcu', 'milli', 'takım', 'yarışma']):
                            continue
                        
                        # Aynı URL'den haber var mı kontrol et
                        if Haber.objects.filter(kaynak_url=full_url).exists():
                            continue
                        
                        # Haber detayını çek
                        detail_content = self.scrape_news_detail(full_url)
                        
                        # Tarih bilgisi varsa al
                        date_elem = item.select_one('.date, .tarih, time, .news-date')
                        date_text = date_elem.get_text(strip=True) if date_elem else None
                        
                        # Özet bilgisi varsa al
                        summary_elem = item.select_one('.summary, .ozet, p')
                        summary = summary_elem.get_text(strip=True) if summary_elem else title
                        
                        # Veritabanına kaydet
                        if self.save_news_to_db(title, summary, detail_content, full_url, federasyon, url_info['type']):
                            processed_count += 1
                            total_processed += 1
                            
                            self.stdout.write(
                                self.style.SUCCESS(f"   ✅ {title[:50]}...")
                            )
                        
                        # Rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"   ❌ İşleme hatası: {e}")
                        )
                        continue
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {url_info['name']} - {processed_count} yeni içerik işlendi")
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {url_info['name']} sayfası hatası: {e}")
                )
        
        # Federasyon bilgilerini güncelle
        federasyon.son_tarama = timezone.now()
        if total_processed > 0:
            federasyon.son_yeni_haber_zamani = timezone.now()
        federasyon.save()
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 TOPLAM: {total_processed} yeni içerik başarıyla işlendi!")
        )
        
        # Fotoğraf çekme
        if options['with_images'] and total_processed > 0:
            self.stdout.write("\n🖼️ Fotoğraflar çekiliyor...")
            self.scrape_images_for_recent_news()

    def scrape_news_detail(self, url):
        """Haber detay sayfasını çeker"""
        
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return "İçerik alınamadı."
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # İçerik selector'larını dene
            content_selectors = [
                '.content', '.icerik', '.haber-icerik', '.news-content',
                '.article-content', '.post-content', '.entry-content',
                'article', '.main-content', '.page-content', '.container .row .col'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Script ve style etiketlerini kaldır
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    
                    content = content_elem.get_text(strip=True)
                    if len(content) > 100:
                        break
            
            if not content:
                # Paragrafları topla
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs 
                                  if len(p.get_text(strip=True)) > 20])
            
            # İçeriği temizle ve kısalt
            if content:
                content = ' '.join(content.split())  # Fazla boşlukları temizle
                return content[:3000] if len(content) > 3000 else content
            else:
                return "İçerik alınamadı."
            
        except Exception as e:
            return "İçerik alınamadı."

    def save_news_to_db(self, title, summary, content, source_url, federasyon, content_type='haber'):
        """Haberi veritabanına kaydeder"""
        
        try:
            # Kategoriyi al
            kategori = Kategori.objects.get(slug='kickboks')
            
            # Bot kullanıcısını al veya oluştur
            bot_user, created = User.objects.get_or_create(
                username='newsbot',
                defaults={
                    'email': 'newsbot@antnews.com',
                    'first_name': 'News',
                    'last_name': 'Bot',
                    'is_active': True
                }
            )
            
            # Başlığa içerik tipini ekle
            if content_type == 'duyuru' and 'duyuru' not in title.lower():
                title = f"[DUYURU] {title}"
            
            # Slug oluştur
            base_slug = slugify(title)
            if not base_slug:
                base_slug = f"kickboks-{content_type}"
            
            slug = base_slug
            counter = 1
            while Haber.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Haberi kaydet
            haber = Haber.objects.create(
                baslik=title[:200],
                slug=slug,
                ozet=summary[:500] if summary else title[:500],
                icerik=content,
                kategori=kategori,
                yazar=bot_user,
                kaynak_url=source_url,
                federasyon_website=federasyon,
                otomatik_eklendi=True,
                yayinlandi=True
            )
            
            return True
            
        except Exception as e:
            return False

    def scrape_images_for_recent_news(self):
        """Son eklenen haberlerin fotoğraflarını çeker"""
        
        # Fotoğrafı olmayan son 10 kickboks haberini al
        recent_news = Haber.objects.filter(
            kategori__slug='kickboks',
            resim__isnull=True,
            kaynak_url__isnull=False
        ).order_by('-olusturma_tarihi')[:10]
        
        for haber in recent_news:
            try:
                # Basit fotoğraf çekme (detaylı implementasyon için ayrı komut kullanılabilir)
                response = requests.get(haber.kaynak_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    img = soup.find('img')
                    if img and img.get('src'):
                        self.stdout.write(f"   📷 {haber.baslik[:30]}... için fotoğraf bulundu")
                        # Fotoğraf indirme işlemi burada yapılabilir
                        
            except Exception:
                pass