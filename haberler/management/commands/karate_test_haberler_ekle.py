from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite, Haber, Kategori
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

class Command(BaseCommand):
    help = 'karate.gov.tr için test haberleri ekler'

    def handle(self, *args, **options):
        try:
            # karate.gov.tr federasyonunu al
            federation = FederasyonWebsite.objects.get(
                ad='Türkiye Karate Federasyonu (Resmi)'
            )
        except FederasyonWebsite.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    '❌ karate.gov.tr federasyonu bulunamadı. '
                    'Önce şu komutu çalıştırın: python ANT_News\\manage.py karate_gov_tr_ekle'
                )
            )
            return

        # Bot kullanıcı al/oluştur
        bot_user, _ = User.objects.get_or_create(
            username='karatebot',
            defaults={
                'email': 'karatebot@netspor.com',
                'first_name': 'Karate',
                'last_name': 'Bot',
                'is_active': True
            }
        )
        
        # Kategori al/oluştur
        kategori, _ = Kategori.objects.get_or_create(
            slug='karate',
            defaults={
                'ad': 'Karate',
                'aciklama': 'Karate haberleri ve duyuruları',
                'federasyon_website': federation
            }
        )
        
        # Test haberleri (gerçek karate.gov.tr'den)
        test_haberler = [
            {
                'title': 'Suudi Antrenörler Derneği Başkanı\'ndan Dostluk Plaketi',
                'summary': 'Suudi Arabistan Antrenörler Derneği Başkanı Ali Alzahrani, Türkiye Karate Federasyonu Başkanımız Ercüment Taşdemir\'e plaket takdiminde bulundu.',
                'content': 'Suudi Arabistan Antrenörler Derneği Başkanı, Başkanımız Ercüment Taşdemir\'in 14 yıllık dostu ve başarılarla dolu kariyeriyle tanınan Ali Alzahrani, Türkiye Karate Federasyonu Başkanımız Ercüment Taşdemir\'e plaket takdiminde bulundu.',
                'date': '02 Eylül 2025 22:47',
                'url': 'https://karate.gov.tr/haber/suudi-antrenorler-dernegi-baskanından-dostluk-plaketi-344'
            },
            {
                'title': 'Milli Takımımız Basel\'de Zirvede',
                'summary': 'Basel\'de düzenlenen uluslararası turnuvada Türk milli takımı zirveye çıktı.',
                'content': 'Basel\'de düzenlenen prestijli karate turnuvasında Türkiye Milli Takımı büyük başarı göstererek zirvede yer aldı.',
                'date': '31 Ağustos 2025 15:17',
                'url': 'https://karate.gov.tr/haber/milli-takimimiz-baselde-zirvede-343'
            },
            {
                'title': 'Uluslararası Marmara Cup Karate Şampiyonası Tamamlandı',
                'summary': 'Başakşehir\'de düzenlenen Marmara Cup Karate Şampiyonası başarıyla sona erdi.',
                'content': 'Başakşehir Spor Salonu\'nda düzenlenen Uluslararası Marmara Cup Karate Şampiyonası başarıyla tamamlandı. 22-24 Ağustos 2025 tarihlerinde gerçekleştirilen organizasyon büyük ilgi gördü.',
                'date': '24 Ağustos 2025 20:37',
                'url': 'https://karate.gov.tr/haber/uluslararasi-marmara-cup-karate-sampiyonasi-tamamlandi-342'
            },
            {
                'title': 'Türkiye Premier Ligi Rıdvan Gümüş Etabı Diyarbakır\'da Tamamlandı',
                'summary': 'Diyarbakır\'da düzenlenen Premier Lig etabı başarıyla sona erdi.',
                'content': 'Türkiye Karate Premier Ligi Rıdvan Gümüş Etabı Diyarbakır\'da coşkulu bir şekilde tamamlandı. Müsabakalar büyük heyecan yaşattı.',
                'date': '11 Ağustos 2025 10:15',
                'url': 'https://karate.gov.tr/haber/turkiye-premier-ligi-ridvan-gumus-etabi-diyarbakir-tamamlandi-341'
            },
            {
                'title': 'Eray Şamdan Dünya Şampiyonu',
                'summary': 'Genç sporcu Eray Şamdan dünya şampiyonluğu kazandı.',
                'content': 'Türk karateci Eray Şamdan uluslararası müsabakada dünya şampiyonu olarak Türkiye\'nin gururu oldu.',
                'date': '08 Ağustos 2025 16:48',
                'url': 'https://karate.gov.tr/haber/eray-samdan-dunya-sampiyonu-340'
            }
        ]
        
        imported_count = 0
        
        for haber_data in test_haberler:
            try:
                # Haber zaten var mı kontrol et
                if Haber.objects.filter(kaynak_url=haber_data['url']).exists():
                    self.stdout.write(f'⚠️  Haber zaten mevcut: {haber_data["title"][:50]}...')
                    continue
                
                # Benzersiz slug oluştur
                base_slug = slugify(haber_data['title'])
                slug = base_slug
                counter = 1
                while Haber.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Haberi oluştur
                haber = Haber.objects.create(
                    baslik=haber_data['title'][:200],
                    slug=slug,
                    ozet=haber_data['summary'][:500],
                    icerik=haber_data['content'],
                    kategori=kategori,
                    yazar=bot_user,
                    kaynak_url=haber_data['url'],
                    federasyon_website=federation,
                    otomatik_eklendi=True,
                    yayinlandi=True,
                    anasayfa_haberi=True  # Ana sayfada göster
                )
                
                imported_count += 1
                self.stdout.write(f'✅ Test haberi eklendi: {haber_data["title"][:50]}...')
                
            except Exception as e:
                self.stdout.write(f'❌ Hata: {haber_data["title"][:50]}... - {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! {imported_count} test haberi eklendi.'
            )
        )
        
        # Son tarama zamanını güncelle
        federation.son_tarama = timezone.now()
        federation.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📺 Artık ana sayfada karate haberlerini görebilirsiniz!'
            )
        )