from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from haberler.models import BekleyenHaber

class Command(BaseCommand):
    help = 'Deletes unapproved and unrejected pending news (BekleyenHaber) older than 30 days (non-interactive)'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🗑️  30 GÜNDEN ESKİ BEKLEYEN HABERLERİ TEMİZLE\n')
        )
        self.stdout.write('=' * 50)
        
        limit_date = timezone.now() - timedelta(days=30)
        
        # Filter pending news older than 30 days (not approved, not rejected)
        old_pending_news = BekleyenHaber.objects.filter(
            onaylandi=False,
            reddedildi=False,
            olusturma_tarihi__lt=limit_date
        )
        
        count = old_pending_news.count()
        
        if count == 0:
            self.stdout.write(
                self.style.WARNING('30 günden eski bekleyen haber bulunamadı.')
            )
            return
            
        self.stdout.write(f'Silinecek eski haber sayısı: {count}')
        
        # Delete old pending news
        deleted_count = old_pending_news.delete()[0]
        
        self.stdout.write('=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Temizlik tamamlandı! {deleted_count} eski bekleyen haber silindi.')
        )
