from django.core.management.base import BaseCommand
from haberler.models import Kategori, FederasyonWebsite

class Command(BaseCommand):
    help = 'Karate kategorilerini düzenler: Resmi Karate kategorisinin federasyon bilgilerini Karate kategorisine aktarır ve Resmi Karate kategorisini siler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🔄 KARATE KATEGORİLERİ DÜZENLENİYOR\n')
        )
        self.stdout.write('=' * 50)
        
        try:
            # Get the categories
            karate_category = Kategori.objects.get(ad='Karate')
            resmi_karate_category = Kategori.objects.get(ad='Resmi Karate')
            federation = FederasyonWebsite.objects.get(ad='Türkiye Karate Federasyonu (Resmi)')
            
            self.stdout.write(f'Karate kategorisi: {karate_category.ad} (ID: {karate_category.id})')
            self.stdout.write(f'Resmi Karate kategorisi: {resmi_karate_category.ad} (ID: {resmi_karate_category.id})')
            self.stdout.write(f'Federasyon: {federation.ad} (ID: {federation.id})')
            
            # Check current federation associations
            if karate_category.federasyon_website:
                self.stdout.write(f'Karate kategorisinin mevcut federasyonu: {karate_category.federasyon_website.ad}')
            else:
                self.stdout.write('Karate kategorisinin federasyonu yok')
                
            if resmi_karate_category.federasyon_website:
                self.stdout.write(f'Resmi Karate kategorisinin federasyonu: {resmi_karate_category.federasyon_website.ad}')
            else:
                self.stdout.write('Resmi Karate kategorisinin federasyonu yok')
            
            # Transfer federation website from Resmi Karate to Karate category
            karate_category.federasyon_website = federation
            karate_category.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Federasyon bilgisi "{resmi_karate_category.ad}" kategorisinden "{karate_category.ad}" kategorisine aktarıldı')
            )
            
            # Delete the Resmi Karate category
            resmi_karate_category.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ "{resmi_karate_category.ad}" kategorisi silindi')
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Karate kategorileri başarıyla düzenlendi')
            )
            
        except Kategori.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Kategori bulunamadı: {e}')
            )
        except FederasyonWebsite.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Federasyon bulunamadı: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ İşlem sırasında hata oluştu: {e}')
            )