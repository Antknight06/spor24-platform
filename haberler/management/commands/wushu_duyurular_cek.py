import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite, Haber, Kategori
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import time
import re

class Command(BaseCommand):
    help = 'Türkiye Wushu Kung Fu Federasyonu duyurularını çeker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Çekilecek duyuru sayısı (varsayılan: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece göster, gerçekten kaydetme'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write('🥋 TÜRKİYE WUSHU KUNG FU FEDERASYONU DUYURULARI ÇEKME SİSTEMİ')
        self.stdout.write('=' * 70)
        
        try:
            # Türkiye Wushu Kung Fu Federasyonu'nu bul
            federation = FederasyonWebsite.objects.get(ad='Türkiye Wushu Kung Fu Federasyonu')
            self.stdout.write(f'Federasyon: {federation.ad}')
        except FederasyonWebsite.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Türkiye Wushu Kung Fu Federasyonu veritabanında bulunamadı')
            )
            return
        
        # Kategoriyi bul
        try:
            kategori = Kategori.objects.get(federasyon_website=federation)
        except Kategori.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('⚠️  Kategori bulunamadı')
            )
            return
        
        # Bot kullanıcı oluştur/al
        bot_user, created = User.objects.get_or_create(
            username='wushu_duyuru_importer',
            defaults={
                'email': 'wushu_duyuru@federations.gov.tr',
                'first_name': 'Wushu',
                'last_name': 'Duyuru Importer',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('🤖 Yeni bot kullanıcı oluşturuldu')
            )
        
        # Duyuruları çek
        announcements = self._scrape_announcements(federation, limit)
        
        if not announcements:
            self.stdout.write(
                self.style.WARNING('⚠️  Duyuru bulunamadı')
            )
            return
        
        self.stdout.write(f'📊 {len(announcements)} duyuru bulundu')
        
        # Duyuruları işle
        imported_count = 0
        for announcement_data in announcements:
            try:
                # Mevcut haberi kontrol et
                if Haber.objects.filter(kaynak_url=announcement_data['url']).exists():
                    self.stdout.write(f'⏭️  Atlandı (mevcut): {announcement_data["title"][:50]}...')
                    continue
                
                if dry_run:
                    self.stdout.write(f'📝 Bulundu: {announcement_data["title"][:50]}...')
                    imported_count += 1
                    continue
                
                # Benzersiz slug oluştur
                base_slug = slugify(announcement_data['title'])
                slug = base_slug
                counter = 1
                while Haber.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Haberi oluştur
                haber = Haber.objects.create(
                    baslik=announcement_data['title'][:200],
                    slug=slug,
                    ozet=announcement_data['summary'][:500] if announcement_data['summary'] else announcement_data['title'][:500],
                    icerik=announcement_data['content'][:15000] if announcement_data['content'] else announcement_data['summary'],
                    kategori=kategori,
                    yazar=bot_user,
                    kaynak_url=announcement_data['url'],
                    federasyon_website=federation,
                    otomatik_eklendi=True,
                    yayinlandi=True,
                    olusturma_tarihi=announcement_data.get('date') or timezone.now()
                )
                
                imported_count += 1
                self.stdout.write(f'✅ Eklendi: {announcement_data["title"][:50]}...')
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Duyuru import hatası: {e}')
                )
                continue
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n🔍 DRY RUN TAMAMLANDI! '
                    f'{imported_count} duyuru bulundu.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 İŞLEM TAMAMLANDI! '
                    f'Toplam {imported_count} duyuru eklendi.'
                )
            )

    def _scrape_announcements(self, federation, limit):
        """Duyuruları çek"""
        announcements = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Duyurular sayfasını çek
            response = requests.get('https://twkf.gov.tr/tum-duyurular/', headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Duyuru öğelerini bul
            # Wushu sitesi genellikle .post veya article elementleri kullanır
            post_elements = soup.find_all(['article', '.post', '.et_pb_post'], limit=limit)
            
            if not post_elements:
                # Alternatif selektörler
                post_elements = soup.select('.et_pb_blog_grid .et_pb_post, .blog-posts .post, .news-item, .announcement-item')
            
            if not post_elements:
                # Tüm elementleri dene
                post_elements = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'post|article|announcement|duyuru', re.I))
            
            if not post_elements:
                # Son çare olarak tüm linkleri dene
                links = soup.find_all('a', href=re.compile(r'duyuru|announcement', re.I))
                for link in links[:limit]:
                    try:
                        title = link.get_text(strip=True)
                        href = link.get('href')
                        if href:
                            if href.startswith('http'):
                                full_url = href
                            elif href.startswith('/'):
                                full_url = f"https://twkf.gov.tr{href}"
                            else:
                                full_url = f"https://twkf.gov.tr/{href}"
                            
                            announcements.append({
                                'title': title,
                                'url': full_url,
                                'summary': title,
                                'content': title,
                                'date': None
                            })
                    except:
                        continue
            
            for post in post_elements:
                try:
                    # Başlık
                    title_element = post.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|baslik', re.I)) or \
                                   post.find(class_=re.compile(r'title|baslik', re.I)) or \
                                   post.find('a')
                    if not title_element:
                        continue
                        
                    title = title_element.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    # Link
                    link_element = post.find('a', href=True)
                    if not link_element:
                        continue
                        
                    href = link_element.get('href')
                    if not href:
                        continue
                    
                    # Tam URL oluştur
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"https://twkf.gov.tr{href}"
                    else:
                        full_url = f"https://twkf.gov.tr/{href}"
                    
                    # Özet
                    summary = ""
                    excerpt_element = post.find(class_=re.compile(r'excerpt|ozet|summary', re.I)) or \
                                    post.find('p')
                    if excerpt_element:
                        summary = excerpt_element.get_text(strip=True)
                    
                    # Tarih
                    date = None
                    date_element = post.find(class_=re.compile(r'date|tarih', re.I)) or \
                                  post.find(['time', 'span'], class_=re.compile(r'date|tarih', re.I))
                    if date_element:
                        date_text = date_element.get_text(strip=True)
                        # Basit tarih ayrıştırma
                        date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', date_text)
                        if date_match:
                            try:
                                day, month, year = map(int, date_match.groups())
                                from django.utils import timezone
                                from datetime import datetime
                                date = timezone.make_aware(datetime(year, month, day))
                            except:
                                pass
                    
                    announcements.append({
                        'title': title,
                        'url': full_url,
                        'summary': summary,
                        'content': summary,  # İçerik daha sonra detaylı çekilebilir
                        'date': date
                    })
                    
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Duyuru parse hatası: {e}')
                    continue
                    
        except Exception as e:
            self.stdout.write(f'   ❌ Duyuru çekme hatası: {e}')
            
        return announcements