from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from haberler.models import Kategori, Haber
from django.utils import timezone

class Command(BaseCommand):
    help = 'Özel dosya haberleri ve arka plan analizleri ekler'

    def handle(self, *args, **options):
        # Admin kullanıcısını al
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Admin kullanıcı bulunamadı. Önce admin oluşturun.')
            )
            return

        # Özel dosya haberleri
        ozel_haberler = [
            {
                'kategori': 'Karate',
                'baslik': 'Türkiye Karate Sporunda Son 10 Yılın Analizi: Başarıların Perde Arkası',
                'ozet': 'Son on yılda Türk karate sporunun kaydettiği gelişim, uluslararası başarılar ve gelecek projeksiyonlarına derinlemesine bakış.',
                'icerik': '''Son on yılda Türkiye karate sporu, dünya çapında dikkat çeken bir dönüşüm yaşadı. 2014 yılından itibaren federasyonun uyguladığı stratejik planlar, bugün elde edilen başarıların temelini oluşturuyor.

**Başarının Temelleri:**

**1. Altyapı Yatırımları (2014-2018)**
Türkiye Karate Federasyonu, 2014 yılında başlattığı "Karate 2023 Vizyonu" ile köklü değişikliklere imza attı. Bu dönemde:
- 81 ilde modern karate salonları kuruldu
- Antrenör sayısı %300 arttı
- Lisanslı sporcu sayısı 50.000'i aştı
- Hakem eğitim programları uluslararası standartlara çıkarıldı

**2. Uluslararası İşbirlikleri (2018-2021)**
Federasyon, dünya karate camiası ile güçlü bağlar kurdu:
- Japonya Karate Federasyonu ile kardeş anlaşma
- WKF ile stratejik ortaklık protokolü
- Avrupa şampiyonalarına ev sahipliği
- Dünya çapında 15 ülke ile sporcu değişim programı

**3. Teknoloji Entegrasyonu (2021-2024)**
Modern teknolojinin karate sporuna entegre edilmesi:
- Video analiz sistemleri
- Performans ölçüm teknolojileri
- Online antrenman platformları
- Yapay zeka destekli takım analizi

**İstatistiksel Başarılar:**

Son 5 yılda Türk karatecilerin kazandığı madalyalar:
- Dünya Şampiyonası: 12 madalya
- Avrupa Şampiyonası: 28 madalya
- Olimpiyat Oyunları: 2 madalya
- Dünya Üniversiteler Şampiyonası: 15 madalya

**Başarı Hikayeleri:**

**Eray Şamdan Fenomeni:**
21 yaşındaki Eray Şamdan'ın dünya şampiyonluğu, Türk karate tarihinin dönüm noktalarından biri. Diyarbakır'dan çıkarak dünya zirvesine ulaşan genç sporcu, sistematik antrenman programlarının nasıl sonuç verdiğinin canlı örneği.

**Kadın Karatecierin Yükselişi:**
2020 yılından itibaren kadın karatecilerin başarı grafiği dikkat çekici. Özellikle kata branşında kaydedilen gelişmeler, Türkiye'yi dünya sıralamasında üst sıralara taşıdı.

**Gelecek Projeksiyonları:**

**2025-2030 Dönemi Hedefleri:**
- Paris 2024 Olimpiyatları'nda 3 madalya hedefi
- Dünya sıralamasında ilk 3'e girme
- Lisanslı sporcu sayısını 100.000'e çıkarma
- 25 ilde Karate Mükemmellik Merkezi açma

**Zorluklar ve Fırsatlar:**
Ana zorluklar arasında sporcu emekliliği, finansman ve uluslararası rekabet yer alıyor. Ancak genç nüfus, artan ilgi ve devlet desteği önemli fırsatlar sunuyor.

**Sonuç:**
Türkiye karate sporu, sağlam temeller üzerine kurduğu başarı hikayesini gelecekte de sürdürecek potansiyele sahip. Sistematik yaklaşım, bilimsel metodlar ve özverili çalışmanın birleşimi, Türk karate sporunu dünya zirvesine taşıyacak güçte.

*Bu analiz, federasyon verileri, uluslararası istatistikler ve uzman görüşleri doğrultusunda hazırlanmıştır.*''',
                'kose_yazisi': True
            },
            {
                'kategori': 'Taekwondo',
                'baslik': 'Olimpiyat Yolunda Türk Taekwondosu: Paris 2024 Hazırlıkları ve Beklentiler',
                'ozet': 'Paris 2024 Olimpiyatları öncesi Türk taekwondo takımının hazırlık süreci, şampiyonluk adayları ve medal beklentileri.',
                'icerik': '''Paris 2024 Olimpiyat Oyunları, Türk taekwondo sporu için kritik bir dönemeç. Son dönemde kaydedilen başarılar, olimpiyat madalyası beklentilerini artırırken, hazırlık süreci de yoğun bir şekilde devam ediyor.

**Hazırlık Sürecinin Anatomisi:**

**Bilimsel Antrenman Metodları:**
Türkiye Taekwondo Federasyonu, Paris 2024 için 3 yıllık bilimsel hazırlık programı uyguluyor:
- Kişiselleştirilmiş antrenman planları
- Beslenme ve psikoloji desteği
- Video analiz teknolojisi
- Biomekanik performans ölçümü

**Milli Takım Kamıları:**
2023 yılında düzenlenen 8 farklı kamp:
- Antalya Yüksek İrtifa Kampı (3 kez)
- Kore Teknik Gelişim Kampı
- Almanya Sparring Kampı
- İspanya Taktik Gelişim Kampı

**Şampiyonluk Adayları:**

**Hatice Kübra İlgün (57 kg):**
- Dünya sıralaması: 3. sıra
- Son 2 yılda 5 uluslararası şampiyonluk
- Güçlü yönleri: Hız ve teknik mükemmellik
- Hedef: Altın madalya

**Nafia Kuş (67 kg):**
- Avrupa şampiyonu (2023)
- Dünya şampiyonası gümüş madalyası
- Güçlü yönleri: Fiziksel güç ve dayanıklılık
- Hedef: Podium garanti

**Erkekler Kategorisi Umutları:**
- Hakan Reçber (68 kg): Dünya sıralaması 5. sıra
- Mahmut Eken (80 kg): Avrupa şampiyonluğu deneyimi

**Teknik Analiz:**

**Güçlü Yönler:**
- Kick teknikleri mükemmelliği
- Psikolojik dayanıklılık
- Takım ruhu ve motivasyon
- Antrenör kadrosu deneyimi

**Gelişim Alanları:**
- Savunma stratejilerinde çeşitlilik
- Yorgunluk yönetimi
- Hakem kararlarına adaptasyon

**Olimpiyat Stratejisi:**

**1. Grup Aşaması Taktiği:**
- İlk maçlarda fiziksel güç saklamalı
- Rakip analizi önceden yapılmalı
- Sakatlanma riskini minimize etmeli

**2. Eleme Maçları Yaklaşımı:**
- Psikolojik baskı yönetimi
- Taktik değişkenliği
- Son saniye konsantrasyonu

**Beklentiler ve Gerçekler:**

**Optimist Senaryo:**
- 2-3 madalya (1 altın, 2 bronz)
- Türkiye'nin en başarılı olimpiyat performansı
- Taekwondo sporunda yeni bir çağ

**Realist Beklenti:**
- 1-2 madalya garantisi
- Yarı final başarıları
- Gelecek olimpiyatlara güçlü altyapı

**Finansal ve Lojistik Destek:**

Gençlik ve Spor Bakanlığı'nın Paris 2024 için tahsis ettiği özel bütçe:
- Antrenman kampları: 2.5 milyon TL
- Ekipman ve teknoloji: 1.8 milyon TL
- Uzman desteği: 1.2 milyon TL
- Lojistik giderler: 3 milyon TL

**Psikolojik Hazırlık:**

Spor psikologu Dr. Mehmet Özkan'ın liderliğindeki ekip:
- Bireysel terapi seansları
- Grup motivasyon çalışmaları
- Stres yönetimi teknikleri
- Olimpiyat atmosferi simülasyonu

**Sonuç ve Değerlendirme:**

Paris 2024, Türk taekwondo sporunun uluslararası arenada konumunu pekiştirecek fırsat. Hazırlık sürecinin kalitesi, sporcuların motivasyonu ve teknik kadronun deneyimi, madalya beklentilerini haklı çıkaracak düzeyde.

Her ne kadar sport alanı öngörülemeyen gelişmelere açık olsa da, mevcut veriler Türkiye'nin Paris'te taekwondo sporunda tarihinin en başarılı olimpiyat performansını sergileyebileceğini gösteriyor.

*Bu rapor, federasyon yetkilileri, teknik direktör ve sporcularla yapılan mülakatlar temelinde hazırlanmıştır.*''',
                'kose_yazisi': True
            },
            {
                'kategori': 'Judo',
                'baslik': 'Türk Judosunda Yeni Nesil: Genç Yeteneklerin Yükselişi ve Gelecek Planları',
                'ozet': 'Son yıllarda öne çıkan genç judo yetenekleri, onları başarıya taşıyan faktörler ve Türk judosunun geleceğine dair analiz.',
                'icerik': '''Türk judo sporunda son beş yılda yaşanan genç yetenek patlaması, sadece şimdiki başarıları değil, geleceğin garanti edilmiş projeksiyonlarını da gözler önüne seriyor. Bu derinlemesine analiz, yeni nesil judocuların hikayesini ve Türk judosunun gelecek yol haritasını ele alıyor.

**Genç Yetenek Devrimi:**

**İstatistiksel Çerçeve:**
- 18 yaş altı kategoride dünya sıralamasında ilk 10'da 12 sporcu
- Son 3 yılda gençler kategorisinde 25 uluslararası madalya
- Yaş ortalaması 16.5 olan milli takım kadrosu
- %85 başarı oranı ile Avrupa'nın en istikrarlı judo programı

**Başarı Hikayeleri:**

**Zeynep Nur Akyol (17 yaş, -52kg):**
Ankara doğumlu genç sporcu, 14 yaşında judoya başladı. 3 yıl içinde:
- Avrupa Gençler Şampiyonu (2023)
- Dünya Gençler Şampiyonası gümüş madalyası
- 45 maçta 42 galibiyet
- Teknik özellik: Ne-waza (yer teknikleri) uzmanlığı

**Ahmet Can Demirtaş (18 yaş, -73kg):**
İzmir'den çıkan yetenekli judocu:
- Dünya Gençler Şampiyonu (2024)
- Olimpiyat hazırlık kampına davet
- Japon stili judo felsefesi
- Güçlü yön: Tachi-waza (ayakta teknikler)

**Sistem Analizi: Başarının Formülü**

**1. Erken Keşif Programı:**
Türkiye Judo Federasyonu'nun 2019'da başlattığı "Altın Nesil Projesi":
- İlkokul seviyesinde yetenek taraması
- Bölgesel gelişim merkezleri
- Aile desteği programları
- Psikolojik gelişim takibi

**2. Bilimsel Antrenman Metodolojisi:**
- Yaş grubuna özel antrenman planları
- Beslenme uzmanı takibi
- Fizyoterapi ve sakatlık önleme
- Mental koç desteği

**3. Uluslararası Deneyim Programı:**
- Japоnya'da 6 aylık staj programı
- Avrupa kulüplerinde sezon deneyimi
- Düzenli uluslararası turnuva katılımı
- Değişim öğrencisi programları

**Teknik Gelişim Analizi:**

**Geleneksel Türk Judo Stili:**
Yeni nesil judocular, geleneksel güçlü fiziksel yapıyı modern tekniklerle harmanlıyor:
- Güçlü kavrama teknikleri
- Hızlı ayak çalışması
- Etkili savunma sistemleri
- Çok yönlü atak çeşitliliği

**Japon Etkisi:**
2021'den itibaren Japon antrenörlerle çalışma:
- Kata mükemmelliği odağı
- Zihinsel disiplin geliştirme
- Detay odaklı teknik gelişim
- Saygı ve öz-kontrol değerleri

**Altyapı Sistemi Devrimi:**

**Bölgesel Mükemmellik Merkezleri:**
7 farklı şehirde kurulan özel merkezler:
- İstanbul Teknik Mükemmellik Merkezi
- Ankara Kondisyon Gelişim Merkezi
- İzmir Taktik Analiz Merkezi
- Bursa Zihinsel Gelişim Merkezi

**Okul Sporları Entegrasyonu:**
- 500 okulda judo programı
- Öğretmen antrenör eğitimi
- Okul takımları ligi sistemi
- Başarılı sporculara eğitim bursu

**Gelecek Projeksiyonları:**

**2028 Los Angeles Olimpiyatları Hedefleri:**
- 4-5 sporcu ile katılım
- En az 2 madalya beklentisi
- Takım halinde madalya şansı
- Dünya sıralamasında ilk 5 ülke statüsü

**2030 Vizyon Planı:**
- Dünya şampiyonalarında 5 madalya
- Her yaş kategorisinde Avrupa zirvesi
- 100.000 lisanslı sporcu sayısı
- 15 uluslararası seviye antrenör

**Zorluklar ve Çözüm Önerileri:**

**Ana Zorluklar:**
- Sporcu emekliliği ve süreklilik
- Uluslararası rekabet baskısı
- Finansal sürdürülebilirlik
- Antrenör kapasitesi sınırı

**Çözüm Stratejileri:**
- Mezun sporcu antrenör programı
- Özel sektör sponsorluk artışı
- Akademik çalışma teşvikleri
- Teknoloji destekli antrenman

**Başarı Faktörleri:**

**1. Sistematik Yaklaşım:**
Rastgele değil, planlaşmış gelişim programları

**2. Çok Disiplinli Destek:**
Sadece antrenman değil, bütüncül sporcu gelişimi

**3. Uluslararası Görüş:**
Dünya standartlarında eğitim ve deneyim

**4. Aile ve Toplum Desteği:**
Sporcu motivasyonunu artıran sosyal çevre

**Sonuç:**

Türk judosunda yaşanan genç yetenek patlaması, tesadüfi bir gelişme değil, 10 yıllık sistematik çalışmanın meyvesi. Bu başarı, sadece şimdiki dönem için değil, gelecek 15-20 yılın Türk judo sporunu zirvede tutacak potansiyeli taşıyor.

Mevcut genç neslin kalitesi ve sistem işleyişi, Türkiye'yi dünya judo haritasında kalıcı bir güç haline getirme yolunda önemli adımlar atmış durumda. Önümüzdeki dönemde bu ivmenin korunması ve geliştirilmesi, Türk sporunun genel başarısına da önemli katkılar sağlayacak.

*Bu analiz, federasyon verilerinin yanı sıra antrenörler, sporcular ve spor bilimcileriyle yapılan detaylı mülakatlar sonucunda hazırlanmıştır.*''',
                'kose_yazisi': True
            }
        ]

        eklenen_haberler = 0

        for haber_data in ozel_haberler:
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
                        anasayfa_haberi=False,
                        kose_yazisi=haber_data['kose_yazisi'],
                        olusturma_tarihi=timezone.now()
                    )
                    eklenen_haberler += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Özel dosya eklendi: {haber_data["baslik"][:50]}...')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Zaten mevcut: {haber_data["baslik"][:50]}...')
                    )
                    
            except Kategori.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Kategori bulunamadı: {haber_data["kategori"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Hata: {haber_data["baslik"][:30]}... - {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 İşlem tamamlandı! {eklenen_haberler} özel dosya haberi eklendi.')
        )