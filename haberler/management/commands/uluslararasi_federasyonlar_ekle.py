from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import FederasyonWebsite, Kategori

class Command(BaseCommand):
    help = 'Uluslararası federasyon websitelerini ve CSS selector\'larını ekler'

    def handle(self, *args, **options):
        # Uluslararası federasyon websiteleri ve CSS selector'ları
        uluslararasi_federasyonlar = [
            {
                'ad': 'International Boxing Federation',
                'ana_url': 'https://www.ibfworld.com',
                'haberler_url': 'https://www.ibfworld.com/news',
                'haber_listesi_selector': '.news-item, .article',
                'haber_baslik_selector': '.title, h3, h2',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.date, time',
                'haber_ozet_selector': '.summary, .excerpt, p',
                'kategori': 'Boxing'
            },
            {
                'ad': 'World Capoeira Federation',
                'ana_url': 'https://www.capoeira.org',
                'haberler_url': 'https://www.capoeira.org/news',
                'haber_listesi_selector': '.news-list .item',
                'haber_baslik_selector': '.news-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.news-date',
                'haber_ozet_selector': '.news-summary',
                'kategori': 'Capoeira'
            },
            {
                'ad': 'International Kendo Federation',
                'ana_url': 'https://www.kendo-fik.org',
                'haberler_url': 'https://www.kendo-fik.org/news',
                'haber_listesi_selector': '.news .post',
                'haber_baslik_selector': '.post-title, h2',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.post-date',
                'haber_ozet_selector': '.post-excerpt',
                'kategori': 'Kendo'
            },
            {
                'ad': 'International Kyokushin Karate Federation',
                'ana_url': 'https://www.ikukf.com',
                'haberler_url': 'https://www.ikukf.com/news',
                'haber_listesi_selector': '.news-container .article',
                'haber_baslik_selector': '.article-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.article-date',
                'haber_ozet_selector': '.article-summary',
                'kategori': 'Kyokushin'
            },
            {
                'ad': 'International Mixed Martial Arts Federation',
                'ana_url': 'https://www.immaf.org',
                'haberler_url': 'https://www.immaf.org/news',
                'haber_listesi_selector': '.news-archive .post',
                'haber_baslik_selector': '.post-title, h2',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.post-date',
                'haber_ozet_selector': '.post-content p',
                'kategori': 'Mixed Martial Arts'
            },
            {
                'ad': 'International Sambo Federation',
                'ana_url': 'https://www.fiasambo.com',
                'haberler_url': 'https://www.fiasambo.com/news',
                'haber_listesi_selector': '.news-list .news-item',
                'haber_baslik_selector': '.news-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.news-date',
                'haber_ozet_selector': '.news-excerpt',
                'kategori': 'Sambo'
            },
            {
                'ad': 'United World Wrestling',
                'ana_url': 'https://www.unitedworldwrestling.org',
                'haberler_url': 'https://www.unitedworldwrestling.org/news',
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

        for fed_data in uluslararasi_federasyonlar:
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