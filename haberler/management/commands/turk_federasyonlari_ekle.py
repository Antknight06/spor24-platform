from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import FederasyonWebsite, Kategori

class Command(BaseCommand):
    help = 'Türkiye\'deki federasyon websitelerini ve CSS selector\'larını ekler'

    def handle(self, *args, **options):
        # Türkiye federasyon websiteleri ve CSS selector'ları
        turk_federasyonlari = [
            {
                'ad': 'Türkiye Boks Federasyonu',
                'ana_url': 'https://www.tbf.gov.tr',
                'haberler_url': 'https://www.tbf.gov.tr/haberler',
                'haber_listesi_selector': '.haberler .haber',
                'haber_baslik_selector': '.baslik, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.tarih',
                'haber_ozet_selector': '.ozet',
                'kategori': 'Boxing'
            },
            {
                'ad': 'Türkiye Güreş Federasyonu',
                'ana_url': 'https://www.tgf.gov.tr',
                'haberler_url': 'https://www.tgf.gov.tr/haberler',
                'haber_listesi_selector': '.news-list .item',
                'haber_baslik_selector': '.title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.date',
                'haber_ozet_selector': '.summary',
                'kategori': 'Güreş'
            },
            {
                'ad': 'Türkiye Kendo Federasyonu',
                'ana_url': 'https://www.turkiyekendofederasyonu.org',
                'haberler_url': 'https://www.turkiyekendofederasyonu.org/haberler',
                'haber_listesi_selector': '.haberler .post',
                'haber_baslik_selector': '.post-title, h2',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.post-date',
                'haber_ozet_selector': '.post-excerpt',
                'kategori': 'Kendo'
            },
            {
                'ad': 'Türkiye Kyokushin Federasyonu',
                'ana_url': 'https://www.tkyf.org',
                'haberler_url': 'https://www.tkyf.org/haberler',
                'haber_listesi_selector': '.news-container .article',
                'haber_baslik_selector': '.article-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.article-date',
                'haber_ozet_selector': '.article-summary',
                'kategori': 'Kyokushin'
            },
            {
                'ad': 'Türkiye Sambo Federasyonu',
                'ana_url': 'https://www.turkiyesambofederasyonu.org',
                'haberler_url': 'https://www.turkiyesambofederasyonu.org/haberler',
                'haber_listesi_selector': '.news-list .news-item',
                'haber_baslik_selector': '.news-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.news-date',
                'haber_ozet_selector': '.news-excerpt',
                'kategori': 'Sambo'
            },
            {
                'ad': 'Türkiye Capoeira Federasyonu',
                'ana_url': 'https://www.turkiyecapoeirafederasyonu.org',
                'haberler_url': 'https://www.turkiyecapoeirafederasyonu.org/haberler',
                'haber_listesi_selector': '.news-list .item',
                'haber_baslik_selector': '.news-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.news-date',
                'haber_ozet_selector': '.news-summary',
                'kategori': 'Capoeira'
            },
            {
                'ad': 'Türkiye Krav Maga Federasyonu',
                'ana_url': 'https://www.turkiyekravmagafederasyonu.org',
                'haberler_url': 'https://www.turkiyekravmagafederasyonu.org/haberler',
                'haber_listesi_selector': '.haberler .makale',
                'haber_baslik_selector': '.makale-baslik, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.makale-tarih',
                'haber_ozet_selector': '.makale-ozet',
                'kategori': 'Krav Maga'
            },
            {
                'ad': 'Türkiye Wrestling Federasyonu',
                'ana_url': 'https://www.turkeywrestling.org',
                'haberler_url': 'https://www.turkeywrestling.org/news',
                'haber_listesi_selector': '.news-feed .article',
                'haber_baslik_selector': '.article-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.article-date',
                'haber_ozet_selector': '.article-summary',
                'kategori': 'Wrestling'
            }
        ]

        eklenen_federasyonlar = 0
        guncellenen_federasyonlar = 0

        for fed_data in turk_federasyonlari:
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
                f'\n🇹🇷 İşlem tamamlandı! '
                f'{eklenen_federasyonlar} yeni Türk federasyonu eklendi, '
                f'{guncellenen_federasyonlar} federasyon güncellendi.'
            )
        )
        
        self.stdout.write('\n📝 Not: Bu CSS selector\'lar örnek amaçlıdır.')
        self.stdout.write('   Gerçek siteler için selector\'ları manuel olarak ayarlamanız gerekebilir.')