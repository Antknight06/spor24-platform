from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite

class Command(BaseCommand):
    help = 'Federasyon tekrarlarını siler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🗑️ FEDERASYON TEKRARLARI SİLİNİYOR\n')
        )
        self.stdout.write('=' * 50)
        
        # Get all federation names
        federation_names = FederasyonWebsite.objects.values_list('ad', flat=True).distinct()
        
        silinen_sayisi = 0
        
        for name in federation_names:
            # Get all federations with the same name
            federations = FederasyonWebsite.objects.filter(ad=name).order_by('id')
            
            if federations.count() > 1:
                self.stdout.write(f'\n🔍 {name} için tekrarlar bulundu:')
                
                # Keep the first one, delete the rest
                federations_to_delete = federations[1:]
                
                for federation in federations_to_delete:
                    self.stdout.write(f'   🗑️ Siliniyor: {federation.ana_url}')
                    federation.delete()
                    silinen_sayisi += 1
                
                kept_federation = federations.first()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Korunan: {kept_federation.ana_url}')
                )
        
        # Special case: Handle similar named federations
        self.stdout.write(f'\n🔍 Benzer isimli federasyonlar kontrol ediliyor...')
        
        # Check for karate federations
        karate_federations = FederasyonWebsite.objects.filter(ad__icontains='Karate')
        if karate_federations.count() > 1:
            self.stdout.write(f'\n🔍 Karate federasyonları için tekrarlar bulundu:')
            
            # Keep the one with "(Resmi)" in the name
            official_karate = karate_federations.filter(ad__icontains='(Resmi)').first()
            if official_karate:
                duplicates = karate_federations.exclude(id=official_karate.id)
                for duplicate in duplicates:
                    self.stdout.write(f'   🗑️ Siliniyor: {duplicate.ad} - {duplicate.ana_url}')
                    duplicate.delete()
                    silinen_sayisi += 1
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Korunan: {official_karate.ad} - {official_karate.ana_url}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ İşlem tamamlandı! Toplam {silinen_sayisi} tekrar silindi.'
            )
        )