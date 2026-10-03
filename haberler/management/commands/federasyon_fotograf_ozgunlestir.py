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
import re

class Command(BaseCommand):
    help = 'Federasyon fotoğraflarını telif hakkı sorunu olmayacak şekilde özgünleştir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='İşlenecek haber sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mevcut resimleri de değiştir'
        )
        parser.add_argument(
            '--style',
            type=str,
            choices=['artistic', 'news', 'modern', 'professional'],
            default='news',
            help='Dönüştürme stili'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        style = options['style']
        
        self.stdout.write('🎨 FEDERASYON FOTOĞRAFLARI ÖZGÜNLEŞTÜRME SİSTEMİ')
        self.stdout.write('=' * 60)
        
        # Kaynak URL'si olan haberleri bul
        queryset = Haber.objects.filter(
            kaynak_url__isnull=False,
            yayinlandi=True
        ).exclude(kaynak_url='')
        
        if not force:
            # Mevcut resmi olan haberler
            queryset = queryset.filter(resim__isnull=False)
        
        if limit > 0:
            queryset = queryset[:limit]
        
        haberler = list(queryset)
        
        if not haberler:
            self.stdout.write(
                self.style.WARNING('⚠️  İşlenecek haber bulunamadı.')
            )
            return
        
        self.stdout.write(f'🎯 {len(haberler)} haber için federasyon fotoğrafları özgünleştirilecek')
        self.stdout.write(f'🎭 Stil: {style.upper()}')
        
        success_count = 0
        failed_count = 0
        
        for i, haber in enumerate(haberler, 1):
            try:
                self.stdout.write(f'\n[{i}/{len(haberler)}] 📸 {haber.baslik[:50]}...')
                
                # Federasyon sitesinden orijinal resmi al
                original_image_url = self._get_federation_image(haber)
                
                if original_image_url:
                    # Resmi indir ve özgünleştir
                    transformed_image = self._transform_image(
                        original_image_url, haber, style
                    )
                    
                    if transformed_image:
                        # Eski resmi sil
                        if haber.resim:
                            haber.resim.delete(save=False)
                        
                        # Yeni özgünleştirilmiş resmi kaydet
                        haber.resim.save(transformed_image.name, transformed_image, save=True)
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✅ Özgünleştirildi: {transformed_image.name}')
                        )
                    else:
                        failed_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'   ⚠️  Dönüştürülemedi')
                        )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Federasyon resmi bulunamadı')
                    )
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! '
                f'✅ {success_count} başarılı, ⚠️ {failed_count} başarısız'
            )
        )

    def _get_federation_image(self, haber):
        """Federasyon sitesinden orijinal resim URL'sini al"""
        try:
            if not haber.kaynak_url:
                return None
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(haber.kaynak_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Karate.gov.tr özel selektörleri
            if 'karate.gov.tr' in haber.kaynak_url:
                image_selectors = [
                    'img.haber-detay-image',
                    '.haber-detay-image',
                    'img[src*="/uploads/haberler/"]',
                    'article img'
                ]
            else:
                # Genel federasyon siteleri
                image_selectors = [
                    'article img',
                    '.content img',
                    '.news-content img',
                    'main img'
                ]
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and self._is_valid_image(src):
                        # Tam URL oluştur
                        if src.startswith('http'):
                            return src
                        elif src.startswith('tema/') and 'karate.gov.tr' in haber.kaynak_url:
                            return f'https://karate.gov.tr/{src}'
                        else:
                            return urljoin(haber.kaynak_url, src)
            
            return None
            
        except Exception as e:
            self.stdout.write(f'   🔍 Resim arama hatası: {e}')
            return None

    def _is_valid_image(self, src):
        """Geçerli haber resmi olup olmadığını kontrol et"""
        src_lower = src.lower()
        
        # Atlanacak resimler
        skip_patterns = [
            'logo', 'icon', 'favicon', 'banner', 'header',
            'footer', 'social', 'share', 'avatar', 'profile',
            'arkaplan', 'yukleniyor', 'loading'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False
        
        # Geçerli formatlar
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        return any(ext in src_lower for ext in valid_extensions)

    def _transform_image(self, image_url, haber, style):
        """Orijinal resmi telif sorunu olmayacak şekilde dönüştür"""
        try:
            # Resmi indir
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': haber.kaynak_url
            }
            
            response = requests.get(image_url, headers=headers, timeout=30, verify=False)
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
            
            # Stile göre dönüştür
            try:
                transformed = self._apply_transformation_style(original_image, haber, style)
            except Exception as style_error:
                self.stdout.write(f'   🔧 Stil uygulama hatası: {style_error}')
                # If style application fails, use the original image with minimal transformation
                transformed = original_image
            
            # Dosya olarak kaydet
            output = io.BytesIO()
            transformed.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Dosya adı oluştur - Enhanced Turkish character fix
            safe_title = self._create_safe_filename(haber.baslik)
            unique_id = str(uuid.uuid4())[:8]
            filename = f"transformed_{style}_{safe_title}_{unique_id}.jpg"
            
            return ContentFile(output.read(), name=filename)
            
        except Exception as e:
            self.stdout.write(f'   🔧 Dönüştürme hatası: {e}')
            return None

    def _create_safe_filename(self, title):
        """Güvenli dosya adı oluştur"""
        if not title:
            return 'haber'
        
        # Django's slugify'a gönder
        safe_title = slugify(title)[:30]
        
        # If slugify fails or returns empty, create a fallback
        if not safe_title or safe_title.isspace():
            import re
            # Manual cleanup
            safe_title = re.sub(r'[^\w\s-]', '', title.lower())
            safe_title = re.sub(r'[\s_-]+', '-', safe_title)
            safe_title = safe_title[:30]
        
        # Final safety check
        if not safe_title:
            safe_title = 'haber'
        
        return safe_title

    def _apply_transformation_style(self, image, haber, style):
        """Seçilen stile göre resmi dönüştür"""
        if style == 'artistic':
            return self._artistic_transform(image, haber)
        elif style == 'modern':
            return self._modern_transform(image, haber)
        elif style == 'professional':
            return self._professional_transform(image, haber)
        else:  # news style
            return self._news_transform(image, haber)

    def _news_transform(self, image, haber):
        """Haber stili dönüştürme - profesyonel görünüm"""
        width, height = image.size
        
        # 1. Hafif renk filtreleri
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.95)  # Renkleri hafif azalt
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)  # Kontrastı artır
        
        # 2. Üst kısma haber başlığı overlay
        # Gradient overlay (üstten şeffaf siyah)
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Üst kısımda gradient
        for y in range(min(height // 3, 200)):
            alpha = int(120 * (1 - y / min(height // 3, 200)))
            overlay_draw.rectangle([0, y, width, y + 1], fill=(0, 0, 0, alpha))
        
        # Overlay'i uygula
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        
        # 3. Başlık metni ekle (güvenli şekilde)
        try:
            self._add_news_title(image, haber.baslik)
        except Exception as title_error:
            # Title overlay failed, skip it but continue with other transformations
            pass
        
        # 4. Alt sağ köşede kategori etiketi (güvenli şekilde)
        try:
            self._add_category_badge(image, haber.kategori.ad)
        except Exception as badge_error:
            # Badge failed, skip it but continue
            pass
        
        return image

    def _artistic_transform(self, image, haber):
        """Sanatsal dönüştürme - filtreler ve efektler"""
        # 1. Hafif blur efekti
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # 2. Renk efektleri
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.2)  # Renkleri artır
        
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.05)  # Parlaklığı artır
        
        # 3. Vintage efekt
        width, height = image.size
        vintage_overlay = Image.new('RGBA', (width, height), (255, 204, 153, 30))
        image = Image.alpha_composite(image.convert('RGBA'), vintage_overlay).convert('RGB')
        
        # 4. Çerçeve efekti
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, width-1, height-1], outline=(200, 200, 200), width=3)
        draw.rectangle([5, 5, width-6, height-6], outline=(255, 255, 255), width=2)
        
        return image

    def _modern_transform(self, image, haber):
        """Modern dönüştürme - geometrik şekiller ve temiz tasarım"""
        width, height = image.size
        
        # 1. Sharpening
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
        
        # 2. Geometrik overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Sol üst köşede renkli geometrik şekil
        theme_color = self._get_category_color(haber.kategori.ad.lower())
        overlay_draw.polygon([
            (0, 0), (200, 0), (150, 100), (0, 80)
        ], fill=(*theme_color, 180))
        
        # Overlay'i uygula
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        
        return image

    def _professional_transform(self, image, haber):
        """Profesyonel dönüştürme - kurumsal görünüm"""
        width, height = image.size
        
        # 1. Renk düzeltmeleri
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.08)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        # 2. Alt kısımda bilgi bandı
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Alt kısımda şeffaf siyah bant
        band_height = 80
        overlay_draw.rectangle([0, height-band_height, width, height], 
                              fill=(0, 0, 0, 180))
        
        # Üst kısımda ince bant
        overlay_draw.rectangle([0, 0, width, 5], 
                              fill=(*self._get_category_color(haber.kategori.ad.lower()), 255))
        
        # Overlay'i uygula
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        
        return image

    def _add_news_title(self, image, title):
        """Haber stilinde başlık ekle"""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Clean the title to handle Turkish characters safely
        safe_title = self._clean_text_for_image(title)
        
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 36)
        except:
            font = ImageFont.load_default()
        
        # Metni böl
        words = safe_title.split()
        lines = []
        current_line = ''
        
        for word in words:
            test_line = current_line + ' ' + word if current_line else word
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] <= width - 40:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            except:
                # Skip problematic text
                continue
        
        if current_line:
            lines.append(current_line)
        
        # Sadece ilk 2 satırı göster
        lines = lines[:2]
        
        # Metni çiz
        y = 20
        for line in lines:
            try:
                # Gölge
                draw.text((21, y+1), line, fill=(0, 0, 0, 200), font=font)
                # Ana metin
                draw.text((20, y), line, fill=(255, 255, 255), font=font)
                y += 45
            except:
                # Skip if we can't render the text
                continue

    def _add_category_badge(self, image, category):
        """Kategori etiketi ekle"""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Clean the category text to handle Turkish characters safely
        safe_category = self._clean_text_for_image(category)
        
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
        except:
            font = ImageFont.load_default()
        
        # Kategori metni
        badge_text = safe_category.upper()
        try:
            bbox = draw.textbbox((0, 0), badge_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Etiket boyutları
            padding = 10
            badge_width = text_width + padding * 2
            badge_height = text_height + padding
            
            # Etiket pozisyonu (sağ alt)
            x = width - badge_width - 20
            y = height - badge_height - 20
            
            # Etiket arkaplanı
            color = self._get_category_color(category.lower())
            draw.rectangle([x, y, x + badge_width, y + badge_height], 
                          fill=color, outline=(255, 255, 255), width=2)
            
            # Etiket metni
            text_x = x + padding
            text_y = y + padding // 2
            draw.text((text_x, text_y), badge_text, fill=(255, 255, 255), font=font)
        except:
            # Skip if we can't render the badge
            pass

    def _clean_text_for_image(self, text):
        """Metni resim için güvenli hale getir"""
        if not text:
            return ""
        
        # Turkish characters that cause issues with image rendering
        turkish_chars = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ş': 's', 'ü': 'u', 'ö': 'o',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ş': 'S', 'Ü': 'U', 'Ö': 'O',
            'â': 'a', 'î': 'i', 'û': 'u', 'Â': 'A', 'Î': 'I', 'Û': 'U'
        }
        
        safe_text = text
        for turkish, latin in turkish_chars.items():
            safe_text = safe_text.replace(turkish, latin)
        
        # Remove any remaining non-ASCII characters
        safe_text = ''.join(c for c in safe_text if ord(c) < 128)
        
        return safe_text

    def _get_category_color(self, category):
        """Kategoriye göre renk döndür"""
        colors = {
            'karate': (255, 87, 51),     # Orange
            'judo': (74, 144, 226),      # Blue
            'taekwondo': (231, 76, 60),  # Red
            'kickboks': (46, 204, 113),  # Green
            'mma': (52, 73, 94),         # Dark blue
            'muay thai': (155, 89, 182)  # Purple
        }
        return colors.get(category, (52, 152, 219))  # Default blue