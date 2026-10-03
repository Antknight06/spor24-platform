from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from haberler.models import BekleyenHaber

class Command(BaseCommand):
    help = '12 saatten eski bekleyen haberleri temizler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🗑️  12 SAATTEN ESKİ BEKLEYEN HABERLERİ TEMİZLE\n')
        )
        self.stdout.write('=' * 50)
        
        # Calculate the time 12 hours ago
        twelve_hours_ago = timezone.now() - timedelta(hours=12)
        
        # Get pending news items older than 12 hours based on haber_tarihi
        old_pending_news = BekleyenHaber.objects.filter(
            onaylandi=False,
            reddedildi=False,
            haber_tarihi__lt=twelve_hours_ago
        )
        
        if not old_pending_news.exists():
            self.stdout.write(
                self.style.WARNING('12 saatten eski bekleyen haber bulunamadı.')
            )
            return
        
        count = old_pending_news.count()
        self.stdout.write(f'Silinecek eski haber sayısı: {count}')
        
        # Confirm deletion
        confirm = input('Eski haberleri silmek istediğinizden emin misiniz? (e/h): ')
        if confirm.lower() != 'e':
            self.stdout.write(
                self.style.WARNING('İşlem iptal edildi.')
            )
            return
        
        # Delete old pending news
        deleted_count = old_pending_news.delete()[0]
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Temizlik tamamlandı! {deleted_count} eski bekleyen haber silindi.')
        )