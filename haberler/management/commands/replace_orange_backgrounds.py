from django.core.management.base import BaseCommand
from haberler.models import Haber
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
import io
import os
import uuid

class Command(BaseCommand):
    help = 'Turuncu arka planlı resimleri telif-free alternatiflerle değiştir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='İşlenecek haber sayısı (varsayılan: 20)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write('🔄 TURUNCU ARKAPLANLı RESİMLERİ DEĞİŞTİRME SİSTEMİ')
        self.stdout.write('=' * 60)
        
        # Original_ ile başlayan resimleri olan haberleri bul
        haberler = []
        for haber in Haber.objects.filter(yayinlandi=True):
            if haber.resim:
                image_name = os.path.basename(haber.resim.name)
                if image_name.startswith('original_'):
                    haberler.append(haber)
        
        if not haberler:
            self.stdout.write(
                self.style.WARNING('⚠️  Değiştirilecek turuncu arka planlı resim bulunamadı.')
            )
            return
        
        if limit > 0:
            haberler = haberler[:limit]
        
        self.stdout.write(f'🎯 {len(haberler)} turuncu arka planlı resim telif-free alternatifle değiştirilecek')
        
        success_count = 0
        
        for i, haber in enumerate(haberler, 1):
            try:
                self.stdout.write(f'\n[{i}/{len(haberler)}] 🎨 {haber.baslik[:50]}...')
                
                # Yeni telif-free resim oluştur
                new_image = self._create_copyright_free_image(haber)
                
                if new_image:
                    # Eski resmi sil
                    if haber.resim:
                        haber.resim.delete(save=False)
                    
                    # Yeni resmi kaydet
                    haber.resim.save(new_image.name, new_image, save=True)
                    success_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Değiştirildi: {new_image.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Resim oluşturulamadı')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! {success_count} turuncu arka planlı resim değiştirildi.'
            )
        )

    def _create_copyright_free_image(self, haber):
        """Telif sorunu olmayan özgün resim oluştur"""
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
            safe_title = self._make_safe_filename(haber.baslik)
            unique_id = str(uuid.uuid4())[:8]
            filename = f"copyright_free_{safe_title}_{unique_id}.jpg"
            
            return ContentFile(output.read(), name=filename)
            
        except Exception as e:
            self.stdout.write(f'   🔧 Resim oluşturma hatası: {e}')
            return None

    def _get_category_color(self, category):
        """Kategoriye göre renk döndür"""
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
        """Dekoratif şekiller ekle"""
        # Solda büyük daire
        circle_color = tuple(min(255, c + 30) for c in color)
        draw.ellipse([width-150, height-150, width+50, height+50], fill=circle_color)
        
        # Üstte küçük daireler
        small_color = tuple(min(255, c + 20) for c in color)
        draw.ellipse([50, 30, 100, 80], fill=small_color)
        draw.ellipse([150, 20, 190, 60], fill=small_color)

    def _add_title_text(self, draw, title, width, height):
        """Başlık metni ekle"""
        try:
            # Font yükle
            try:
                font_large = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 32)
                font_small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Metni temizle ve böl
            clean_title = self._clean_turkish_text(title)
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
        """Kategori etiketi ekle"""
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

    def _clean_turkish_text(self, text):
        """Türkçe karakterleri temizle"""
        if not text:
            return ""
        
        # Türkçe karakterleri değiştir
        replacements = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ş': 's', 'ü': 'u', 'ö': 'o',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ş': 'S', 'Ü': 'U', 'Ö': 'O'
        }
        
        for turkish, latin in replacements.items():
            text = text.replace(turkish, latin)
        
        return text

    def _make_safe_filename(self, title):
        """Güvenli dosya adı oluştur"""
        if not title:
            return 'haber'
        
        # Türkçe karakterleri temizle
        safe_title = self._clean_turkish_text(title)
        
        # Sadece harf, rakam ve tire bırak
        import re
        safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', safe_title)
        safe_title = re.sub(r'\s+', '-', safe_title)
        safe_title = safe_title.strip('-')[:30]
        
        return safe_title if safe_title else 'haber'