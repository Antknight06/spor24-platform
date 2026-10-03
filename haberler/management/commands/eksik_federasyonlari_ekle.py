from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import FederasyonWebsite, Kategori

class Command(BaseCommand):
    help = 'Eksik federasyon websitelerini ekler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n➕ EKSİK FEDERASYON WEBSİTELERİ EKLENİYOR\n')
        )
        self.stdout.write('=' * 60)
        
        # Eksik federasyon websiteleri
        eksik_federasyonlar = [
            {
                'ad': 'Türkiye Aikido Federasyonu',
                'ana_url': 'https://www.turkiyeaikidofederasyonu.org',
                'haberler_url': 'https://www.turkiyeaikidofederasyonu.org/haberler',
                'haber_listesi_selector': '.haberler .haber',
                'haber_baslik_selector': '.baslik, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.tarih',
                'haber_ozet_selector': '.ozet',
                'kategori': 'Aikido'
            },
            {
                'ad': 'Türkiye Kempo Federasyonu',
                'ana_url': 'https://www.turkiyekempofederasyonu.org',
                'haberler_url': 'https://www.turkiyekempofederasyonu.org/haberler',
                'haber_listesi_selector': '.news-list .item',
                'haber_baslik_selector': '.title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.date',
                'haber_ozet_selector': '.summary',
                'kategori': 'Kempo'
            },
            {
                'ad': 'Türkiye Wushu Kung Fu Federasyonu',
                'ana_url': 'https://www.turkeywushu.org',
                'haberler_url': 'https://www.turkeywushu.org/haberler',
                'haber_listesi_selector': '.haberler .post',
                'haber_baslik_selector': '.post-title, h2',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.post-date',
                'haber_ozet_selector': '.post-excerpt',
                'kategori': 'Wushu'
            },
            {
                'ad': 'Türkiye Savate Federasyonu',
                'ana_url': 'https://www.turkiyesavatefederasyonu.org',
                'haberler_url': 'https://www.turkiyesavatefederasyonu.org/haberler',
                'haber_listesi_selector': '.news-container .article',
                'haber_baslik_selector': '.article-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.article-date',
                'haber_ozet_selector': '.article-summary',
                'kategori': 'Savate'
            },
            {
                'ad': 'Türkiye Hapkido Federasyonu',
                'ana_url': 'https://www.turkiyehapkidofederasyonu.org',
                'haberler_url': 'https://www.turkiyehapkidofederasyonu.org/haberler',
                'haber_listesi_selector': '.news-list .news-item',
                'haber_baslik_selector': '.news-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.news-date',
                'haber_ozet_selector': '.news-excerpt',
                'kategori': 'Hapkido'
            },
            {
                'ad': 'Türkiye Karate-Do Federasyonu',
                'ana_url': 'https://www.turkiyekarate-dofederasyonu.org',
                'haberler_url': 'https://www.turkiyekarate-dofederasyonu.org/haberler',
                'haber_listesi_selector': '.haberler .makale',
                'haber_baslik_selector': '.makale-baslik, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.makale-tarih',
                'haber_ozet_selector': '.makale-ozet',
                'kategori': 'Karate-Do'
            },
            {
                'ad': 'Türkiye Ju Jitsu Federasyonu',
                'ana_url': 'https://www.turkiyejujitsufederasyonu.org',
                'haberler_url': 'https://www.turkiyejujitsufederasyonu.org/haberler',
                'haber_listesi_selector': '.news-feed .article',
                'haber_baslik_selector': '.article-title, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.article-date',
                'haber_ozet_selector': '.article-summary',
                'kategori': 'Jiu Jitsu'
            },
            {
                'ad': 'Türkiye Karma Dövüş Sanatları Federasyonu',
                'ana_url': 'https://www.turkeymma.org',
                'haberler_url': 'https://www.turkeymma.org/haberler',
                'haber_listesi_selector': '.haberler .item',
                'haber_baslik_selector': '.haber-baslik, h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': '.haber-tarih',
                'haber_ozet_selector': '.haber-ozet',
                'kategori': 'MMA'
            }
        ]

        eklenen_federasyonlar = 0
        guncellenen_federasyonlar = 0

        for fed_data in eksik_federasyonlar:
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
                f'\n✅ İşlem tamamlandı! '
                f'{eklenen_federasyonlar} yeni federasyon eklendi, '
                f'{guncellenen_federasyonlar} federasyon güncellendi.'
            )
        )
        
        # Final summary
        toplam_kategori = Kategori.objects.count()
        federasyonlu_kategori = Kategori.objects.filter(federasyon_website__isnull=False).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🏆 SON DURUM:'
                f'\n   • Toplam Kategori: {toplam_kategori}'
                f'\n   • Federasyonlu Kategori: {federasyonlu_kategori}'
                f'\n   • Federasyonsuz Kategori: {toplam_kategori - federasyonlu_kategori}'
            )
        )