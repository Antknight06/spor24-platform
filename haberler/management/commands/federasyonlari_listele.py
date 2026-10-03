from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite

class Command(BaseCommand):
    help = 'Tüm federasyonları listeler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n📋 FEDERASYON LİSTESİ\n')
        )
        self.stdout.write('=' * 50)
        
        # Tüm aktif federasyonları al
        federations = FederasyonWebsite.objects.filter(aktif=True).order_by('ad')
        
        if not federations:
            self.stdout.write(
                self.style.WARNING('⚠️  Hiç federasyon bulunamadı')
            )
            return
        
        self.stdout.write(f'📊 Toplam {federations.count()} federasyon:')
        self.stdout.write('')
        
        for i, federation in enumerate(federations, 1):
            self.stdout.write(f'{i:2d}. {federation.ad}')
            self.stdout.write(f'     URL: {federation.ana_url}')
            self.stdout.write(f'     Haberler: {federation.haberler_url}')
            
            # Kategori kontrolü
            if hasattr(federation, 'kategori_set') and federation.kategori_set.exists():
                kategori_sayisi = federation.kategori_set.count()
                self.stdout.write(f'     Kategoriler: {kategori_sayisi} adet')
            else:
                self.stdout.write(f'     Kategori: Henüz oluşturulmamış')
                self.stdout.write(
                    f'     Komut: python manage.py kategori_olustur --isim="{federation.ad}" --federasyon="{federation.ad}"'
                )
            
            self.stdout.write('')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'💡 Kategori oluşturmak için: python manage.py kategori_olustur --isim="Kategori Adı"'
            )
        )