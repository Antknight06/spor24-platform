from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from haberler.models import Haber

class Command(BaseCommand):
    help = 'Son 1 saat içinde eklenen tüm haberleri siler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Onay olmadan silme işlemini zorla',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🗑️ SON 1 SAAT İÇİNDE EKLENEN HABERLER SİLİNİYOR\n')
        )
        self.stdout.write('=' * 50)
        
        # Calculate the time 1 hour ago
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Find news articles added in the last hour
        recent_news = Haber.objects.filter(olusturma_tarihi__gte=one_hour_ago)
        
        self.stdout.write(f'Bir saat önce: {one_hour_ago.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'Silinecek haber sayısı: {recent_news.count()}')
        
        if recent_news.count() == 0:
            self.stdout.write(
                self.style.WARNING('Son 1 saat içinde eklenen haber bulunamadı.')
            )
            return
        
        # List news articles to be deleted
        self.stdout.write('\nSilinecek haberler:')
        for news in recent_news:
            self.stdout.write(f'   🗑️ {news.baslik} (Eklenme: {news.olusturma_tarihi.strftime("%Y-%m-%d %H:%M:%S")})')
        
        # Ask for confirmation unless force flag is used
        if not options['force']:
            confirm = input('\nBu haberleri silmek istediğinize emin misiniz? (evet/hayır): ')
            
            if confirm.lower() not in ['evet', 'e', 'yes', 'y']:
                self.stdout.write(
                    self.style.WARNING('İşlem iptal edildi.')
                )
                return
        
        # Delete news articles
        deleted_count = 0
        for news in recent_news:
            try:
                # Delete the news image if it exists
                if news.resim:
                    news.resim.delete(save=False)
                # Delete the news article
                news.delete()
                deleted_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ "{news.baslik}" silinirken hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ İşlem tamamlandı! {deleted_count} haber silindi.'
            )
        )