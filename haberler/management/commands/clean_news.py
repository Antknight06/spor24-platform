from django.core.management.base import BaseCommand
from haberler.models import BekleyenYetkiliHaberi
from django.db.models import Count

class Command(BaseCommand):
    help = 'Bekleyen haberlerdeki mükerrer kayıtları temizler.'

    def handle(self, *args, **options):
        self.stdout.write("🧹 Mükerrer haber temizliği başlıyor...")
        
        # 1. Başlığa göre grupla
        duplicates = BekleyenYetkiliHaberi.objects.values('baslik').annotate(count=Count('id')).filter(count__gt=1)
        
        total_deleted = 0
        
        for item in duplicates:
            baslik = item['baslik']
            # Aynı başlıklı haberleri al, ID'ye göre tersten sırala (en yeni en üstte)
            haberler = BekleyenYetkiliHaberi.objects.filter(baslik=baslik).order_by('-id')
            
            # İlkini (en yenisini) tut, diğerlerini sil
            to_keep = haberler.first()
            to_delete = haberler.exclude(id=to_keep.id)
            
            count = to_delete.count()
            to_delete.delete()
            
            self.stdout.write(f"   🗑️  Silindi ({count} adet): {baslik[:50]}...")
            total_deleted += count
            
        self.stdout.write(self.style.SUCCESS(f"\n✅ Temizlik tamamlandı. Toplam {total_deleted} mükerrer haber silindi."))
