from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite, Kategori
from haberler.services.news_scraper import NewsImportService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test news scraping with a real website (BBC Sport Turkish)'

    def handle(self, *args, **options):
        self.stdout.write('🧪 Haber çekme işlevselliğini test ediyoruz...')
        
        # Create or get a test federation website with BBC Sport Turkish
        test_federation, created = FederasyonWebsite.objects.get_or_create(
            ad='BBC Sport Türkçe (Test)',
            defaults={
                'ana_url': 'https://www.bbc.com',
                'haberler_url': 'https://www.bbc.com/turkce/spor',
                'haber_listesi_selector': '.bbc-uk8dsi',  # BBC article selector
                'haber_baslik_selector': 'h3',
                'haber_link_selector': 'a',
                'haber_tarih_selector': 'time',
                'haber_ozet_selector': 'p',
                'aktif': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Test federasyonu oluşturuldu'))
        else:
            self.stdout.write(self.style.WARNING('! Test federasyonu zaten mevcut'))
        
        # Create test category
        test_kategori, created = Kategori.objects.get_or_create(
            slug='test-sporlar',
            defaults={
                'ad': 'Test Sporları',
                'aciklama': 'Test amaçlı spor haberleri',
                'federasyon_website': test_federation
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Test kategorisi oluşturuldu'))
        
        # Test scraping
        try:
            news_import_service = NewsImportService()
            
            self.stdout.write('🔄 Haber çekme testi başlıyor...')
            imported_count = news_import_service.import_federation_news(
                test_federation, 
                test_kategori
            )
            
            if imported_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Test başarılı! {imported_count} haber çekildi.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  Haber çekilemedi. CSS selector\'lar kontrol edilmeli.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Test hatası: {str(e)}')
            )
        
        self.stdout.write('\n📊 Test sonucu:')
        
        # Show test results
        from haberler.models import Haber
        test_news = Haber.objects.filter(
            federasyon_website=test_federation,
            otomatik_eklendi=True
        )
        
        self.stdout.write(f'   • Toplam çekilen test haberleri: {test_news.count()}')
        
        if test_news.exists():
            self.stdout.write('   • Son çekilen haberler:')
            for news in test_news[:3]:
                self.stdout.write(f'     - {news.baslik[:60]}...')
                self.stdout.write(f'       Kaynak: {news.kaynak_url}')
        
        self.stdout.write('\n✨ Test tamamlandı!')
        self.stdout.write('\n💡 İpucu: Gerçek federasyon siteleri için CSS selector\'ları manuel olarak ayarlayın.')
        self.stdout.write('    Admin panelinden Federasyon Websiteleri bölümünden düzenleyebilirsiniz.')