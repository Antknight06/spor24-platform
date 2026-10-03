from django.core.management.base import BaseCommand
from django.utils import timezone
from haberler.models import FederasyonWebsite
from haberler.services.news_scraper import NewsImportService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sadece son 12 saat içindeki haberleri çekmek için yapılandırma
# Bu değer, NewsScrapingService içinde kullanılıyor

class Command(BaseCommand):
    help = 'Federasyon sitelerinden haberleri otomatik olarak çeker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--federation',
            type=str,
            help='Specific federation website ID to scrape',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Scrape news from all active federation websites',
        )

    def handle(self, *args, **options):
        news_import_service = NewsImportService()
        
        total_imported = 0
        
        if options['federation']:
            # Scrape specific federation
            try:
                federation = FederasyonWebsite.objects.get(id=options['federation'])
                if not federation.aktif:
                    self.stdout.write(
                        self.style.WARNING(f'{federation.ad} websitesi aktif değil')
                    )
                    return
                
                self.stdout.write(f'📰 {federation.ad} sitesinden haberler çekiliyor...')
                imported = news_import_service.import_federation_news(federation)
                total_imported += imported
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {federation.ad}: {imported} haber eklendi')
                )
                
            except FederasyonWebsite.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Federation website bulunamadı: {options["federation"]}')
                )
                return
                
        elif options['all']:
            # Scrape all active federations
            federations = FederasyonWebsite.objects.filter(aktif=True)
            
            if not federations.exists():
                self.stdout.write(
                    self.style.WARNING('Aktif federasyon websitesi bulunamadı')
                )
                return
            
            self.stdout.write(f'📰 {federations.count()} federasyon sitesinden haberler çekiliyor...')
            
            for federation in federations:
                try:
                    self.stdout.write(f'🔄 {federation.ad} işleniyor...')
                    imported = news_import_service.import_federation_news(federation)
                    total_imported += imported
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {federation.ad}: {imported} haber eklendi')
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ {federation.ad} hatası: {str(e)}')
                    )
                    continue
        else:
            self.stdout.write(
                self.style.ERROR('Lütfen --federation <ID> veya --all parametresini kullanın')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! Toplam {total_imported} haber eklendi.'
            )
        )
        
        # Boks haberlerinin tarihlerini düzelt
        if total_imported > 0:
            self.fix_boks_dates()
        
        # Show statistics
        self.show_statistics()
    
    def show_statistics(self):
        """Show import statistics"""
        from haberler.models import Haber
        
        # Show recent automatic imports
        recent_auto_news = Haber.objects.filter(
            otomatik_eklendi=True,
            olusturma_tarihi__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        total_auto_news = Haber.objects.filter(otomatik_eklendi=True).count()
        
        self.stdout.write('\n📊 İstatistikler:')
        self.stdout.write(f'   • Bugün eklenen otomatik haberler: {recent_auto_news}')
        self.stdout.write(f'   • Toplam otomatik haberler: {total_auto_news}')
    
    def fix_boks_dates(self):
        """Boks haberlerinin tarihlerini düzeltir"""
        from django.core.management import call_command
        
        self.stdout.write('\n🥊 Boks haberleri tarih düzeltme işlemi başlatılıyor...')
        
        try:
            # Önce basit tarih düzeltme
            call_command('boks_tarih_duzelt', '--recent', '--limit=20', verbosity=0)
            
            # Sonra gelişmiş tarih çıkarma (sadece eşleşmeyenler için)
            import subprocess
            import sys
            result = subprocess.run([
                sys.executable, 'boks_gelismis_api_tarih.py'
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('✓ Boks tarih düzeltme tamamlandı'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Boks tarih düzeltme kısmen tamamlandı'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Boks tarih düzeltme hatası: {e}'))