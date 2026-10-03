from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from haberler.models import BekleyenHaber

class Command(BaseCommand):
    help = 'Yeni haber sembolü kontrolü (sadece bekleyen haberler için)'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🔍 YENİ HABER SEMBOLÜ KONTROLÜ (Sadece Bekleyen Haberler)\n')
        )
        self.stdout.write('=' * 50)
        
        # Count pending news
        pending_news = BekleyenHaber.objects.filter(
            onaylandi=False, 
            reddedildi=False
        ).count()
        
        self.stdout.write(f'Bekleyen haberler: {pending_news}')
        
        if pending_news > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Yeni haber sembolü aktif! {pending_news} bekleyen haber bulunuyor.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n⚠️  Yeni haber sembolü pasif - bekleyen haber bulunamadı.')
            )
        
        # Show details of pending news
        if pending_news > 0:
            self.stdout.write('\n⏳ Bekleyen haberler:')
            pending_news_items = BekleyenHaber.objects.filter(
                onaylandi=False, 
                reddedildi=False
            ).order_by('-olusturma_tarihi')
            
            for news in pending_news_items[:10]:  # Show first 10
                self.stdout.write(
                    f'   ⏳ {news.baslik} ({news.olusturma_tarihi.strftime("%Y-%m-%d %H:%M")})'
                )
            
            if pending_news_items.count() > 10:
                self.stdout.write(
                    f'   ... ve {pending_news_items.count() - 10} haber daha'
                )