from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from haberler.models import Kategori, Haber

class Command(BaseCommand):
    help = 'Dövüş sanatları kategorileri için örnek haberler oluşturur'

    def handle(self, *args, **options):
        # Admin kullanıcısını al
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin kullanıcı bulunamadı. Önce admin oluşturun.')
            )
            return

        # Örnek haberler
        ornek_haberler = [
            {
                'kategori': 'Karate',
                'baslik': 'Türkiye Karate Federasyonu Yeni Sezon Hazırlıklarını Tamamladı',
                'ozet': 'Türkiye Karate Federasyonu, 2024-2025 sezonuna yönelik hazırlıklarını tamamlayarak yeni dönem planlarını açıkladı.',
                'icerik': '''Türkiye Karate Federasyonu Başkanı, yeni sezon öncesi yaptığı açıklamada, "Bu sezon daha fazla sporcu yetiştirme hedefiyle çalışıyoruz. Gençlerimize karate sporunun disiplinini ve değerlerini aktarmaya devam edeceğiz" dedi.

Federasyon, bu sezon içerisinde:
- 50 il şampiyonası
- Ulusal gençler şampiyonası
- Türkiye Şampiyonası
- Uluslararası turnuvalar

düzenlemeyi planlıyor. Ayrıca antrenör eğitim programları da güçlendirilecek.'''
            },
            {
                'kategori': 'Taekwondo',
                'baslik': 'Olimpiyat Şampiyonu Mete Gazoz Taekwondo Sporcularıyla Buluştu',
                'ozet': 'Olimpiyat şampiyonu okçu Mete Gazoz, Taekwondo Federasyonu\'nun davetlisi olarak genç sporcularla motivasyon toplantısı gerçekleştirdi.',
                'icerik': '''Milli Okçu Mete Gazoz, Türkiye Taekwondo Federasyonu'nun düzenlediği motivasyon etkinliğinde genç taekwondocularla bir araya geldi. Gazoz, "Sporda başarının anahtarı disiplin ve azimdir" diyerek gençlere önemli tavsiyelerde bulundu.

Etkinlikte konuşan Taekwondo Federasyonu Başkanı da, "Sporcularımızın moralini yüksek tutmak ve onlara rol model sunmak için böyle etkinlikler düzenlemeye devam edeceğiz" açıklamasını yaptı.'''
            },
            {
                'kategori': 'MMA',
                'baslik': 'Türkiye MMA Şampiyonası Tarihleri Belli Oldu',
                'ozet': 'Türkiye Karma Dövüş Sanatları Federasyonu, 2024 yılının en önemli turnuvası olan Türkiye MMA Şampiyonası\'nın tarihlerini açıkladı.',
                'icerik': '''Türkiye Karma Dövüş Sanatları Federasyonu, merakla beklenen Türkiye MMA Şampiyonası'nın 15-17 Kasım 2024 tarihleri arasında İstanbul'da düzenleneceğini duyurdu.

Şampiyonaya katılım koşulları:
- 18-35 yaş arası olmak
- Lisanslı sporcu olmak
- Sağlık raporu sunmak
- Amatör statüde olmak

Federasyon Başkanı, "Bu şampiyona Türk MMA'sının geleceği için çok önemli. En iyi sporcularımızı göreceğiz" dedi.'''
            }
        ]

        eklenen_haberler = 0

        for haber_data in ornek_haberler:
            try:
                kategori = Kategori.objects.get(ad=haber_data['kategori'])
                slug = slugify(haber_data['baslik'])
                
                # Haber zaten var mı kontrol et
                if not Haber.objects.filter(slug=slug).exists():
                    Haber.objects.create(
                        baslik=haber_data['baslik'],
                        slug=slug,
                        ozet=haber_data['ozet'],
                        icerik=haber_data['icerik'],
                        kategori=kategori,
                        yazar=admin_user,
                        yayinlandi=True,
                        anasayfa_haberi=True
                    )
                    eklenen_haberler += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {haber_data["baslik"][:50]}... haberi eklendi')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'! Haber zaten mevcut: {haber_data["baslik"][:50]}...')
                    )
            except Kategori.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Kategori bulunamadı: {haber_data["kategori"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n📰 İşlem tamamlandı! {eklenen_haberler} örnek haber eklendi.')
        )