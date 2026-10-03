from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import Kategori, FederasyonWebsite

class Command(BaseCommand):
    help = 'Kategorileri düzeltir, gereksizleri siler ve federasyon bağlantılarını günceller'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🔧 KATEGORİ DÜZELTME İŞLEMİ BAŞLIYOR\n')
        )
        self.stdout.write('=' * 60)
        
        # 1. Duplicate kategorileri düzelt
        self.stdout.write('\n1. DUPLICATE KATEGORİLER DÜZELTİLİYOR...')
        
        # "Boks" ve "Boxing" birleştirilecek - Türkçesini tut
        try:
            boxing_kategori = Kategori.objects.filter(ad='Boxing')
            if boxing_kategori.exists():
                # "Boks" kategorisini bul
                boks_kategori = Kategori.objects.filter(ad='Boks').first()
                if boks_kategori:
                    # "Boxing" kategorilerini sil, haberleri "Boks" kategorisine taşı
                    for kategori in boxing_kategori:
                        # Haberleri taşı
                        for haber in kategori.haberler.all():
                            haber.kategori = boks_kategori
                            haber.save()
                        # Kategoriyi sil
                        kategori.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✓ "Boxing" kategorisi silindi ve haberleri "Boks" kategorisine taşındı')
                        )
                else:
                    # "Boxing" ismini "Boks" olarak güncelle
                    kategori = boxing_kategori.first()
                    kategori.ad = 'Boks'
                    kategori.slug = slugify('Boks')
                    kategori.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✓ "Boxing" kategorisi "Boks" olarak güncellendi')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ "Boxing" kategorisi düzeltilirken hata: {str(e)}')
            )
        
        # "Mixed Martial Arts" ve "MMA" birleştirilecek - "MMA"yı tut
        try:
            mixed_martial_arts_kategori = Kategori.objects.filter(ad='Mixed Martial Arts')
            if mixed_martial_arts_kategori.exists():
                # "MMA" kategorisini bul
                mma_kategori = Kategori.objects.filter(ad='MMA').first()
                if mma_kategori:
                    # "Mixed Martial Arts" kategorilerini sil, haberleri "MMA" kategorisine taşı
                    for kategori in mixed_martial_arts_kategori:
                        # Haberleri taşı
                        for haber in kategori.haberler.all():
                            haber.kategori = mma_kategori
                            haber.save()
                        # Kategoriyi sil
                        kategori.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✓ "Mixed Martial Arts" kategorisi silindi ve haberleri "MMA" kategorisine taşındı')
                        )
                else:
                    # "Mixed Martial Arts" ismini "MMA" olarak güncelle
                    kategori = mixed_martial_arts_kategori.first()
                    kategori.ad = 'MMA'
                    kategori.slug = slugify('MMA')
                    kategori.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✓ "Mixed Martial Arts" kategorisi "MMA" olarak güncellendi')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ "Mixed Martial Arts" kategorisi düzeltilirken hata: {str(e)}')
            )
        
        # "Wrestling" ve "Güreş" birleştirilecek - "Güreş"i tut
        try:
            wrestling_kategori = Kategori.objects.filter(ad='Wrestling')
            if wrestling_kategori.exists():
                # "Güreş" kategorisini bul
                gures_kategori = Kategori.objects.filter(ad='Güreş').first()
                if gures_kategori:
                    # "Wrestling" kategorilerini sil, haberleri "Güreş" kategorisine taşı
                    for kategori in wrestling_kategori:
                        # Haberleri taşı
                        for haber in kategori.haberler.all():
                            haber.kategori = gures_kategori
                            haber.save()
                        # Kategoriyi sil
                        kategori.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✓ "Wrestling" kategorisi silindi ve haberleri "Güreş" kategorisine taşındı')
                        )
                else:
                    # "Wrestling" ismini "Güreş" olarak güncelle
                    kategori = wrestling_kategori.first()
                    kategori.ad = 'Güreş'
                    kategori.slug = slugify('Güreş')
                    kategori.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✓ "Wrestling" kategorisi "Güreş" olarak güncellendi')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ "Wrestling" kategorisi düzeltilirken hata: {str(e)}')
            )
        
        # 2. Federasyon bağlantılarını güncelle
        self.stdout.write('\n2. FEDERASYON BAĞLANTILARI GÜNCELLENİYOR...')
        
        federasyon_baglantilari = {
            'Boks': 'Türkiye Boks Federasyonu',
            'Güreş': 'Türkiye Güreş Federasyonu',
            'Taekwondo': 'Türkiye Taekwondo Federasyonu',
            'Judo': 'Türkiye Judo Federasyonu',
            'Kickboks': 'Türkiye Kick Boks Federasyonu',
            'Muay Thai': 'Türkiye Muay Thai Federasyonu',
            'Aikido': 'Türkiye Aikido Federasyonu',
            'Kempo': 'Türkiye Kempo Federasyonu',
            'Wushu': 'Türkiye Wushu Kung Fu Federasyonu',
            'Savate': 'Türkiye Savate Federasyonu',
            'Hapkido': 'Türkiye Hapkido Federasyonu',
            'Karate-Do': 'Türkiye Karate-Do Federasyonu',
            'Ju Jitsu': 'Türkiye Ju Jitsu Federasyonu',
            'MMA': 'Türkiye Karma Dövüş Sanatları Federasyonu',
            'Karate': 'Türkiye Karate Federasyonu'
        }
        
        for kategori_ad, federasyon_ad in federasyon_baglantilari.items():
            try:
                kategori = Kategori.objects.filter(ad=kategori_ad).first()
                if kategori:
                    federasyon = FederasyonWebsite.objects.filter(ad=federasyon_ad).first()
                    if federasyon:
                        kategori.federasyon_website = federasyon
                        kategori.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✓ {kategori_ad} → {federasyon_ad}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'   ⚠️  {federasyon_ad} bulunamadı')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  {kategori_ad} kategorisi bulunamadı')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ✗ {kategori_ad} federasyon bağlantısı yapılırken hata: {str(e)}')
                )
        
        # 3. Özet
        self.stdout.write('\n3. İŞLEM ÖZETİ')
        self.stdout.write('=' * 30)
        
        toplam_kategori = Kategori.objects.count()
        federasyonlu_kategori = Kategori.objects.filter(federasyon_website__isnull=False).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🏆 SONUÇ:'
                f'\n   • Toplam Kategori: {toplam_kategori}'
                f'\n   • Federasyonlu Kategori: {federasyonlu_kategori}'
                f'\n   • Federasyonsuz Kategori: {toplam_kategori - federasyonlu_kategori}'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Kategori düzeltme işlemi tamamlandı!')
        )