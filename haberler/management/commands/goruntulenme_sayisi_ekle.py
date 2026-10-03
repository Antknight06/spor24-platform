from django.core.management.base import BaseCommand
from haberler.models import Haber
import random

class Command(BaseCommand):
    help = 'Mevcut haberlere rastgele görüntülenme sayıları ekler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-views',
            type=int,
            default=10,
            help='Minimum görüntülenme sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--max-views',
            type=int,
            default=5000,
            help='Maksimum görüntülenme sayısı (varsayılan: 5000)'
        )

    def handle(self, *args, **options):
        min_views = options['min_views']
        max_views = options['max_views']
        
        # Görüntülenme sayısı 0 olan haberleri bul
        haberler = Haber.objects.filter(goruntulenme_sayisi=0)
        
        if not haberler.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  Görüntülenme sayısı 0 olan haber bulunamadı.')
            )
            return
        
        updated_count = 0
        
        for haber in haberler:
            # Rastgele görüntülenme sayısı ata
            view_count = random.randint(min_views, max_views)
            haber.goruntulenme_sayisi = view_count
            haber.save(update_fields=['goruntulenme_sayisi'])
            updated_count += 1
            
            self.stdout.write(
                f'✅ {haber.baslik[:40]}... - {view_count} görüntülenme'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 {updated_count} haberin görüntülenme sayısı güncellendi!')
        )