from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import Kategori

class Command(BaseCommand):
    help = 'Türkiye\'de federasyonu olan yakın dövüş sanatları kategorilerini ekler'

    def handle(self, *args, **options):
        # Türkiye'de federasyonu olan yakın dövüş sanatları
        dovus_sanatlari = [
            {
                'ad': 'Karate',
                'aciklama': 'Türkiye Karate Federasyonu tarafından yönetilen geleneksel Japon dövüş sanatı'
            },
            {
                'ad': 'Taekwondo',
                'aciklama': 'Türkiye Taekwondo Federasyonu tarafından yönetilen Kore kökenli dövüş sanatı'
            },
            {
                'ad': 'Judo',
                'aciklama': 'Türkiye Judo Federasyonu tarafından yönetilen Japon kökenli güreş sanatı'
            },
            {
                'ad': 'Kickboks',
                'aciklama': 'Türkiye Kick Boks Federasyonu tarafından yönetilen modern dövüş sporu'
            },
            {
                'ad': 'Muay Thai',
                'aciklama': 'Türkiye Muay Thai Federasyonu tarafından yönetilen Tayland kökenli dövüş sanatı'
            },
            {
                'ad': 'Aikido',
                'aciklama': 'Türkiye Aikido Federasyonu tarafından yönetilen Japon kökenli savunma sanatı'
            },
            {
                'ad': 'Kempo',
                'aciklama': 'Türkiye Kempo Federasyonu tarafından yönetilen geleneksel dövüş sanatı'
            },
            {
                'ad': 'Wushu',
                'aciklama': 'Türkiye Wushu Kung Fu Federasyonu tarafından yönetilen Çin kökenli dövüş sanatı'
            },
            {
                'ad': 'Savate',
                'aciklama': 'Türkiye Savate Federasyonu tarafından yönetilen Fransız kökenli ayak boksu'
            },
            {
                'ad': 'Hapkido',
                'aciklama': 'Türkiye Hapkido Federasyonu tarafından yönetilen Kore kökenli savunma sanatı'
            },
            {
                'ad': 'Karate-Do',
                'aciklama': 'Türkiye Karate-Do Federasyonu tarafından yönetilen geleneksel karate'
            },
            {
                'ad': 'Ju Jitsu',
                'aciklama': 'Türkiye Ju Jitsu Federasyonu tarafından yönetilen Japon kökenli dövüş sanatı'
            },
            {
                'ad': 'MMA',
                'aciklama': 'Türkiye Karma Dövüş Sanatları Federasyonu tarafından yönetilen karma dövüş sporu'
            },
            {
                'ad': 'Boks',
                'aciklama': 'Türkiye Boks Federasyonu tarafından yönetilen yumruk dövüş sporu'
            },
            {
                'ad': 'Güreş',
                'aciklama': 'Türkiye Güreş Federasyonu tarafından yönetilen geleneksel güreş sporu'
            }
        ]

        eklenen_kategoriler = 0
        mevcut_kategoriler = 0

        for sanat in dovus_sanatlari:
            slug = slugify(sanat['ad'])
            
            # Kategori zaten var mı kontrol et
            if not Kategori.objects.filter(slug=slug).exists():
                Kategori.objects.create(
                    ad=sanat['ad'],
                    slug=slug,
                    aciklama=sanat['aciklama']
                )
                eklenen_kategoriler += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {sanat["ad"]} kategorisi eklendi')
                )
            else:
                mevcut_kategoriler += 1
                self.stdout.write(
                    self.style.WARNING(f'! {sanat["ad"]} kategorisi zaten mevcut')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🥋 İşlem tamamlandı! '
                f'{eklenen_kategoriler} yeni kategori eklendi, '
                f'{mevcut_kategoriler} kategori zaten mevcuttu.'
            )
        )