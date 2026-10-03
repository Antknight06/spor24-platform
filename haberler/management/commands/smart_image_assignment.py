from django.core.management.base import BaseCommand
from haberler.models import Haber
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from django.core.files.base import ContentFile
import io
import requests
from urllib.parse import urljoin
import uuid
from django.utils.text import slugify
import random
import os

class Command(BaseCommand):
    help = 'Akilli resim atama: Gercek fotograflari modifiye et, bulamayanlar icin telif-free olustur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Islenecek haber sayisi (varsayilan: 20)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mevcut resimleri de yeniden isle'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        
        self.stdout.write('🧠 AKILLI RESIM ATAMA SISTEMI')
        self.stdout.write('=' * 60)
        
        # Haberleri belirle
        queryset = Haber.objects.filter(
            yayinlandi=True,
            kaynak_url__isnull=False
        ).exclude(kaynak_url='')
        
        if not force:
            # Sadece transformed_ veya copyright_free_ ile başlayanları işle
            processed_haberler = []
            for haber in queryset:
                if haber.resim:
                    image_name = os.path.basename(haber.resim.name)
                    if (image_name.startswith('transformed_') or 
                        image_name.startswith('copyright_free_') or
                        not haber.resim):
                        processed_haberler.append(haber)
                else:
                    processed_haberler.append(haber)
            queryset = processed_haberler
        
        if limit > 0:
            queryset = queryset[:limit]
        
        if not queryset:
            self.stdout.write(
                self.style.WARNING('⚠️  İşlenecek haber bulunamadı.')
            )
            return
        
        self.stdout.write(f'🎯 {len(queryset)} haber için akıllı resim ataması yapılacak')
        
        photo_modified_count = 0
        generated_count = 0
        failed_count = 0
        
        for i, haber in enumerate(queryset, 1):
            try:
                self.stdout.write(f'\\n[{i}/{len(queryset)}] 📸 {haber.baslik[:50]}...')
                
                # Önce gerçek fotoğraf bulmaya çalış
                real_photo_url = self._find_real_photo(haber)
                
                if real_photo_url:
                    # Gerçek fotoğrafı modifiye et
                    modified_image = self._create_modified_real_photo(haber, real_photo_url)
                    
                    if modified_image:
                        # Eski resmi sil
                        if haber.resim:
                            haber.resim.delete(save=False)
                        
                        # Yeni modifiye edilmiş resmi kaydet
                        haber.resim.save(modified_image.name, modified_image, save=True)
                        photo_modified_count += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✅ Gerçek fotoğraf modifiye edildi: {modified_image.name}')
                        )
                    else:
                        # Gerçek fotoğraf işlenemediyse, telif-free oluştur
                        generated_image = self._create_copyright_free_image(haber)
                        if generated_image:
                            if haber.resim:
                                haber.resim.delete(save=False)
                            haber.resim.save(generated_image.name, generated_image, save=True)
                            generated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'   🎨 Fotoğraf işlenemedi, telif-free oluşturuldu: {generated_image.name}')
                            )
                        else:
                            failed_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'   ❌ Hiçbir resim oluşturulamadı')
                            )
                else:
                    # Gerçek fotoğraf bulunamadı, telif-free oluştur
                    generated_image = self._create_copyright_free_image(haber)
                    
                    if generated_image:
                        if haber.resim:
                            haber.resim.delete(save=False)
                        haber.resim.save(generated_image.name, generated_image, save=True)
                        generated_count += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'   🎨 Fotoğraf bulunamadı, telif-free oluşturuldu: {generated_image.name}')
                        )
                    else:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Resim oluşturulamadı')
                        )
                        
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\\n🎉 İşlem tamamlandı!\\n'
                f'   📸 {photo_modified_count} gerçek fotoğraf modifiye edildi\\n'
                f'   🎨 {generated_count} telif-free resim oluşturuldu\\n'
                f'   ❌ {failed_count} başarısız'
            )
        )

    def _find_real_photo(self, haber):
        # Haberin gercek fotografini bulmaya calis
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(haber.kaynak_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Script ve style elementlerini kaldır
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Ana resim selektörleri - daha geniş arama
            image_selectors = [
                # Haber detay resimleri
                'img.haber-detay-image',
                '.haber-detay-image',
                'img[src*="/uploads/haberler/"]',
                'img[src*="/tema/"]',
                'img[src*="/images/"]',
                'img[src*="/foto/"]',
                'img[src*="/galeri/"]',
                
                # Genel içerik resimleri
                'article img',
                '.content img',
                'main img',
                '.news-content img',
                '.post-content img',
                '.entry-content img',
                '.article-body img',
                '.news-detail img',
                '.haber-icerik img',
                
                # Alt attribute'a göre
                'img[alt*="haber"]',
                'img[alt*="foto"]',
                'img[alt*="resim"]',
                'img[alt*="eray"]',
                'img[alt*="şamdan"]',
                'img[alt*="samdan"]',
                'img[alt*="sporcu"]',
                'img[alt*="şampiyon"]',
                
                # Src attribute'a göre geniş arama
                'img[src*="haber"]',
                'img[src*="news"]',
                'img[src*="photo"]',
                'img[src*="picture"]',
                'img[src*="img"]',
                
                # Tüm img elementleri (son çare)
                'img'
            ]
            
            # Tüm resimleri topla ve değerlendir
            candidate_images = []
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    alt = img.get('alt', '').lower()
                    
                    if src and self._is_valid_news_image(src, alt, haber.baslik):
                        # Tam URL oluştur
                        full_url = self._build_full_image_url(src, haber.kaynak_url)
                        if full_url:
                            # Öncelik puanı hesapla
                            priority = self._calculate_image_priority(src, alt, haber.baslik)
                            candidate_images.append((full_url, priority))
            
            # En yüksek öncelikli resmi döndür
            if candidate_images:
                candidate_images.sort(key=lambda x: x[1], reverse=True)
                return candidate_images[0][0]
            
            return None
            
        except Exception as e:
            self.stdout.write(f'   🔍 Fotoğraf arama hatası: {e}')
            return None

    def _calculate_image_priority(self, src, alt, title):
        # Resim onceligi hesapla
        priority = 0
        src_lower = src.lower()
        alt_lower = alt.lower()
        title_lower = title.lower()
        
        # Dosya boyutu göstergeleri (büyük resimler daha iyi)
        if any(size in src_lower for size in ['large', 'big', 'full', 'original']):
            priority += 30
        
        # Kalite göstergeleri
        if any(qual in src_lower for qual in ['hd', 'high', 'quality']):
            priority += 25
        
        # Kişi isimleri (özellikle Eray Şamdan) - Çok yüksek öncelik
        if any(name in title_lower for name in ['eray', 'şamdan', 'samdan']):
            priority += 100  # Çok yüksek öncelik
            # Eğer resim kaynağında da kişi adı geçiyorsa daha da yüksek
            if any(name in src_lower for name in ['eray', 'şamdan', 'samdan']):
                priority += 50
        if any(name in alt_lower for name in ['eray', 'şamdan', 'samdan']):
            priority += 80
        
        # Diğer önemli kişiler
        important_people = ['ercument', 'taşdemir', 'tasdemir', 'osman', 'aşkın', 'bak']
        for person in important_people:
            if person in title_lower:
                priority += 60
            if person in alt_lower:
                priority += 50
            if person in src_lower:
                priority += 30
        
        # Spor terimleri
        sport_terms = ['karate', 'judo', 'taekwondo', 'kickboks', 'mma', 'muay thai', 'sporcu', 'şampiyon']
        for term in sport_terms:
            if term in title_lower:
                priority += 20
            if term in alt_lower:
                priority += 15
        
        # Resim formatı (jpeg daha iyi)
        if src_lower.endswith(('.jpg', '.jpeg')):
            priority += 10
        elif src_lower.endswith('.png'):
            priority += 5
        
        # Federasyon siteleri güvenilir
        if any(fed in src_lower for fed in ['tkd', 'karate', 'judo', 'federasyon']):
            priority += 35
        
        # Fotoğraf dosya yolu göstergeleri
        if any(path in src_lower for path in ['/foto', '/image', '/resim', '/galeri']):
            priority += 25
        
        # Haber resimleri
        if any(news in src_lower for news in ['/haber', '/news', 'upload']):
            priority += 20
        
        return priority

    def _build_full_image_url(self, src, base_url):
        # Tam resim URL'si olustur
        try:
            if src.startswith('http'):
                return src
            elif src.startswith('//'):
                return 'https:' + src
            elif src.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                return f"{parsed.scheme}://{parsed.netloc}{src}"
            else:
                return urljoin(base_url, src)
        except:
            return None

    def _is_valid_news_image(self, src, alt, title):
        # Gecerli haber resmi mi kontrol et
        src_lower = src.lower()
        alt_lower = alt.lower()
        
        # Atlanacak resimler
        skip_patterns = [
            'logo', 'icon', 'favicon', 'banner', 'header',
            'footer', 'social', 'share', 'avatar', 'profile',
            'advertisement', 'ads', 'sponsor', 'arkaplan',
            'yukleniyor', 'loading', 'default', 'placeholder'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower or pattern in alt_lower:
                return False
        
        # Çok küçük resimler
        if any(size in src_lower for size in ['thumb', 'small', '50x', '100x']):
            return False
        
        # Geçerli resim formatları
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not any(ext in src_lower for ext in valid_extensions):
            return False
        
        # En az 200px boyutunda olmalı (URL'den tahmin)
        if any(size in src_lower for size in ['150x', '100x', '50x']):
            return False
        
        return True



    def _create_modified_real_photo(self, haber, photo_url):
        # Gercek fotografi 2 detay degistirerek modifiye et
        try:
            # Fotoğrafı indir
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': haber.kaynak_url
            }
            
            response = requests.get(photo_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            # PIL ile aç
            original_image = Image.open(io.BytesIO(response.content))
            
            # RGB'ye çevir
            if original_image.mode in ('RGBA', 'P', 'L'):
                original_image = original_image.convert('RGB')
            
            # Boyutu optimize et
            max_width = 1200
            if original_image.width > max_width:
                ratio = max_width / original_image.width
                new_height = int(original_image.height * ratio)
                original_image = original_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # 2 detay değişikliği uygula
            modified_image = self._apply_two_detail_changes(original_image, haber)
            
            # Dosya olarak kaydet
            output = io.BytesIO()
            modified_image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Dosya adı oluştur
            safe_title = self._create_safe_filename(haber.baslik)
            unique_id = str(uuid.uuid4())[:8]
            filename = f"real_modified_{safe_title}_{unique_id}.jpg"
            
            return ContentFile(output.read(), name=filename)
            
        except Exception as e:
            self.stdout.write(f'   🔧 Fotoğraf modifikasyon hatası: {e}')
            return None

    def _apply_two_detail_changes(self, image, haber):
        # Fotografia 2 detay degisikligi uygula (telif hakki icin)
        width, height = image.size
        
        # Değişiklik 1: Hafif renk filtresi ve kontrast ayarı
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.05)  # Renkleri hafif artır
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.08)  # Kontrastı artır
        
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.02)  # Parlaklığı hafif artır
        
        # Değişiklik 2: Subtle vignette effect (köşeleri hafif koyulaştır)
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Köşelerde vignette efekti
        center_x, center_y = width // 2, height // 2
        max_distance = ((width/2)**2 + (height/2)**2)**0.5
        
        for x in range(0, width, 20):  # Performance için her 20 pixel
            for y in range(0, height, 20):
                distance = ((x - center_x)**2 + (y - center_y)**2)**0.5
                if distance > max_distance * 0.6:  # Sadece kenar bölgelerde
                    alpha = int((distance / max_distance - 0.6) * 60)
                    alpha = min(alpha, 30)  # Maksimum %12 koyulaştırma
                    overlay_draw.ellipse([x-10, y-10, x+10, y+10], fill=(0, 0, 0, alpha))
        
        # Overlay'i uygula
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        
        return image

    def _create_copyright_free_image(self, haber):
        # Telif sorunu olmayan ozgun resim olustur
        try:
            # Resim boyutları
            width, height = 800, 400
            
            # Kategori rengi al
            kategori_rengi = self._get_category_color(haber.kategori.ad.lower() if haber.kategori else 'default')
            
            # Gradient arka plan oluştur
            image = Image.new('RGB', (width, height), kategori_rengi)
            
            # Gradient efekti
            for y in range(height):
                # Üstten alta gradient
                alpha = 1.0 - (y / height) * 0.3
                current_color = tuple(int(c * alpha) for c in kategori_rengi)
                
                draw_line = ImageDraw.Draw(image)
                draw_line.line([(0, y), (width, y)], fill=current_color)
            
            # Çizim nesnesi
            draw = ImageDraw.Draw(image)
            
            # Dekoratif şekiller ekle
            self._add_decorative_shapes(draw, width, height, kategori_rengi)
            
            # Başlık ekle
            self._add_title_text(draw, haber.baslik, width, height)
            
            # Kategori etiketi
            if haber.kategori:
                self._add_category_badge(draw, haber.kategori.ad, width, height)
            
            # Dosya olarak kaydet
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Güvenli dosya adı oluştur
            safe_title = self._create_safe_filename(haber.baslik)
            unique_id = str(uuid.uuid4())[:8]
            filename = f"smart_generated_{safe_title}_{unique_id}.jpg"
            
            return ContentFile(output.read(), name=filename)
            
        except Exception as e:
            self.stdout.write(f'   🔧 Resim oluşturma hatası: {e}')
            return None

    def _get_category_color(self, category):
        # Kategoriye gore renk dondur
        colors = {
            'karate': (41, 128, 185),      # Mavi
            'judo': (46, 204, 113),        # Yeşil
            'taekwondo': (231, 76, 60),    # Kırmızı
            'kickboks': (142, 68, 173),    # Mor
            'mma': (52, 73, 94),           # Koyu Gri
            'muay thai': (230, 126, 34)    # Turuncu
        }
        return colors.get(category, (52, 152, 219))  # Varsayılan mavi

    def _add_decorative_shapes(self, draw, width, height, color):
        # Dekoratif sekiller ekle
        # Solda büyük daire
        circle_color = tuple(min(255, c + 30) for c in color)
        draw.ellipse([width-150, height-150, width+50, height+50], fill=circle_color)
        
        # Üstte küçük daireler
        small_color = tuple(min(255, c + 20) for c in color)
        draw.ellipse([50, 30, 100, 80], fill=small_color)
        draw.ellipse([150, 20, 190, 60], fill=small_color)

    def _add_title_text(self, draw, title, width, height):
        # Baslik metni ekle
        try:
            # Font yükle
            try:
                font_large = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 32)
                font_small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Metni temizle ve böl
            clean_title = self._clean_text_for_display(title)
            words = clean_title.split()
            
            lines = []
            current_line = ''
            
            for word in words:
                test_line = current_line + ' ' + word if current_line else word
                # Yaklaşık genişlik kontrolü
                if len(test_line) <= 35:  # Karakter sayısına göre kontrol
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Sadece ilk 3 satırı göster
            lines = lines[:3]
            
            # Metni çiz
            y_start = 80
            for i, line in enumerate(lines):
                font = font_large if i == 0 else font_small
                # Gölge
                draw.text((21, y_start + i * 40 + 1), line, fill=(0, 0, 0, 200), font=font)
                # Ana metin
                draw.text((20, y_start + i * 40), line, fill=(255, 255, 255), font=font)
                
        except Exception as e:
            # Metin ekleme başarısız olursa devam et
            pass

    def _add_category_badge(self, draw, category, width, height):
        # Kategori etiketi ekle
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
        except:
            font = ImageFont.load_default()
        
        badge_text = category.upper()
        
        # Etiket boyutları (yaklaşık)
        text_width = len(badge_text) * 10
        text_height = 20
        padding = 8
        
        badge_width = text_width + padding * 2
        badge_height = text_height + padding
        
        # Sağ üst köşe
        x = width - badge_width - 20
        y = 20
        
        # Etiket arkaplanı
        draw.rectangle([x, y, x + badge_width, y + badge_height], 
                      fill=(255, 255, 255, 200), outline=(200, 200, 200))
        
        # Etiket metni
        text_x = x + padding
        text_y = y + padding // 2
        draw.text((text_x, text_y), badge_text, fill=(50, 50, 50), font=font)

    def _clean_text_for_display(self, text):
        # Görüntüleme için metni temizle
        if not text:
            return ""
        
        # Türkçe karakterleri korunacak şekilde temizle
        # Sadece aşırı uzun kısımları kısalt
        if len(text) > 100:
            text = text[:100] + "..."
        
        return text

    def _create_safe_filename(self, title):
        # Güvenli dosya adı oluştur
        if not title:
            return 'haber'
        
        # Django's slugify kullan
        safe_title = slugify(title)[:30]
        
        # Eğer slugify başarısız olursa fallback
        if not safe_title:
            import re
            safe_title = re.sub(r'[^\w\s-]', '', title.lower())
            safe_title = re.sub(r'[\s_-]+', '-', safe_title)
            safe_title = safe_title[:30]
        
        return safe_title if safe_title else 'haber'