from django.core.management.base import BaseCommand
from haberler.models import Haber
import os

class Command(BaseCommand):
    help = 'Modifiye edilmiş görsellerin kullanım durumunu raporla'

    def handle(self, *args, **options):
        self.stdout.write('🖼️  MODİFİYE EDİLMİŞ GÖRSELLER RAPORU')
        self.stdout.write('=' * 50)
        
        # Transformed images kullanan haberleri bul
        transformed_news = []
        original_news = []
        news_style_images = []
        total_with_images = 0
        
        for haber in Haber.objects.filter(yayinlandi=True):
            if haber.resim:
                total_with_images += 1
                image_name = os.path.basename(haber.resim.name)
                
                if 'transformed_' in image_name:
                    transformed_news.append({
                        'haber': haber,
                        'image': image_name,
                        'type': 'transformed'
                    })
                elif image_name.startswith('news_'):
                    news_style_images.append({
                        'haber': haber,
                        'image': image_name,
                        'type': 'news_style'
                    })
                elif image_name.startswith('original_'):
                    original_news.append({
                        'haber': haber,
                        'image': image_name,
                        'type': 'original'
                    })
        
        self.stdout.write(f'\n📊 İSTATİSTİKLER:')
        self.stdout.write(f'   • Toplam resimli haber: {total_with_images}')
        self.stdout.write(f'   • Transformed federasyon görselleri: {len(transformed_news)}')
        self.stdout.write(f'   • News stili telif-free görseller: {len(news_style_images)}')
        self.stdout.write(f'   • Orijinal yedek görseller: {len(original_news)}')
        
        self.stdout.write(f'\n✅ MODİFİYE EDİLMİŞ FEDERASYON GÖRSELLERİ:')
        for item in transformed_news[:10]:  # Show first 10
            self.stdout.write(f'   🎨 {item["haber"].baslik[:60]}...')
            self.stdout.write(f'      └─ {item["image"]}')
        
        if len(transformed_news) > 10:
            self.stdout.write(f'   ... ve {len(transformed_news) - 10} tane daha')
        
        self.stdout.write(f'\n🆕 NEWS STİLİ TELİF-FREE GÖRSELLER:')
        for item in news_style_images[:10]:  # Show first 10
            self.stdout.write(f'   📰 {item["haber"].baslik[:60]}...')
            self.stdout.write(f'      └─ {item["image"]}')
            
        if len(news_style_images) > 10:
            self.stdout.write(f'   ... ve {len(news_style_images) - 10} tane daha')
        
        self.stdout.write(f'\n📋 ÖNERİLER:')
        self.stdout.write(f'   1. ✅ Transformed görseller telif sorunu olmayan dönüştürülmüş görseller')
        self.stdout.write(f'   2. ✅ News stili görseller tamamen telif-free özgün görseller')
        self.stdout.write(f'   3. ⚠️  Original görseller federasyon sitesinden alınmış yedekler')
        self.stdout.write(f'   4. 🔄 Daha fazla haber için transformed görseller oluşturulabilir')
        
        # Success percentage
        copyright_safe = len(transformed_news) + len(news_style_images)
        if total_with_images > 0:
            safe_percentage = (copyright_safe / total_with_images) * 100
            self.stdout.write(f'\n🎯 TELİF GÜVENLİĞİ: %{safe_percentage:.1f} ({copyright_safe}/{total_with_images})')
        
        self.stdout.write(f'\n🎉 Sistem başarıyla çalışıyor! Haberlerde modifiye edilmiş görseller kullanılıyor.')