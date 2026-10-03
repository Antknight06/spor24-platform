from django.core.management.base import BaseCommand
from haberler.models import Haber, Kategori
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

class Command(BaseCommand):
    help = 'Karate kategorisi için test köşe yazıları ekler'

    def handle(self, *args, **options):
        try:
            # Karate kategorisini al
            karate_kategori = Kategori.objects.get(slug='karate')
        except Kategori.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Karate kategorisi bulunamadı.')
            )
            return

        # Yazar kullanıcı al/oluştur
        yazar, _ = User.objects.get_or_create(
            username='kose_yazari',
            defaults={
                'email': 'kose@netspor.com',
                'first_name': 'Köşe',
                'last_name': 'Yazarı',
                'is_active': True
            }
        )
        
        # Test köşe yazıları
        kose_yazilari = [
            {
                'title': 'Karatede Zihinsel Hazırlığın Önemi',
                'summary': 'Karate sporcularının fiziksel antrenmanın yanı sıra zihinsel hazırlığa da odaklanması gerektiğini anlatan deneyim yazısı.',
                'content': '''Karate sadece fiziksel bir spor değildir. Gerçek bir karateci olmak için zihin ve beden uyumunun sağlanması gerekir. 
                
Yıllardır karate antrenörlüğü yapan biri olarak gözlemlediğim en önemli konu, sporcuların zihinsel hazırlığa verdiği önemin eksikliğidir. Fiziksel antrenman tabii ki çok önemli, ancak zihinsel hazırlık olmadan başarıya ulaşmak mümkün değildir.

Meditasyon, konsantrasyon egzersizleri ve görselleştirme teknikleri, karate antrenmanının ayrılmaz parçaları olmalıdır. Bu konuda federasyonumuzun daha fazla çalışma yapması gerektiğini düşünüyorum.'''
            },
            {
                'title': 'Gençlerde Karate: Sadece Spor Değil, Hayat Felsefesi',
                'summary': 'Karatenin gençler üzerindeki olumlu etkilerini ve karakterlerine katkısını anlatan köşe yazısı.',
                'content': '''Bugünün gençleri teknolojinin içinde büyüyor ve ne yazık ki fiziksel aktiviteden uzaklaşıyorlar. Bu noktada karate gibi geleneksel dövüş sanatları, sadece fiziksel gelişim değil, aynı zamanda karakter gelişimi için de büyük fırsatlar sunuyor.

Karate, disiplin, saygı, sebat ve öz-güven gibi değerleri öğretir. Bu değerler, gençlerin hem spor hayatında hem de günlük yaşamlarında başarılı olmalarına yardımcı olur.

Aileler karate sporu konusunda daha bilinçli hale gelmeli ve çocuklarını bu değerli sporla tanıştırmalıdır.'''
            },
            {
                'title': 'Türk Karatesi ve Uluslararası Başarılar',
                'summary': 'Türk karatecilerin uluslararası arenada elde ettiği başarıların analizi ve gelecek için öneriler.',
                'content': '''Son yıllarda Türk karateciler uluslararası müsabakalarda kayda değer başarılar elde ediyor. Bu başarıların arkasında elbette sporcularin azmi, antrenörlerin özverisi ve federasyonumuzun destekleri yatıyor.

Ancak daha üst seviyeye çıkabilmek için altyapıya daha fazla yatırım yapmamız gerekiyor. Özellikle il ve ilçe düzeyinde karate kulüplerinin yaygınlaştırılması, genç yeteneklerin keşfedilmesi açısından kritik öneme sahip.

Olimpiyat oyunlarında karate sporu ne yazık ki programa dahil edilmedi, ancak bu durum bizim motivasyonumuzu düşürmemeli. Dünya şampiyonalarında ve diğer prestijli turnuvalarda ülkemizi temsil etmeye devam edeceğiz.'''
            }
        ]
        
        imported_count = 0
        
        for yazı_data in kose_yazilari:
            try:
                # Yazı zaten var mı kontrol et
                base_slug = slugify(yazı_data['title'])
                if Haber.objects.filter(slug=base_slug).exists():
                    self.stdout.write(f'⚠️  Köşe yazısı zaten mevcut: {yazı_data["title"][:50]}...')
                    continue
                
                # Benzersiz slug oluştur
                slug = base_slug
                counter = 1
                while Haber.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Köşe yazısını oluştur
                haber = Haber.objects.create(
                    baslik=yazı_data['title'][:200],
                    slug=slug,
                    ozet=yazı_data['summary'][:500],
                    icerik=yazı_data['content'],
                    kategori=karate_kategori,
                    yazar=yazar,
                    otomatik_eklendi=False,
                    yayinlandi=True,
                    anasayfa_haberi=False,
                    kose_yazisi=True  # Köşe yazısı olarak işaretle
                )
                
                imported_count += 1
                self.stdout.write(f'✅ Köşe yazısı eklendi: {yazı_data["title"][:50]}...')
                
            except Exception as e:
                self.stdout.write(f'❌ Hata: {yazı_data["title"][:50]}... - {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! {imported_count} köşe yazısı eklendi.'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📰 Artık Karate kategorisinde köşe yazıları bölümünü görebilirsiniz!'
            )
        )