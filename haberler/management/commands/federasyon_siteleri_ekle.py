from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import FederasyonWebsite, Kategori

class Command(BaseCommand):
    help = 'Örnek federasyon websitelerini ve CSS selector\'larını ekler'

    def handle(self, *args, **options):
        # Sample federation websites with their CSS selectors
        # These are example configurations - you'll need to adjust selectors for real websites
        federasyon_siteleri = [
            {
                'ad': 'Türkiye Karate Federasyonu',
                'ana_url': 'https://www.turkiyekaratefederasyonu.gov.tr',
                'haberler_url': 'https://www.turkiyekaratefederasyonu.gov.tr/haberler',
                'haber_listesi_selector': '.news-list .news-item',
                'haber_baslik_selector': '.news-title, h3, h2',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.news-date, .date',
                'haber_ozet_selector': '.news-summary, .excerpt',
                'kategori': 'Karate'
            },
            {
                'ad': 'Türkiye Taekwondo Federasyonu',
                'ana_url': 'https://www.turkiyetaekwondofederasyonu.gov.tr',
                'haberler_url': 'https://www.turkiyetaekwondofederasyonu.gov.tr/haberler',
                'haber_listesi_selector': '.haberler .haber',
                'haber_baslik_selector': '.baslik, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.tarih',
                'haber_ozet_selector': '.ozet',
                'kategori': 'Taekwondo'
            },
            {
                'ad': 'Türkiye Judo Federasyonu',
                'ana_url': 'https://www.turkiyejudofederasyonu.org.tr',
                'haberler_url': 'https://www.turkiyejudofederasyonu.org.tr/haberler',
                'haber_listesi_selector': 'article, .post',
                'haber_baslik_selector': 'h2, h3, .title',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.date, time',
                'haber_ozet_selector': '.excerpt, p',
                'kategori': 'Judo'
            },
            {
                'ad': 'Türkiye Kickboks Federasyonu',
                'ana_url': 'https://www.tkbf.gov.tr',
                'haberler_url': 'https://www.tkbf.gov.tr/haberler',
                'haber_listesi_selector': '.news .item',
                'haber_baslik_selector': '.title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.date',
                'haber_ozet_selector': '.summary',
                'kategori': 'Kickboks'
            },
            {
                'ad': 'Türkiye Muay Thai Federasyonu',
                'ana_url': 'https://www.tmtf.gov.tr',
                'haberler_url': 'https://www.tmtf.gov.tr/haberler',
                'haber_listesi_selector': '.haber-listesi .haber',
                'haber_baslik_selector': '.haber-baslik',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.haber-tarih',
                'haber_ozet_selector': '.haber-ozet',
                'kategori': 'Muay Thai'
            }
        ]

        eklenen_federasyonlar = 0
        guncellenen_federasyonlar = 0

        for fed_data in federasyon_siteleri:
            try:
                # Check if federation website already exists
                federation, created = FederasyonWebsite.objects.get_or_create(
                    ad=fed_data['ad'],
                    defaults={
                        'ana_url': fed_data['ana_url'],
                        'haberler_url': fed_data['haberler_url'],
                        'haber_listesi_selector': fed_data['haber_listesi_selector'],
                        'haber_baslik_selector': fed_data['haber_baslik_selector'],
                        'haber_link_selector': fed_data['haber_link_selector'],
                        'haber_tarih_selector': fed_data['haber_tarih_selector'],
                        'haber_ozet_selector': fed_data['haber_ozet_selector'],
                        'aktif': True
                    }
                )
                
                if created:
                    eklenen_federasyonlar += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {fed_data["ad"]} eklendi')
                    )
                else:
                    # Update existing federation with new selectors
                    federation.ana_url = fed_data['ana_url']
                    federation.haberler_url = fed_data['haberler_url']
                    federation.haber_listesi_selector = fed_data['haber_listesi_selector']
                    federation.haber_baslik_selector = fed_data['haber_baslik_selector']
                    federation.haber_link_selector = fed_data['haber_link_selector']
                    federation.haber_tarih_selector = fed_data['haber_tarih_selector']
                    federation.haber_ozet_selector = fed_data['haber_ozet_selector']
                    federation.save()
                    
                    guncellenen_federasyonlar += 1
                    self.stdout.write(
                        self.style.WARNING(f'! {fed_data["ad"]} güncellendi')
                    )
                
                # Link category to federation if exists
                try:
                    kategori = Kategori.objects.get(ad=fed_data['kategori'])
                    kategori.federasyon_website = federation
                    kategori.save()
                except Kategori.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Kategori bulunamadı: {fed_data["kategori"]}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ {fed_data["ad"]} eklenirken hata: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🌐 İşlem tamamlandı! '
                f'{eklenen_federasyonlar} yeni federasyon eklendi, '
                f'{guncellenen_federasyonlar} federasyon güncellendi.'
            )
        )
        
        self.stdout.write('\n📝 Not: Bu CSS selector\'lar örnek amaçlıdır.')
        self.stdout.write('   Gerçek siteler için selector\'ları manuel olarak ayarlamanız gerekebilir.')
        self.stdout.write('\n📋 Kurulum adımları:')
        self.stdout.write('   1. python manage.py makemigrations')
        self.stdout.write('   2. python manage.py migrate')
        self.stdout.write('   3. python manage.py haber_cek --all  (haberleri çekmek için)')