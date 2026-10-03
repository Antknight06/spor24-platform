import os
import django
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from haberler.models import Haber

class Command(BaseCommand):
    help = 'Boks haberlerine varsayılan boxing fotoğraflarını atar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mevcut resimleri de değiştir'
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Boks ile ilgili haberleri bul (tüm boks haberleri)
        boks_haberleri = Haber.objects.filter(
            baslik__icontains='boks'
        )
        
        if not boks_haberleri.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  Boks haberi bulunamadı.')
            )
            return
        
        self.stdout.write(f'🔍 Toplam {boks_haberleri.count()} boks haberi bulundu')
        
        # Varsayılan boxing görsellerinin yolları
        static_boxing_dir = os.path.join(settings.BASE_DIR, 'static', 'boxing')
        
        # Yeni kırmızı boxing eldiveni görselini kullan
        selected_image = 'default_boxing_glove.svg'
        image_path = os.path.join(static_boxing_dir, selected_image)
        
        # Kontrol et: dosya mevcut mu?
        if not os.path.exists(image_path):
            self.stdout.write(
                self.style.ERROR(f'❌ {selected_image} bulunamadı!')
            )
            return
        
        self.stdout.write(f'   ✅ {selected_image} mevcut')
        
        # Tüm boks haberlerine yeni kırmızı görseli ata
        updated_count = 0
        for i, haber in enumerate(boks_haberleri):
            # Her durumda (force olsun ya da olmasın) güncelle
            try:
                # Resmi haber modeline ata
                with open(image_path, 'rb') as f:
                    # Dosya adını oluştur
                    file_name = f"red_boxing_glove_{i+1}.svg"
                    
                    # Haber resmini güncelle
                    haber.resim.save(file_name, File(f), save=True)
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ {haber.baslik[:50]}... için yeni kırmızı boxing eldiveni atandı')
                )
                updated_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {haber.baslik[:50]}... için görsel atanamadı: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 İşlem tamamlandı! {updated_count} boks haberi için yeni kırmızı boxing eldiveni atandı.')
        )