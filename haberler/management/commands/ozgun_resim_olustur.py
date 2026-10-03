from django.core.management.base import BaseCommand
from haberler.models import Haber
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
import io
import random
import os
from django.utils.text import slugify
import uuid

class Command(BaseCommand):
    help = 'Telif hakkı sorunu yaşamayacak özgün haberler için resimler oluştur'

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
            '--category',
            type=str,
            help='Sadece belirtilen kategori haberleri (örn: karate, judo)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        category = options.get('category')
        
        self.stdout.write('🎨 ÖZGÜN RESİM OLUŞTURMA SİSTEMİ')
        self.stdout.write('=' * 50)
        
        # Hangi haberleri işleyeceğimizi belirle
        queryset = Haber.objects.filter(yayinlandi=True)
        
        if category:
            queryset = queryset.filter(kategori__slug__icontains=category)
        
        if not force:
            queryset = queryset.filter(resim__isnull=True)
        
        if limit > 0:
            queryset = queryset[:limit]
        
        haberler = list(queryset)
        
        if not haberler:
            self.stdout.write(
                self.style.WARNING('⚠️  İşlenecek haber bulunamadı.')
            )
            return
        
        self.stdout.write(f'🎯 {len(haberler)} haber için özgün resim oluşturulacak')
        
        success_count = 0
        failed_count = 0
        
        for i, haber in enumerate(haberler, 1):
            try:
                self.stdout.write(f'\n[{i}/{len(haberler)}] 🖼️  {haber.baslik[:50]}...')
                
                # Haberin kategorisine göre resim oluştur
                image_file = self._create_original_image(haber)
                
                if image_file:
                    # Eski resmi sil
                    if haber.resim:
                        haber.resim.delete(save=False)
                    
                    # Yeni resmi kaydet
                    haber.resim.save(image_file.name, image_file, save=True)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Özgün resim oluşturuldu: {image_file.name}')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Resim oluşturulamadı')
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

    def _create_original_image(self, haber):
        """Haber için özgün resim oluştur"""
        try:
            # Resim boyutları
            width, height = 1200, 630  # Social media optimal size
            
            # Kategoriye göre tema belirle
            theme = self._get_theme_by_category(haber.kategori.ad.lower())
            
            # Gradient arkaplan oluştur
            image = self._create_gradient_background(width, height, theme['colors'])
            
            # Text overlay ekle
            image = self._add_text_overlay(image, haber.baslik, theme)
            
            # Kategori iconunu ekle
            image = self._add_category_icon(image, haber.kategori.ad.lower(), theme)
            
            # Dekoratif öğeler ekle
            image = self._add_decorative_elements(image, theme)
            
            # Resmi kaydet
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Dosya adı oluştur
            safe_title = slugify(haber.baslik)[:30]
            unique_id = str(uuid.uuid4())[:8]
            filename = f"original_{safe_title}_{unique_id}.jpg"
            
            return ContentFile(output.read(), name=filename)
            
        except Exception as e:
            self.stdout.write(f'Resim oluşturma hatası: {e}')
            return None

    def _get_theme_by_category(self, category):
        """Kategoriye göre tema renkleri ve stilini belirle"""
        themes = {
            'karate': {
                'colors': [(255, 87, 51), (255, 154, 0)],  # Orange gradient
                'accent': (255, 255, 255),
                'icon': '🥋',
                'pattern': 'diagonal'
            },
            'judo': {
                'colors': [(74, 144, 226), (155, 89, 182)],  # Blue-purple gradient
                'accent': (255, 255, 255),
                'icon': '🥋',
                'pattern': 'circles'
            },
            'taekwondo': {
                'colors': [(231, 76, 60), (192, 57, 43)],  # Red gradient
                'accent': (255, 255, 255),
                'icon': '🦵',
                'pattern': 'lines'
            },
            'kickboks': {
                'colors': [(46, 204, 113), (26, 188, 156)],  # Green gradient
                'accent': (255, 255, 255),
                'icon': '👊',
                'pattern': 'hexagon'
            },
            'mma': {
                'colors': [(52, 73, 94), (44, 62, 80)],  # Dark gradient
                'accent': (241, 196, 15),
                'icon': '🥊',
                'pattern': 'grid'
            },
            'muay thai': {
                'colors': [(155, 89, 182), (142, 68, 173)],  # Purple gradient
                'accent': (255, 255, 255),
                'icon': '⚡',
                'pattern': 'waves'
            }
        }
        
        # Default tema
        default_theme = {
            'colors': [(52, 152, 219), (41, 128, 185)],  # Blue gradient
            'accent': (255, 255, 255),
            'icon': '🏆',
            'pattern': 'simple'
        }
        
        return themes.get(category, default_theme)

    def _create_gradient_background(self, width, height, colors):
        """Gradient arkaplan oluştur"""
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Linear gradient oluştur
        color1, color2 = colors
        
        for y in range(height):
            # Y ekseninde gradient hesapla
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return image

    def _add_text_overlay(self, image, title, theme):
        """Başlık metnini resme ekle"""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Font boyutunu başlık uzunluğuna göre ayarla
        if len(title) > 60:
            font_size = 48
        elif len(title) > 40:
            font_size = 56
        else:
            font_size = 64
        
        try:
            # Windows için font yolu
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf',
                'arial.ttf',
                'calibri.ttf'
            ]
            
            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            
            if not font:
                font = ImageFont.load_default()
                
        except:
            font = ImageFont.load_default()
        
        # Metni satırlara böl
        words = title.split()
        lines = []
        current_line = ''
        
        for word in words:
            test_line = current_line + ' ' + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= width - 200:  # 100px margin on each side
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Metni ortala ve çiz
        total_height = len(lines) * (font_size + 10)
        y_start = (height - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_start + i * (font_size + 10)
            
            # Gölge efekti
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), line, 
                     fill=(0, 0, 0, 128), font=font)
            
            # Ana metin
            draw.text((x, y), line, fill=theme['accent'], font=font)
        
        return image

    def _add_category_icon(self, image, category, theme):
        """Kategori simgesini ekle"""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        try:
            # Unicode emoji font (Windows 10+)
            icon_font = ImageFont.truetype('seguiemj.ttf', 80)
            icon_text = theme['icon']
            
            # Sağ üst köşeye yerleştir
            bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
            icon_width = bbox[2] - bbox[0]
            
            x = width - icon_width - 50
            y = 50
            
            # Gölge
            draw.text((x + 2, y + 2), icon_text, fill=(0, 0, 0, 100), font=icon_font)
            # Ana icon
            draw.text((x, y), icon_text, font=icon_font)
            
        except:
            # Fallback: Basit geometrik şekil
            circle_radius = 40
            x = width - circle_radius - 50
            y = 50
            
            draw.ellipse([x - circle_radius, y, 
                         x + circle_radius, y + circle_radius * 2], 
                        fill=theme['accent'], outline=theme['colors'][0], width=3)
        
        return image

    def _add_decorative_elements(self, image, theme):
        """Dekoratif öğeler ekle"""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        pattern = theme.get('pattern', 'simple')
        accent_color = theme['accent']
        
        if pattern == 'diagonal':
            # Diagonal çizgiler
            for i in range(0, width + height, 100):
                draw.line([(i, 0), (i - height, height)], 
                         fill=(*accent_color[:3], 30), width=2)
        
        elif pattern == 'circles':
            # Rastgele daireler
            for _ in range(8):
                x = random.randint(0, width)
                y = random.randint(0, height)
                radius = random.randint(20, 60)
                draw.ellipse([x - radius, y - radius, x + radius, y + radius],
                           outline=(*accent_color[:3], 50), width=2)
        
        elif pattern == 'lines':
            # Horizontal çizgiler
            for y in range(0, height, 80):
                draw.line([(0, y), (width, y)], 
                         fill=(*accent_color[:3], 20), width=1)
        
        return image