from django.core.management.base import BaseCommand
from haberler.models import Haber
import os

class Command(BaseCommand):
    help = 'Hangi haberlerde hangi tür resimler kullanıldığını detaylı analiz et'

    def handle(self, *args, **options):
        self.stdout.write('🔍 DETAYLI RESİM ANALİZİ')
        self.stdout.write('=' * 60)
        
        # Kategorilere göre analiz
        categories = {}
        total_news = 0
        transformed_count = 0
        orange_background_count = 0
        no_image_count = 0
        
        for haber in Haber.objects.filter(yayinlandi=True).order_by('-olusturma_tarihi'):
            total_news += 1
            category = haber.kategori.ad if haber.kategori else 'Kategori Yok'
            
            if category not in categories:
                categories[category] = {
                    'total': 0,
                    'transformed': [],
                    'orange_bg': [],
                    'no_image': []
                }
            
            categories[category]['total'] += 1
            
            if haber.resim:
                image_name = os.path.basename(haber.resim.name)
                
                if ('transformed_' in image_name or 
                    image_name.startswith('news_') or 
                    image_name.startswith('copyright_free_') or
                    image_name.startswith('original_')):
                    categories[category]['transformed'].append({
                        'title': haber.baslik,
                        'image': image_name,
                        'date': haber.olusturma_tarihi.strftime('%d.%m.%Y') if haber.olusturma_tarihi else 'Tarih yok'
                    })
                    transformed_count += 1
                else:
                    # Bu muhtemelen başka tür orijinal resim
                    categories[category]['orange_bg'].append({
                        'title': haber.baslik,
                        'image': image_name,
                        'date': haber.olusturma_tarihi.strftime('%d.%m.%Y') if haber.olusturma_tarihi else 'Tarih yok'
                    })
                    orange_background_count += 1
            else:
                categories[category]['no_image'].append({
                    'title': haber.baslik,
                    'date': haber.olusturma_tarihi.strftime('%d.%m.%Y') if haber.olusturma_tarihi else 'Tarih yok'
                })
                no_image_count += 1
        
        # Genel istatistikler
        self.stdout.write(f'\n📊 GENEL İSTATİSTİKLER:')
        self.stdout.write(f'   • Toplam haber: {total_news}')
        self.stdout.write(f'   • Modifiye edilmiş resimli: {transformed_count} (%{(transformed_count/total_news)*100:.1f})')
        self.stdout.write(f'   • Turuncu/orijinal resimli: {orange_background_count} (%{(orange_background_count/total_news)*100:.1f})')
        self.stdout.write(f'   • Resimsiz: {no_image_count} (%{(no_image_count/total_news)*100:.1f})')
        
        # Kategori bazında detay
        for category, data in categories.items():
            self.stdout.write(f'\n📂 {category.upper()} KATEGORİSİ ({data["total"]} haber):')
            
            if data['transformed']:
                self.stdout.write(f'   ✅ MODİFİYE EDİLMİŞ RESİMLER ({len(data["transformed"])} adet):')
                for item in data['transformed'][:5]:  # İlk 5'i göster
                    self.stdout.write(f'      🎨 {item["title"][:50]}... ({item["date"]})')
                    self.stdout.write(f'         └─ {item["image"]}')
                if len(data['transformed']) > 5:
                    self.stdout.write(f'      ... ve {len(data["transformed"]) - 5} tane daha')
            
            if data['orange_bg']:
                self.stdout.write(f'   🟠 TURUNCU/ORİJİNAL RESİMLER ({len(data["orange_bg"])} adet):')
                for item in data['orange_bg'][:5]:  # İlk 5'i göster
                    self.stdout.write(f'      📸 {item["title"][:50]}... ({item["date"]})')
                    self.stdout.write(f'         └─ {item["image"]}')
                if len(data['orange_bg']) > 5:
                    self.stdout.write(f'      ... ve {len(data["orange_bg"]) - 5} tane daha')
            
            if data['no_image']:
                self.stdout.write(f'   ❌ RESİMSİZ ({len(data["no_image"])} adet):')
                for item in data['no_image'][:3]:  # İlk 3'ü göster
                    self.stdout.write(f'      📝 {item["title"][:50]}... ({item["date"]})')
                if len(data['no_image']) > 3:
                    self.stdout.write(f'      ... ve {len(data["no_image"]) - 3} tane daha')
        
        self.stdout.write(f'\n💡 ÖNERİLER:')
        self.stdout.write(f'   • Turuncu arka planlı resimleri değiştirmek için:')
        self.stdout.write(f'     python manage.py federasyon_fotograf_ozgunlestir --limit=20 --style=news')
        self.stdout.write(f'   • Veya özgün resimler oluşturmak için:')
        self.stdout.write(f'     python manage.py ozgun_resim_olustur --limit=20')
        self.stdout.write(f'   • Farklı stiller denemek için: --style=artistic, --style=modern, --style=professional')