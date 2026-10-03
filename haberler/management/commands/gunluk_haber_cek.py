from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

class Command(BaseCommand):
    help = 'Her gün sabah 12 ve akşam 12\'de haber çekmek için zamanlanmış komut'

    def handle(self, *args, **options):
        # Zaman damgası
        now = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(f'\n=== GÜNLÜK HABER ÇEKME İŞLEMİ ===')
        )
        self.stdout.write(
            f'Başlangıç Zamanı: {now.strftime("%d.%m.%Y %H:%M:%S")}'
        )
        
        try:
            # Tüm aktif federasyonlardan haber çek
            self.stdout.write('\n🔄 Tüm federasyonlardan haberler çekiliyor...')
            call_command('federasyon_haber_import', verbosity=1)
            
            # Yeni haberleri bildir
            self.stdout.write('\n📢 Yeni haberler kontrol ediliyor...')
            call_command('yeni_haber_bildir', verbosity=1)
            
            # Bitiş zamanı
            end_time = timezone.now()
            duration = end_time - now
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Günlük haber çekme işlemi tamamlandı!')
            )
            self.stdout.write(
                f'Bitiş Zamanı: {end_time.strftime("%d.%m.%Y %H:%M:%S")}'
            )
            self.stdout.write(
                f'Toplam Süre: {duration.total_seconds():.2f} saniye'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Hata oluştu: {e}')
            )
            raise