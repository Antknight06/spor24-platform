from django.core.management.base import BaseCommand
from django.db import transaction
from haberler.models import Haber, Kategori

class Command(BaseCommand):
    help = 'Tüm karate alt kategorilerindeki haberleri ana Karate kategorisine taşı ve alt kategorileri sil'

    def handle(self, *args, **options):
        self.stdout.write('🔄 KARATE KATEGORİLERİNİ KONSOLİDE ETME')
        self.stdout.write('=' * 50)
        
        # Ana Karate kategorisini al
        try:
            ana_karate = Kategori.objects.get(slug='karate')
            self.stdout.write(f'✅ Ana Karate kategorisi bulundu: {ana_karate.ad} (ID: {ana_karate.id})')
        except Kategori.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Ana Karate kategorisi bulunamadı!')
            )
            return
        
        # Alt kategorileri bul
        alt_kategoriler = [
            'Ziyaretler',
            'Kurs & Seminer', 
            'Etkinlikler',
            'Kyokushin',
            'Federasyon'
        ]
        
        toplam_tasinan = 0
        silinen_kategoriler = []
        
        for kategori_adi in alt_kategoriler:
            try:
                alt_kategori = Kategori.objects.get(ad=kategori_adi)
                
                # Bu kategorideki haberleri say
                haberler = Haber.objects.filter(kategori=alt_kategori)
                haber_sayisi = haberler.count()
                
                self.stdout.write(f'\\n📂 {kategori_adi} kategorisi: {haber_sayisi} haber')
                
                if haber_sayisi > 0:
                    # Haberleri ana kategoriye taşı
                    with transaction.atomic():
                        for haber in haberler:
                            haber.kategori = ana_karate
                            haber.save()
                            self.stdout.write(f'   ✅ Taşındı: {haber.baslik[:50]}...')
                        
                        toplam_tasinan += haber_sayisi
                
                # Alt kategoriyi sil
                alt_kategori.delete()
                silinen_kategoriler.append(kategori_adi)
                self.stdout.write(f'🗑️  Kategori silindi: {kategori_adi}')
                
            except Kategori.DoesNotExist:
                self.stdout.write(f'⚠️  Kategori bulunamadı: {kategori_adi}')
                continue
        
        # Sonuçları göster
        self.stdout.write(
            self.style.SUCCESS(f'\\n🎉 İşlem tamamlandı!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   📰 {toplam_tasinan} haber ana Karate kategorisine taşındı')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   🗑️  {len(silinen_kategoriler)} alt kategori silindi')
        )
        
        # Son durum
        final_count = Haber.objects.filter(kategori=ana_karate).count()
        self.stdout.write(
            self.style.SUCCESS(f'   📊 Ana Karate kategorisinde toplam: {final_count} haber')
        )
        
        self.stdout.write(f'\\n📋 Silinen kategoriler:')
        for kategori in silinen_kategoriler:
            self.stdout.write(f'   - {kategori}')