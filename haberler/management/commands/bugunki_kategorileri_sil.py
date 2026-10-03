from django.core.management.base import BaseCommand
from django.utils import timezone
from haberler.models import Kategori

class Command(BaseCommand):
    help = 'Bugün tarihli eklenen tüm kategorileri siler'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🗑️ BUGÜNKİ KATEGORİLER SİLİNİYOR\n')
        )
        self.stdout.write('=' * 50)
        
        # Get today's date
        today = timezone.now().date()
        
        # Find categories added today
        categories = Kategori.objects.filter(olusturma_tarihi__date=today)
        
        self.stdout.write(f'Bugünün tarihi: {today}')
        self.stdout.write(f'Silinecek kategori sayısı: {categories.count()}')
        
        if categories.count() == 0:
            self.stdout.write(
                self.style.WARNING('Silenecek kategori bulunamadı.')
            )
            return
        
        # List categories to be deleted
        self.stdout.write('\nSilinecek kategoriler:')
        for category in categories:
            self.stdout.write(f'   🗑️ {category.ad}')
        
        # Ask for confirmation
        confirm = input('\nBu kategorileri silmek istediğinize emin misiniz? (evet/hayır): ')
        
        if confirm.lower() not in ['evet', 'e', 'yes', 'y']:
            self.stdout.write(
                self.style.WARNING('İşlem iptal edildi.')
            )
            return
        
        # Delete categories
        deleted_count = 0
        for category in categories:
            try:
                category.delete()
                deleted_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {category.ad} silinirken hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ İşlem tamamlandı! {deleted_count} kategori silindi.'
            )
        )