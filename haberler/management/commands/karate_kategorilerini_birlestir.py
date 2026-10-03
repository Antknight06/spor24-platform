from django.core.management.base import BaseCommand
from haberler.models import Kategori, Haber
from django.db import transaction

class Command(BaseCommand):
    help = 'Karate (Resmi) kategorisindeki haberleri ana Karate kategorisine aktar ve resmi kategoriyi sil'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece analiz yap, değişiklik yapma'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('🔄 KARATE KATEGORİLERİNİ BİRLEŞTİRME SİSTEMİ')
        self.stdout.write('=' * 50)
        
        try:
            # Ana Karate kategorisini bul
            ana_karate = Kategori.objects.get(id=1, slug='karate')
            self.stdout.write(f'✅ Ana Karate kategorisi bulundu: {ana_karate.ad} (ID: {ana_karate.id})')
            
            # Resmi Karate kategorisini bul
            resmi_karate = Kategori.objects.get(id=27, slug='turkiye-karate-federasyonu-resmi')
            self.stdout.write(f'✅ Resmi Karate kategorisi bulundu: {resmi_karate.ad} (ID: {resmi_karate.id})')
            
            # Resmi kategorideki haberleri say
            resmi_haberler = Haber.objects.filter(kategori=resmi_karate)
            haber_sayisi = resmi_haberler.count()
            
            self.stdout.write(f'\n📊 DURUM:')
            self.stdout.write(f'   Ana Karate kategorisi: {Haber.objects.filter(kategori=ana_karate).count()} haber')
            self.stdout.write(f'   Resmi Karate kategorisi: {haber_sayisi} haber')
            
            if haber_sayisi == 0:
                self.stdout.write(
                    self.style.WARNING('⚠️  Resmi kategoride aktarılacak haber bulunamadı')
                )
                if not dry_run:
                    resmi_karate.delete()
                    self.stdout.write(
                        self.style.SUCCESS('✅ Boş Resmi Karate kategorisi silindi')
                    )
                return
            
            if dry_run:
                self.stdout.write(f'\n🔍 DRY RUN - Yapılacak işlemler:')
                self.stdout.write(f'   - {haber_sayisi} haber ana Karate kategorisine aktarılacak')
                self.stdout.write(f'   - Resmi Karate kategorisi silinecek')
                
                self.stdout.write(f'\n📝 Aktarılacak haberler:')
                for haber in resmi_haberler[:10]:  # İlk 10 haberi göster
                    self.stdout.write(f'   • {haber.baslik[:60]}...')
                if haber_sayisi > 10:
                    self.stdout.write(f'   ... ve {haber_sayisi - 10} haber daha')
                
                return
            
            # Gerçek aktarım işlemi
            with transaction.atomic():
                self.stdout.write(f'\n🔄 Haberler aktarılıyor...')
                
                aktarilan = 0
                for haber in resmi_haberler:
                    haber.kategori = ana_karate
                    haber.save()
                    aktarilan += 1
                    self.stdout.write(f'   ✅ Aktarıldı: {haber.baslik[:50]}...')
                
                # Resmi kategoriyi sil
                resmi_karate.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 İşlem tamamlandı!')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   • {aktarilan} haber ana Karate kategorisine aktarıldı')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   • Resmi Karate kategorisi silindi')
                )
                
                # Son durum
                final_count = Haber.objects.filter(kategori=ana_karate).count()
                self.stdout.write(f'\n📊 SON DURUM:')
                self.stdout.write(f'   Ana Karate kategorisi: {final_count} haber')
        
        except Kategori.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Kategori bulunamadı: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Hata oluştu: {e}')
            )