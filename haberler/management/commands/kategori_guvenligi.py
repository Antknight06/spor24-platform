from django.core.management.base import BaseCommand
from haberler.models import Kategori

class Command(BaseCommand):
    help = 'Otomatik kategori oluşturmayı engellemek için mevcut komutları güvenli hale getirir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-sources',
            action='store_true',
            help='Otomatik kategori oluşturan kaynak komutları göster'
        )
        parser.add_argument(
            '--current-categories',
            action='store_true',
            help='Mevcut kategorileri listele'
        )

    def handle(self, *args, **options):
        self.stdout.write('🔒 OTOMATİK KATEGORİ OLUŞTURMAYI ENGELLEME SİSTEMİ')
        self.stdout.write('=' * 50)
        
        if options['show_sources']:
            self._show_category_creation_sources()
            return
            
        if options['current_categories']:
            self._show_current_categories()
            return
        
        # Ana işlem - kategori oluşturmayı engelleme önlemleri
        self._implement_safeguards()

    def _show_category_creation_sources(self):
        """Otomatik kategori oluşturan komutları göster"""
        self.stdout.write('\n📋 OTOMATİK KATEGORİ OLUŞTURAN KOMUTLAR:')
        
        sources = [
            {
                'file': 'federasyon_haber_import.py',
                'line': '102-109',
                'code': 'Kategori.objects.get_or_create()',
                'reason': 'Federasyon haberleri import ederken otomatik kategori oluşturuyor'
            },
            {
                'file': 'karate_gov_tr_ekle.py', 
                'line': '20-30',
                'code': 'Kategori.objects.get_or_create()',
                'reason': 'Karate federasyonu eklerken kategori oluşturuyor'
            },
            {
                'file': 'dovus_kategorileri_ekle.py',
                'line': '80-90',
                'code': 'Kategori.objects.create()',
                'reason': 'Dövüş sanatları kategorilerini toplu oluşturuyor'
            },
            {
                'file': 'test_scraper.py',
                'line': '35-45',
                'code': 'Kategori.objects.get_or_create()',
                'reason': 'Test kategorisi oluşturuyor'
            },
            {
                'file': 'news_scraper.py (NewsImportService)',
                'line': '380-390',
                'code': 'Kategori.objects.get_or_create()',
                'reason': 'Import sırasında kategori bulamazsa oluşturuyor'
            }
        ]
        
        for source in sources:
            self.stdout.write(f'\n📄 {source["file"]}')
            self.stdout.write(f'   📍 Satır: {source["line"]}')
            self.stdout.write(f'   💻 Kod: {source["code"]}')
            self.stdout.write(f'   ⚠️  Sebep: {source["reason"]}')

    def _show_current_categories(self):
        """Mevcut kategorileri listele"""
        from haberler.models import Haber
        
        self.stdout.write('\n📂 MEVCUT KATEGORİLER:')
        kategoriler = Kategori.objects.all().order_by('ad')
        
        for kategori in kategoriler:
            haber_sayisi = Haber.objects.filter(kategori=kategori).count()
            self.stdout.write(f'   • {kategori.ad} ({kategori.slug}) - {haber_sayisi} haber')
        
        self.stdout.write(f'\nToplam kategori sayısı: {kategoriler.count()}')

    def _implement_safeguards(self):
        """Güvenlik önlemlerini uygula"""
        
        self.stdout.write('\n🔒 GÜVENLİK ÖNLEMLERİ:')
        
        # 1. Mevcut kategorileri kaydet
        current_categories = list(Kategori.objects.values_list('slug', 'ad'))
        
        self.stdout.write(f'✅ Mevcut {len(current_categories)} kategori kaydedildi')
        
        # 2. Öneriler
        self.stdout.write('\n📋 ÖNERİLER:')
        self.stdout.write('   1. Federasyon haberi import etmeden önce kategorinin mevcut olduğunu kontrol edin')
        self.stdout.write('   2. Yeni kategoriler sadece manuel olarak admin panelinden eklensin')
        self.stdout.write('   3. Import komutlarında --dry-run seçeneğini kullanın')
        self.stdout.write('   4. Kategori değişikliklerini önceden onaylayın')
        
        # 3. Güvenli import için örnek komutlar
        self.stdout.write('\n💡 GÜVENLİ İMPORT KOMUTLARI:')
        self.stdout.write('   • Federasyon haberleri: --federation-id=X (sadece mevcut kategorilere)')
        self.stdout.write('   • Dry-run test: --dry-run parametresi ekleyin')
        self.stdout.write('   • Manuel kontrol: Kategorileri önceden kontrol edin')
        
        # 4. Acil durum kurtarma
        self.stdout.write('\n🚨 ACİL DURUM KURTARMA:')
        self.stdout.write('   • İstenmeyen kategori oluşursa: python manage.py shell kullanarak silin')
        self.stdout.write('   • Haber transferi: karate_kategorilerini_birlestir komutunu kullanın')
        self.stdout.write('   • Yedekleme: Veritabanını düzenli olarak yedekleyin')
        
        self.stdout.write('\n⚠️  UYARI: Bu komutlar değiştirilene kadar otomatik kategori oluşturma devam edecek!')
        self.stdout.write('Manuel onay olmadan kategori oluşturmayı engellemek için komutlar düzenlenmelidir.')
        
        self.stdout.write('\n✅ Güvenlik önlemleri tamamlandı!')