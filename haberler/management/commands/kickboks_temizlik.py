from django.core.management.base import BaseCommand
from haberler.models import Haber

class Command(BaseCommand):
    help = 'Kickboks kategorisindeki gereksiz haberleri temizler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece göster, silme',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🧹 KICKBOKS HABERLERİ TEMİZLİĞİ\n')
        )
        self.stdout.write('=' * 50)
        
        # Kickboks kategorisindeki haberleri al
        kickboks_haberler = Haber.objects.filter(kategori__slug='kickboks')
        
        self.stdout.write(f"📊 Toplam {kickboks_haberler.count()} kickboks haberi bulundu")
        
        # Gereksiz haber başlıkları (menü öğeleri, sayfalar vs.)
        gereksiz_basliklar = [
            'ANASAYFA',
            'KURUMSAL', 
            'FEDERASYON BAŞKANI',
            'FEDERASYON PERSONELİ',
            'İL TEMSİLCİLERİ VEBÖLGE BAŞKANLARI',
            'TARİHÇE',
            'HAKKIMIZDA',
            'VİZYONUMUZ',
            'MİSYONUMUZ',
            'İLETİŞİM',
            'HABERLER',
            'DUYURULAR',
            'GALERİ',
            'LİNKLER',
            'BAĞLANTILAR'
        ]
        
        # URL'ye göre gereksiz olanları bul
        gereksiz_url_parcalari = [
            'sayfa/',
            'page/',
            'javascript:',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            '#',
            'mailto:'
        ]
        
        silinecek_haberler = []
        
        for haber in kickboks_haberler:
            # Başlık kontrolü
            if haber.baslik.upper().strip() in gereksiz_basliklar:
                silinecek_haberler.append({
                    'haber': haber,
                    'sebep': f'Gereksiz başlık: {haber.baslik}'
                })
                continue
            
            # URL kontrolü
            if haber.kaynak_url:
                for url_parca in gereksiz_url_parcalari:
                    if url_parca in haber.kaynak_url:
                        silinecek_haberler.append({
                            'haber': haber,
                            'sebep': f'Gereksiz URL: {url_parca}'
                        })
                        break
            
            # Çok kısa başlık kontrolü
            if len(haber.baslik.strip()) < 5:
                silinecek_haberler.append({
                    'haber': haber,
                    'sebep': 'Çok kısa başlık'
                })
                continue
            
            # Çok kısa içerik kontrolü
            if len(haber.icerik.strip()) < 50:
                silinecek_haberler.append({
                    'haber': haber,
                    'sebep': 'Çok kısa içerik'
                })
                continue
        
        self.stdout.write(f"\n🗑️ {len(silinecek_haberler)} gereksiz haber bulundu:")
        
        for item in silinecek_haberler:
            haber = item['haber']
            sebep = item['sebep']
            
            self.stdout.write(f"\n❌ {haber.baslik[:50]}...")
            self.stdout.write(f"   Sebep: {sebep}")
            self.stdout.write(f"   URL: {haber.kaynak_url}")
            self.stdout.write(f"   Tarih: {haber.olusturma_tarihi.strftime('%d.%m.%Y')}")
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f"\n🔍 DRY RUN: {len(silinecek_haberler)} haber silinecekti")
            )
        else:
            # Gerçekten sil
            silinen_sayisi = 0
            for item in silinecek_haberler:
                try:
                    item['haber'].delete()
                    silinen_sayisi += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Silme hatası: {e}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f"\n🗑️ {silinen_sayisi} gereksiz haber silindi!")
            )
        
        # Kalan haberleri göster
        kalan_haberler = Haber.objects.filter(kategori__slug='kickboks')
        self.stdout.write(f"\n📰 Kalan haber sayısı: {kalan_haberler.count()}")
        
        if kalan_haberler.exists():
            self.stdout.write("\n✅ Kalan geçerli haberler:")
            for haber in kalan_haberler.order_by('-olusturma_tarihi')[:10]:
                self.stdout.write(f"   • {haber.baslik[:60]}...")
        
        # Öneriler
        self.stdout.write(
            self.style.SUCCESS(
                f"\n💡 Öneri: Gelecekte daha iyi filtreleme için CSS selector'ları optimize edilebilir"
            )
        )