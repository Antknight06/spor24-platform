from django.core.management.base import BaseCommand
from haberler.models import Haber, Kategori
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Çekilen haberlerin içeriklerini genişletir ve arka plan bilgileri ekler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Genişletilecek haber sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--kategori',
            type=str,
            help='Sadece belirtilen kategorideki haberleri genişlet'
        )

    def handle(self, *args, **options):
        limit = options.get('limit', 10)
        kategori_filter = options.get('kategori')
        
        # Kısa içerikli otomatik eklenen haberleri bul
        queryset = Haber.objects.filter(
            otomatik_eklendi=True,
            yayinlandi=True
        ).exclude(
            icerik__isnull=True
        ).exclude(
            icerik=''
        )
        
        # Kategori filtresi varsa uygula
        if kategori_filter:
            try:
                kategori = Kategori.objects.get(ad__icontains=kategori_filter)
                queryset = queryset.filter(kategori=kategori)
                self.stdout.write(f'📂 Sadece {kategori.ad} kategorisi işlenecek')
            except Kategori.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ "{kategori_filter}" kategorisi bulunamadı')
                )
                return
        
        # Kısa içerikli haberleri filtrele (Python seviyesinde)
        all_news = list(queryset[:50])  # İlk 50 haberi al
        short_content_news = [haber for haber in all_news if len(haber.icerik) < 500][:limit]
        
        if not short_content_news:
            self.stdout.write(
                self.style.WARNING('⚠️  Genişletilecek kısa içerikli haber bulunamadı')
            )
            return
        
        self.stdout.write(f'🔍 {len(short_content_news)} haber genişletilecek...\n')
        
        expanded_count = 0
        
        for haber in short_content_news:
            try:
                expanded_content = self._expand_news_content(haber)
                
                # İçeriği güncelle
                haber.icerik = expanded_content
                haber.guncelleme_tarihi = timezone.now()
                haber.save()
                
                expanded_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Genişletildi: {haber.baslik[:50]}...')
                )
                self.stdout.write(f'   📊 Yeni içerik uzunluğu: {len(expanded_content)} karakter\n')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Hata: {haber.baslik[:30]}... - {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 İşlem tamamlandı! {expanded_count} haber genişletildi.')
        )

    def _expand_news_content(self, haber):
        """Haber içeriğini genişletir ve arka plan bilgileri ekler"""
        
        # Kategori bazlı şablonlar
        content_templates = self._get_content_templates()
        kategori_ad = haber.kategori.ad.lower()
        
        # Uygun şablonu seç
        template = content_templates.get(kategori_ad, content_templates['genel'])
        
        # Mevcut içerik
        original_content = haber.icerik
        original_summary = haber.ozet
        
        # Genişletilmiş içerik oluştur
        expanded_content = self._build_expanded_content(
            haber, original_content, original_summary, template
        )
        
        return expanded_content
    
    def _build_expanded_content(self, haber, original_content, summary, template):
        """Detaylı içerik oluşturur"""
        
        # İçerik bölümleri
        sections = []
        
        # Giriş paragrafı
        intro = f"{summary}\n\n"
        if len(original_content) > len(summary):
            intro += f"{original_content}\n\n"
        
        sections.append(intro)
        
        # Ana içerik bölümü
        main_content = template['main_content'].format(
            kategori=haber.kategori.ad,
            baslik=haber.baslik
        )
        sections.append(main_content)
        
        # Detaylar bölümü
        details = template['details'].format(
            kategori=haber.kategori.ad,
            federasyon=haber.federasyon_website.ad if haber.federasyon_website else 'İlgili Federasyon',
            tarih=haber.olusturma_tarihi.strftime('%d.%m.%Y')
        )
        sections.append(details)
        
        # Arka plan bilgisi
        background = template['background'].format(
            kategori=haber.kategori.ad,
            yil=haber.olusturma_tarihi.year
        )
        sections.append(background)
        
        # Sonuç/Gelecek beklentileri
        conclusion = template['conclusion'].format(
            kategori=haber.kategori.ad
        )
        sections.append(conclusion)
        
        return '\n\n'.join(sections)
    
    def _get_content_templates(self):
        """Kategori bazlı içerik şablonları"""
        return {
            'karate': {
                'main_content': """Bu gelişme, Türkiye {kategori} sporundaki genel durumu yansıtıyor. Federasyon yetkilileri, bu tür gelişmelerin sporun büyümesine katkı sağladığını belirtiyor.

Spor camiasında {baslik} konusu önemli yankılar uyandırırken, uzmanlar bu durumun spora olan ilgiyi artırabileceğini değerlendiriyor.""",

                'details': """**Etkinlik Detayları:**
• Tarih: {tarih}
• Organizatör: {federasyon}
• Kategori: {kategori}
• Katılım: Ulusal ve uluslararası sporcular
• Hakem Kurulu: Uluslararası standartlarda

**Teknik Bilgiler:**
Müsabakalar uluslararası karate kuralları çerçevesinde gerçekleştirildi. Kata ve kumite branşlarında yapılan yarışmalar, WKF (World Karate Federation) standartlarına uygun olarak düzenlendi.""",

                'background': """**{kategori} Sporu Hakkında:**
Karate, Japonya kökenli bir dövüş sanatı olup, Türkiye'de 1960'lı yıllardan itibaren yaygınlaşmaya başladı. Türkiye Karate Federasyonu, 1971 yılında kurulmuş ve o tarihten itibaren sporcularımızın uluslararası arenada başarılar kazanmasına öncülük etmiştir.

Son yıllarda karate sporu, hem katılımcı sayısı hem de başarı açısından önemli bir ivme kazandı. {yil} yılında federasyonun uyguladığı yeni gelişim programları ile genç yetenekler keşfedilmeye ve desteklenmeye devam ediyor.""",

                'conclusion': """**Gelecek Hedefleri:**
Bu başarının ardından {kategori} branşında yeni hedefler belirlendi. Federasyon yetkilileri, önümüzdeki dönemde daha fazla sporcunun uluslararası müsabakalara hazırlanması için antrenman kampları düzenlemeyi planlıyor.

Ayrıca, genç sporcuların gelişimi için alt yapı yatırımlarının artırılması ve teknik kadronun güçlendirilmesi de öncelikli konular arasında yer alıyor."""
            },
            
            'taekwondo': {
                'main_content': """Taekwondo sporundaki bu gelişme, Türkiye'nin bu branştaki artan başarısının bir yansıması olarak görülüyor. {kategori} alanında kaydedilen bu ilerleme, federasyonun uzun vadeli stratejilerinin başarıyla uygulandığının göstergesi.

Türkiye Taekwondo Federasyonu'nun verilerine göre, son dönemde yapılan teknik ve altyapı yatırımları meyvelerini vermeye başladı. {baslik} konusundaki gelişmeler, sporcu ve antrenörlerin sistemli çalışmalarının sonucu.""",

                'details': """**Müsabaka Bilgileri:**
• Organizasyon Tarihi: {tarih}
• Düzenleyen: {federasyon}
• Branş: {kategori}
• Yaş Kategorileri: Çocuklar, gençler, yetişkinler
• Teknik Standartlar: World Taekwondo (WT) kuralları

**Başarı Faktörleri:**
- Sistematik antrenman programları
- Modern teknik donanım kullanımı
- Deneyimli antrenör kadrosu
- Sporcu gelişim programları""",

                'background': """**Türkiye'de {kategori} Tarihi:**
Taekwondo, 1960'lı yılların sonunda Türkiye'ye gelmiş ve hızla yaygınlaşmıştır. Kore kökenli bu dövüş sanatı, özellikle gençler arasında büyük ilgi görmüş ve Türkiye Taekwondo Federasyonu'nun kurulmasıyla birlikte profesyonel bir kimlik kazanmıştır.

{yil} yılı itibariyle Türkiye, taekwondo sporunda dünya sıralamasında üst sıralarda yer almaktadır. Olimpiyat başarıları ve dünya şampiyonlukları ile dikkat çeken branş, gelecek nesillere umut vermeye devam ediyor.""",

                'conclusion': """**Önümüzdeki Dönem:**
Bu başarının arkasından {kategori} federasyonu, daha büyük hedeflere odaklandı. Önümüzdeki sezon için planlanan uluslararası müsabakalar ve antrenman kampları ile sporcuların performanslarının daha da artırılması hedefleniyor.

Genç sporcuların yetiştirilmesi için okul programları ve kulüp destekleri de artırılacak."""
            },
            
            'judo': {
                'main_content': """Judo sporundaki bu önemli gelişme, Türkiye'nin bu alandaki güçlü konumunu bir kez daha gözler önüne serdi. {kategori} branşında yaşanan bu başarı, federasyonun yıllardır sürdürdüğü kaliteli çalışmaların bir yansıması olarak değerlendiriliyor.

{baslik} haberi, judo camiasında büyük bir memnuniyet yaratırken, sporun gelecekteki hedefleri açısından da önemli bir dönüm noktası oluşturuyor.""",

                'details': """**Organizasyon Detayları:**
• Etkinlik Tarihi: {tarih}
• Koordinatör: {federasyon}
• Müsabaka Türü: {kategori}
• Katılımcı Profili: Lisanslı sporcular
• Hakem Sistemi: Uluslararası Judo Federasyonu (IJF) standartları

**Teknik Özellikler:**
Müsabakalar, judo sporuna özgü teknik kurallar çerçevesinde icra edildi. Tatami üzerinde gerçekleştirilen yarışmalarda, sporcular hem teknik hem de fiziksel yeteneklerini sergilediler.""",

                'background': """**Judo Sporuna Genel Bakış:**
Japonya'dan dünyaya yayılan judo, "yumuşak yol" anlamına gelir ve sadece fiziksel güç değil, zihinsel disiplin de gerektirir. Türkiye'de judo sporu, 1950'li yıllardan itibaren gelişmeye başlamış ve bugün güçlü bir sporcu potansiyeline sahiptir.

{yil} yılında judo branşında kaydedilen gelişmeler, hem yerli hem de uluslararası arenada Türkiye'nin konumunu güçlendirmiştir. Federasyonun uyguladığı modern antrenman metodları ve sporcu geliştirme programları, başarının temelini oluşturmaktadır.""",

                'conclusion': """**Strateji ve Hedefler:**
{kategori} alanındaki bu başarının devamı için federasyon, kapsamlı bir strateji belirliyor. Antrenör eğitimi, sporcu kampları ve uluslararası işbirliği projelerinin genişletilmesi planlanıyor.

Özellikle genç yeteneklerin keşfi ve geliştirilmesi için bölgesel tarama programları ve yaz okulları düzenlenecek."""
            },
            
            'genel': {
                'main_content': """Bu gelişme, Türk dövüş sporlarındaki kalite artışının önemli bir göstergesi olarak kabul ediliyor. {kategori} alanında kaydedilen bu ilerleme, federasyonların son dönemde yürüttüğü kapsamlı projelerin başarısını yansıtıyor.

{baslik} konusundaki bu önemli adım, hem sporcular hem de teknik kadro açısından motivasyon artışı sağlarken, sporun toplumsal tabanda daha geniş kitleler tarafından benimsenmesin de katkı sunuyor.""",

                'details': """**Etkinlik Hakkında:**
• Düzenleme Tarihi: {tarih}
• Organizatör Kurum: {federasyon}
• Spor Dalı: {kategori}
• Hedef Kitle: Sporcular ve sporseverler
• Standartlar: Ulusal ve uluslararası normlar

**Öne Çıkan Özellikler:**
Bu gelişme, branşın professionalleşme sürecindeki önemli adımlardan birini oluşturuyor. Sistematik yaklaşım ve bilimsel metodların uygulanması sonucu elde edilen başarı, gelecekteki projeler için de örnek teşkil ediyor.""",

                'background': """**Branş Gelişimi:**
{kategori} sporu, Türkiye'de son yıllarda artan bir ivme kazandı. Federasyonların modernizasyon çabaları, antrenman kalitesinin artırılması ve sporcu odaklı yaklaşımlar, branştaki genel performansın yükselmesinde etkili oldu.

{yil} yılında spora yapılan yatırımlar ve geliştirilen projeler, hem katılımcı sayısında hem de başarı seviyesinde önemli artışlar sağladı.""",

                'conclusion': """**Gelecek Perspektifi:**
Bu başarının sürekliliği için {kategori} federasyonu, yeni dönem stratejilerini belirlemeye başladı. Sporcu gelişimi, antrenör eğitimi ve altyapı güçlendirme çalışmaları öncelikli alanlar olarak tespit edildi.

Ayrıca, sporun toplumsal yaygınlaşması için okullarda ve yerel topluluklar da tanıtım faaliyetleri düzenlenerek katılımın artırılması hedefleniyor."""
            }
        }
