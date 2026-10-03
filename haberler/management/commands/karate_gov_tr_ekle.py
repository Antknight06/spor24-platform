from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import FederasyonWebsite, Kategori

class Command(BaseCommand):
    help = 'karate.gov.tr federasyon websitesini ekler ve CSS selectorlarını yapılandırır'

    def handle(self, *args, **options):
        # karate.gov.tr için yapılandırma
        karate_gov_tr = {
            'ad': 'Türkiye Karate Federasyonu (Resmi)',
            'ana_url': 'https://karate.gov.tr',
            'haberler_url': 'https://karate.gov.tr/haber-kategori/federasyon',
            'haber_listesi_selector': '.row .col-md-4, .haber-item, article',
            'haber_baslik_selector': 'h3, h4, .title, .baslik',
            'haber_link_selector': 'a',
            'haber_tarih_selector': '.date, .tarih, time',
            'haber_ozet_selector': '.excerpt, .ozet, p',
            'kategori': 'Karate'
        }

        try:
            # Karate kategorisini oluştur veya al
            karate_kategori, kategori_created = Kategori.objects.get_or_create(
                slug='karate',
                defaults={
                    'ad': 'Karate',
                    'aciklama': 'Karate haberleri ve duyuruları'
                }
            )
            
            if kategori_created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Karate kategorisi oluşturuldu')
                )

            # Federasyon websitesini oluştur veya güncelle
            federation, created = FederasyonWebsite.objects.get_or_create(
                ad=karate_gov_tr['ad'],
                defaults={
                    'ana_url': karate_gov_tr['ana_url'],
                    'haberler_url': karate_gov_tr['haberler_url'],
                    'haber_listesi_selector': karate_gov_tr['haber_listesi_selector'],
                    'haber_baslik_selector': karate_gov_tr['haber_baslik_selector'],
                    'haber_link_selector': karate_gov_tr['haber_link_selector'],
                    'haber_tarih_selector': karate_gov_tr['haber_tarih_selector'],
                    'haber_ozet_selector': karate_gov_tr['haber_ozet_selector'],
                    'aktif': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {karate_gov_tr["ad"]} eklendi')
                )
            else:
                # Mevcut federasyonu güncelle
                federation.ana_url = karate_gov_tr['ana_url']
                federation.haberler_url = karate_gov_tr['haberler_url']
                federation.haber_listesi_selector = karate_gov_tr['haber_listesi_selector']
                federation.haber_baslik_selector = karate_gov_tr['haber_baslik_selector']
                federation.haber_link_selector = karate_gov_tr['haber_link_selector']
                federation.haber_tarih_selector = karate_gov_tr['haber_tarih_selector']
                federation.haber_ozet_selector = karate_gov_tr['haber_ozet_selector']
                federation.aktif = True
                federation.save()
                
                self.stdout.write(
                    self.style.WARNING(f'! {karate_gov_tr["ad"]} güncellendi')
                )
            
            # Kategoriyi federasyona bağla
            karate_kategori.federasyon_website = federation
            karate_kategori.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🥋 karate.gov.tr başarıyla yapılandırıldı!'
                )
            )
            
            self.stdout.write('\n📋 Haberleri çekmek için:')
            self.stdout.write('   python ANT_News\\manage.py haber_cek --federation="Türkiye Karate Federasyonu (Resmi)"')
            self.stdout.write('\n📋 Veya tüm federasyonlardan haber çekmek için:')
            self.stdout.write('   python ANT_News\\manage.py haber_cek --all')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Hata oluştu: {str(e)}')
            )