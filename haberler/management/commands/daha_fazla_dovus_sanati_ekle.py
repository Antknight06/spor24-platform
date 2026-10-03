from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import Kategori

class Command(BaseCommand):
    help = 'Daha fazla uluslararası yakın dövüş sanatı kategorilerini ekler'

    def handle(self, *args, **options):
        # Uluslararası federasyonlara sahip diğer yakın dövüş sanatları
        ek_dovus_sanatlari = [
            {
                'ad': 'Boxing',
                'aciklama': 'Uluslararası amateur ve profesyonel boks federasyonları tarafından yönetilen yumruk dövüş sporu'
            },
            {
                'ad': 'Capoeira',
                'aciklama': 'Brezilya kökenli dans ve dövüş sanatı'
            },
            {
                'ad': 'Krav Maga',
                'aciklama': 'İsrail kökenli askeri savunma sanatı'
            },
            {
                'ad': 'Kendo',
                'aciklama': 'Japonya\'da gelişen samuray kılıcı sanatı'
            },
            {
                'ad': 'Kyokushin',
                'aciklama': 'Japonya\'da geliştirilen tam temaslı karate stili'
            },
            {
                'ad': 'Lethwei',
                'aciklama': 'Myanmar kökenli tam temaslı dövüş sanatı'
            },
            {
                'ad': 'Mixed Martial Arts',
                'aciklama': 'Birden fazla dövüş sanatını birleştiren karma dövüş sporu'
            },
            {
                'ad': 'Pankration',
                'aciklama': 'Antik Yunan kökenli tam temaslı dövüş sanatı'
            },
            {
                'ad': 'Pencak Silat',
                'aciklama': 'Güneydoğu Asya kökenli dövüş sanatı'
            },
            {
                'ad': 'Sambo',
                'aciklama': 'Rusya kökenli askeri savunma ve dövüş sanatı'
            },
            {
                'ad': 'Sandhammaren',
                'aciklama': 'Norveç kökenli geleneksel dövüş sanatı'
            },
            {
                'ad': 'Savate',
                'aciklama': 'Fransa kökenli ayak ve yumruk dövüş sanatı'
            },
            {
                'ad': 'Shoot Boxing',
                'aciklama': 'Japonya kökenli ayak ve yumruk dövüş sporu'
            },
            {
                'ad': 'Systema',
                'aciklama': 'Rusya kökenli askeri savunma sanatı'
            },
            {
                'ad': 'Vale Tudo',
                'aciklama': 'Brezilya kökenli tam temaslı dövüş sporu'
            },
            {
                'ad': 'Vovinam',
                'aciklama': 'Vietnam kökenli dövüş sanatı'
            },
            {
                'ad': 'Wrestling',
                'aciklama': 'Uluslararası güreş federasyonları tarafından yönetilen geleneksel güreş sporu'
            },
            {
                'ad': 'Yoseikan Budo',
                'aciklama': 'Fransa kökenli çoklu dövüş sanatı'
            }
        ]

        eklenen_kategoriler = 0
        mevcut_kategoriler = 0

        for sanat in ek_dovus_sanatlari:
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