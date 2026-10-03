from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from haberler.models import FederasyonWebsite, Kategori, Haber

class Command(BaseCommand):
    help = 'Federasyon sitelerinden çekilmiş gibi demo haberler ekler'

    def handle(self, *args, **options):
        # Get or create bot user
        bot_user, created = User.objects.get_or_create(
            username='newsbot',
            defaults={
                'email': 'newsbot@antnews.com',
                'first_name': 'News',
                'last_name': 'Bot',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ News bot kullanıcısı oluşturuldu'))
        
        # Demo federation news
        demo_haberler = [
            {
                'federation': 'Türkiye Karate Federasyonu',
                'kategori': 'Karate',
                'haberler': [
                    {
                        'baslik': 'Karate Milli Takımı Avrupa Şampiyonası\'na Hazırlanıyor',
                        'ozet': 'Milli karate takımımız, önümüzdeki ay düzenlenecek Avrupa Şampiyonası için yoğun antrenman programına başladı.',
                        'icerik': 'Türkiye Karate Federasyonu tarafından açıklanan programa göre, milli sporcular İstanbul\'da toplanarak özel antrenman kampına alınacak. Teknik direktör ve antrenörler, sporcuların kondisyon ve teknik seviyelerini en üst düzeye çıkarmak için kapsamlı bir program hazırladı. Şampiyonada 15 kategoride yarışacak olan milli takımımız, geçen yıl aldığı başarılı sonuçları tekrarlamayı hedefliyor.',
                        'kaynak_url': 'https://www.turkiyekaratefederasyonu.gov.tr/haber-1'
                    },
                    {
                        'baslik': 'İl Şampiyonaları Takvimi Açıklandı',
                        'ozet': 'Türkiye Karate Federasyonu, 2024-2025 sezonunun il şampiyonalarının tarihlerini ve mekanlarını duyurdu.',
                        'icerik': 'Federasyon başkanı tarafından yapılan açıklamada, il şampiyonalarının Ekim ayından başlayarak Aralık ayına kadar süreceği belirtildi. Şampiyonalara katılacak sporcuların kayıt işlemleri bu hafta başlıyor. Her ilde yaş kategorilerine göre düzenlenecek müsabakalar, bölgesel eleme niteliği taşıyacak.',
                        'kaynak_url': 'https://www.turkiyekaratefederasyonu.gov.tr/haber-2'
                    }
                ]
            },
            {
                'federation': 'Türkiye Taekwondo Federasyonu',
                'kategori': 'Taekwondo',
                'haberler': [
                    {
                        'baslik': 'Taekwondo A Milli Takımı Paris\'te Kampta',
                        'ozet': 'A Milli Taekwondo Takımımız, Dünya Şampiyonası hazırlıkları kapsamında Paris\'te antrenman kampına başladı.',
                        'icerik': 'Fransa\'nın başkenti Paris\'te düzenlenen antrenman kampında, dünya şampiyonası için form tutan milli sporcular yer alıyor. Kamp süresince sporcular, uluslararası arenada başarı sağlamış antrenörlerle çalışarak teknik ve taktik gelişimlerini sürdürecek. Federasyon yetkilileri, kampın sporculara büyük katkı sağlayacağını belirtti.',
                        'kaynak_url': 'https://www.turkiyetaekwondofederasyonu.gov.tr/haber-1'
                    }
                ]
            },
            {
                'federation': 'Türkiye Judo Federasyonu',
                'kategori': 'Judo',
                'haberler': [
                    {
                        'baslik': 'Judo Gençler Türkiye Şampiyonası Sonuçlandı',
                        'ozet': 'Ankara\'da düzenlenen Gençler Türkiye Judo Şampiyonası\'nda 16 kategoride madalyalar sahiplerini buldu.',
                        'icerik': 'Atatürk Spor Salonu\'nda gerçekleştirilen şampiyonaya 45 ilden toplamda 380 sporcu katıldı. İki gün süren müsabakaların sonunda her kategoride birinci, ikinci ve iki üçüncülük derecesi belirlendi. Federasyon başkanı, gençlerin gösterdiği performanstan memnun olduklarını ve gelecek adına umutlu olduklarını ifade etti.',
                        'kaynak_url': 'https://www.turkiyejudofederasyonu.org.tr/haber-1'
                    }
                ]
            }
        ]
        
        eklenen_haberler = 0
        
        for fed_data in demo_haberler:
            try:
                # Get federation and category
                federation = FederasyonWebsite.objects.get(ad=fed_data['federation'])
                kategori = Kategori.objects.get(ad=fed_data['kategori'])
                
                for haber_data in fed_data['haberler']:
                    # Check if news already exists
                    if Haber.objects.filter(kaynak_url=haber_data['kaynak_url']).exists():
                        continue
                    
                    # Generate unique slug
                    base_slug = slugify(haber_data['baslik'])
                    slug = base_slug
                    counter = 1
                    while Haber.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    
                    # Create news
                    haber = Haber.objects.create(
                        baslik=haber_data['baslik'],
                        slug=slug,
                        ozet=haber_data['ozet'],
                        icerik=haber_data['icerik'],
                        kategori=kategori,
                        yazar=bot_user,
                        kaynak_url=haber_data['kaynak_url'],
                        federasyon_website=federation,
                        otomatik_eklendi=True,
                        yayinlandi=True,
                        anasayfa_haberi=True
                    )
                    
                    eklenen_haberler += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {haber_data["baslik"][:50]}... eklendi')
                    )
                    
            except (FederasyonWebsite.DoesNotExist, Kategori.DoesNotExist) as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Hata: {str(e)}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Demo tamamlandı! {eklenen_haberler} örnek haber eklendi.'
            )
        )
        
        # Update federation last scraping time
        FederasyonWebsite.objects.filter(aktif=True).update(
            son_tarama=timezone.now()
        )
        
        self.stdout.write('\n📊 Sistem Özeti:')
        total_federations = FederasyonWebsite.objects.filter(aktif=True).count()
        total_categories = Kategori.objects.count()
        total_auto_news = Haber.objects.filter(otomatik_eklendi=True).count()
        
        self.stdout.write(f'   • Aktif federasyon siteleri: {total_federations}')
        self.stdout.write(f'   • Toplam kategoriler: {total_categories}')
        self.stdout.write(f'   • Otomatik eklenen haberler: {total_auto_news}')
        
        self.stdout.write('\n✨ Haber çekme sistemi hazır!')
        self.stdout.write('   Admin panelinden federasyon sitelerinin CSS selectorlarını')
        self.stdout.write('   gerçek değerlerle güncelledikten sonra "python manage.py haber_cek --all"')
        self.stdout.write('   komutuyla haberleri otomatik olarak çekebilirsiniz.')