from django.core.management.base import BaseCommand
from django.db import transaction
from haberler.models import Haber, Kategori, FederasyonWebsite
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from django.core.files.base import ContentFile
import io
from PIL import Image
import uuid
import time
import re

class Command(BaseCommand):
    help = 'Karate haberlerini sil ve baştan fotoğraflarıyla beraber yükle (modifikasyon yapmadan)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=30,
            help='Yüklenecek haber sayısı (varsayılan: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece analiz yap, değişiklik yapma'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write('🥋 KARATE HABERLERİNİ YENİDEN YÜKLEME SİSTEMİ')
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 DRY RUN MODU - Değişiklik yapılmayacak'))
        
        # Adım 1: Mevcut karate haberlerini sil
        self._remove_existing_karate_news(dry_run)
        
        # Adım 2: Yeni haberleri çek ve yükle
        if not dry_run:
            self._import_fresh_karate_news(limit)
        else:
            self.stdout.write(f'\n📥 DRY RUN: {limit} haber çekilecek')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 İşlem tamamlandı!'))

    def _remove_existing_karate_news(self, dry_run):
        """Mevcut karate haberlerini sil"""
        self.stdout.write('\n🗑️  MEVCUT KARATE HABERLERİNİ SİLME')
        self.stdout.write('-' * 40)
        
        # Karate ile ilgili tüm haberleri bul
        karate_categories = Kategori.objects.filter(ad__icontains='Karate')
        karate_news_by_category = []
        
        for cat in karate_categories:
            news = list(Haber.objects.filter(kategori=cat))
            karate_news_by_category.extend(news)
        
        # Başlıkta 'karate' geçen haberler
        karate_news_by_title = list(Haber.objects.filter(baslik__icontains='karate'))
        
        # karate.gov.tr'den gelen haberler
        karate_news_by_source = list(Haber.objects.filter(kaynak_url__icontains='karate.gov.tr'))
        
        # Tekrarları kaldır
        all_karate_news = list(set(karate_news_by_category + karate_news_by_title + karate_news_by_source))
        
        self.stdout.write(f'📊 Silinecek karate haberi: {len(all_karate_news)}')
        
        if dry_run:
            for news in all_karate_news[:5]:  # İlk 5'ini göster
                self.stdout.write(f'   🗑️  {news.baslik[:50]}...')
            if len(all_karate_news) > 5:
                self.stdout.write(f'   ... ve {len(all_karate_news) - 5} haber daha')
            return
        
        # Gerçek silme işlemi
        removed_count = 0
        for news in all_karate_news:
            try:
                news_title = news.baslik[:50]
                news_id = news.id
                
                # Resim dosyasını sil
                if news.resim:
                    try:
                        news.resim.delete(save=False)
                        self.stdout.write(f'   🖼️  Resim silindi: {news.resim.name}')
                    except Exception as e:
                        self.stdout.write(f'   ⚠️  Resim silinemedi: {e}')
                
                # Haberi sil
                news.delete()
                self.stdout.write(f'   ✅ Silindi: {news_title}... (ID: {news_id})')
                removed_count += 1
                
            except Exception as e:
                self.stdout.write(f'   ❌ Hata: {news.id}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'🎉 {removed_count} karate haberi silindi'))

    def _import_fresh_karate_news(self, limit):
        """Yeni karate haberlerini çek ve yükle"""
        self.stdout.write('\n📥 YENİ KARATE HABERLERİNİ YÜKLEME')
        self.stdout.write('-' * 40)
        
        # Federasyon ve kategori hazırlığı
        federation, kategori = self._setup_karate_federation()
        
        # Bot kullanıcı
        bot_user = self._get_or_create_bot_user()
        
        # Haberleri çek
        news_data = self._scrape_karate_news(limit)
        
        self.stdout.write(f'📊 {len(news_data)} haber bulundu, içe aktarılıyor...')
        
        imported_count = 0
        for i, news_item in enumerate(news_data, 1):
            try:
                self.stdout.write(f'\n[{i}/{len(news_data)}] 📰 {news_item["title"][:50]}...')
                
                # Haber zaten var mı kontrol et
                if Haber.objects.filter(kaynak_url=news_item['url']).exists():
                    self.stdout.write('   ⚠️  Zaten mevcut, atlanıyor')
                    continue
                
                # Haberi oluştur
                haber = self._create_news_article(news_item, kategori, bot_user)
                
                if haber:
                    # Orijinal fotoğrafı indir ve ekle
                    self._download_original_photo(haber, news_item['url'])
                    imported_count += 1
                    self.stdout.write(f'   ✅ İçe aktarıldı: {haber.slug}')
                else:
                    self.stdout.write('   ❌ Oluşturulamadı')
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(f'   ❌ Hata: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 {imported_count} karate haberi başarıyla yüklendi!'))

    def _setup_karate_federation(self):
        """Karate federasyon ve kategori kurulumu"""
        # Federasyon al/oluştur
        federation, created = FederasyonWebsite.objects.get_or_create(
            ana_url='https://karate.gov.tr',
            defaults={
                'ad': 'Türkiye Karate Federasyonu (Resmi)',
                'haberler_url': 'https://karate.gov.tr/haber-kategori/federasyon',
                'haber_listesi_selector': '.row .col-md-4',
                'haber_baslik_selector': 'h3, h4',
                'haber_link_selector': 'a',
                'aktif': True
            }
        )
        
        # Kategori al/oluştur
        kategori, created = Kategori.objects.get_or_create(
            slug='karate',
            defaults={
                'ad': 'Karate',
                'aciklama': 'Karate haberleri ve duyuruları',
                'federasyon_website': federation
            }
        )
        
        return federation, kategori

    def _get_or_create_bot_user(self):
        """Bot kullanıcı al/oluştur"""
        bot_user, created = User.objects.get_or_create(
            username='karatebot',
            defaults={
                'email': 'karatebot@netspor.com',
                'first_name': 'Karate',
                'last_name': 'Bot',
                'is_active': True
            }
        )
        return bot_user

    def _scrape_karate_news(self, limit):
        """karate.gov.tr'den haberleri çek"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            base_url = 'https://karate.gov.tr/haber-kategori/federasyon'
            response = requests.get(base_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            
            # Haber listesi bulma
            articles = soup.select('.row .col-md-4')[:limit]
            
            for article in articles:
                try:
                    # Başlık ve link
                    title_elem = article.select_one('h3, h4, .title')
                    link_elem = article.select_one('a')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    href = link_elem.get('href')
                    
                    if not href:
                        continue
                    
                    # Tam URL oluştur
                    if href.startswith('/haber/'):
                        url = f'https://karate.gov.tr{href}'
                    elif href.startswith('haber/'):
                        url = f'https://karate.gov.tr/{href}'
                    elif href.startswith('/'):
                        url = f'https://karate.gov.tr{href}'
                    elif href.startswith('http'):
                        url = href
                    else:
                        url = f'https://karate.gov.tr/haber/{href}'
                    
                    # Tarih
                    date_elem = article.select_one('.date, .tarih, time')
                    date_text = date_elem.get_text(strip=True) if date_elem else None
                    
                    # Özet
                    summary_elem = article.select_one('.excerpt, .ozet, p')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ''
                    
                    news_items.append({
                        'title': title,
                        'url': url,
                        'date': date_text,
                        'summary': summary[:200] if summary else title[:100]
                    })
                    
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Haber parse hatası: {e}')
                    continue
            
            return news_items
            
        except Exception as e:
            self.stdout.write(f'❌ Scraping hatası: {e}')
            return []

    def _create_news_article(self, news_item, kategori, bot_user):
        """Haber makalesini oluştur"""
        try:
            # Detay sayfasından içeriği çek
            content = self._scrape_news_content(news_item['url'])
            
            # Slug oluştur
            base_slug = slugify(news_item['title'])
            slug = base_slug
            counter = 1
            while Haber.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Haberi oluştur
            haber = Haber.objects.create(
                baslik=news_item['title'],
                slug=slug,
                ozet=news_item['summary'],
                icerik=content,
                kategori=kategori,
                yazar=bot_user,
                kaynak_url=news_item['url'],
                yayinlandi=True,
                olusturma_tarihi=timezone.now(),
                guncelleme_tarihi=timezone.now()
            )
            
            return haber
            
        except Exception as e:
            self.stdout.write(f'   ❌ Haber oluşturma hatası: {e}')
            return None

    def _scrape_news_content(self, url):
        """Haber detay sayfasından içeriği çek"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # İçerik selektörleri
            content_selectors = [
                '.news-detail-content',
                '.haber-detay-icerik',
                '.content',
                '.article-body',
                '.post-content',
                'main .container',
                '.row .col-md-8'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Script ve style elementlerini temizle
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    
                    content = content_elem.get_text(separator='\n', strip=True)
                    break
            
            # İçeriği temizle
            content = self._clean_content(content)
            
            return content if content else "İçerik yüklenirken bir hata oluştu."
            
        except Exception as e:
            return f"İçerik çekilemedi: {str(e)}"

    def _clean_content(self, content):
        """İçeriği temizle"""
        if not content:
            return ""
        
        # Navigasyon metinlerini temizle
        navigation_patterns = [
            r'ANASAYFA.*?İLETİŞİM',
            r'TKF MENÜ.*?İletişim Formu',
            r'SOSYAL MEDYA.*?Formu',
            r'Karate-Do Nedir\?.*?Vizyonumuz',
            r'KULÜP BİLGİ SİSTEMİ.*?İLETİŞİM'
        ]
        
        for pattern in navigation_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Gereksiz boşlukları temizle
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        content = content.strip()
        
        return content

    def _download_original_photo(self, haber, source_url):
        """Orijinal fotoğrafı indir ve ekle (modifikasyon yapmadan)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': source_url
            }
            
            response = requests.get(source_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Fotoğraf selektörleri
            image_selectors = [
                'img.haber-detay-image',
                '.news-detail img',
                '.haber-detay img',
                '.content img',
                'article img',
                'main img'
            ]
            
            image_url = None
            for selector in image_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src and self._is_valid_image(src):
                        # Tam URL oluştur
                        if src.startswith('/'):
                            image_url = f'https://karate.gov.tr{src}'
                        elif src.startswith('//'):
                            image_url = f'https:{src}'
                        elif src.startswith('http'):
                            image_url = src
                        else:
                            image_url = urljoin(source_url, src)
                        break
            
            if image_url:
                # Resmi indir
                img_response = requests.get(image_url, headers=headers, timeout=30, verify=False)
                img_response.raise_for_status()
                
                # PIL ile aç ve optimizasyon yap
                image = Image.open(io.BytesIO(img_response.content))
                
                # RGB'ye çevir
                if image.mode in ('RGBA', 'P', 'L'):
                    image = image.convert('RGB')
                
                # Boyut optimizasyonu
                max_width = 1200
                if image.width > max_width:
                    ratio = max_width / image.width
                    new_height = int(image.height * ratio)
                    image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Kaydet
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=90, optimize=True)
                output.seek(0)
                
                # Dosya adı oluştur
                safe_title = slugify(haber.baslik)[:30]
                unique_id = str(uuid.uuid4())[:8]
                filename = f"karate_original_{safe_title}_{unique_id}.jpg"
                
                # Habere ekle
                haber.resim.save(filename, ContentFile(output.read()), save=True)
                
                self.stdout.write(f'   📸 Orijinal fotoğraf eklendi: {filename}')
                return True
            else:
                self.stdout.write('   📷 Fotoğraf bulunamadı')
                return False
                
        except Exception as e:
            self.stdout.write(f'   ❌ Fotoğraf indirme hatası: {e}')
            return False

    def _is_valid_image(self, src):
        """Geçerli resim URL'si mi kontrol et"""
        if not src:
            return False
        
        src_lower = src.lower()
        
        # Atlanacak resimler
        skip_patterns = ['logo', 'icon', 'favicon', 'banner', 'default', 'placeholder']
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False
        
        # Geçerli formatlar
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        return any(ext in src_lower for ext in valid_extensions)