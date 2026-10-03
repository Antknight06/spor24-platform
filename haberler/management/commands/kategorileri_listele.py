from django.core.management.base import BaseCommand
from haberler.models import Kategori, FederasyonWebsite

class Command(BaseCommand):
    help = 'Tüm kategorileri ve ilişkili federasyon websitelerini listeler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🏆 TÜM KATEGORİLER ve FEDERASYON WEBSİTELERİ\n')
        )
        self.stdout.write('=' * 80)
        
        # Get all categories ordered by name
        kategoriler = Kategori.objects.all().order_by('ad')
        
        if not kategoriler.exists():
            self.stdout.write(
                self.style.WARNING('Henüz kategori bulunmamaktadır.')
            )
            return
            
        toplam_kategoriler = kategoriler.count()
        federasyonlu_kategoriler = 0
        
        for kategori in kategoriler:
            # Display category info
            self.stdout.write(f'\n🥋 {kategori.ad}')
            self.stdout.write(f'   Açıklama: {kategori.aciklama[:100]}{"..." if len(kategori.aciklama) > 100 else ""}')
            self.stdout.write(f'   Oluşturma Tarihi: {kategori.olusturma_tarihi.strftime("%d.%m.%Y") if kategori.olusturma_tarihi else "Bilinmiyor"}')
            
            # Check if category has a federation website
            if kategori.federasyon_website:
                federasyonlu_kategoriler += 1
                federation = kategori.federasyon_website
                self.stdout.write(
                    self.style.SUCCESS(f'   🌐 Federasyon: {federation.ad}')
                )
                self.stdout.write(f'      Ana URL: {federation.ana_url}')
                self.stdout.write(f'      Haberler URL: {federation.haberler_url}')
                self.stdout.write(f'      Aktif: {"Evet" if federation.aktif else "Hayır"}')
            else:
                self.stdout.write(
                    self.style.WARNING('   ⚠️  Federasyon: Henüz atanmamış')
                )
                
            self.stdout.write('-' * 60)
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 ÖZET:'
                f'\n   • Toplam Kategori: {toplam_kategoriler}'
                f'\n   • Federasyonlu Kategori: {federasyonlu_kategoriler}'
                f'\n   • Federasyonsuz Kategori: {toplam_kategoriler - federasyonlu_kategoriler}'
            )
        )