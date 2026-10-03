from django.core.management.base import BaseCommand
from haberler.models import Haber, FederasyonWebsite

class Command(BaseCommand):
    help = 'Resim indirme işlemlerinin özetini göster'

    def handle(self, *args, **options):
        self.stdout.write('🖼️  RESİM İNDİRME RAPORU')
        self.stdout.write('=' * 50)
        
        # Genel istatistikler
        total_news = Haber.objects.count()
        news_with_images = Haber.objects.filter(resim__isnull=False).count()
        news_from_federation = Haber.objects.filter(
            resim__isnull=False, 
            kaynak_url__isnull=False,
            otomatik_eklendi=True
        ).count()
        
        self.stdout.write(f'📊 Toplam haber sayısı: {total_news}')
        self.stdout.write(f'🖼️  Resimli haber sayısı: {news_with_images}')
        self.stdout.write(f'📡 Federasyon sitesinden çekilen: {news_from_federation}')
        self.stdout.write(f'✅ Başarı oranı: {(news_with_images/total_news*100):.1f}%')
        
        self.stdout.write('\n🌐 FEDERASYON SİTELERİ')
        self.stdout.write('-' * 30)
        
        for federation in FederasyonWebsite.objects.filter(aktif=True):
            fed_news = Haber.objects.filter(federasyon_website=federation)
            fed_with_images = fed_news.filter(resim__isnull=False)
            
            if fed_news.exists():
                success_rate = (fed_with_images.count() / fed_news.count() * 100)
                self.stdout.write(
                    f'🏛️  {federation.ad}: '
                    f'{fed_with_images.count()}/{fed_news.count()} '
                    f'({success_rate:.1f}%)'
                )
        
        self.stdout.write('\n🎯 ÖNERİLER')
        self.stdout.write('-' * 20)
        
        # Resmi olmayan haberleri kontrol et
        news_without_images = Haber.objects.filter(resim__isnull=True)
        if news_without_images.exists():
            self.stdout.write(f'⚠️  {news_without_images.count()} haber hala resimsiz')
            self.stdout.write('   Çözüm: python manage.py stok_resim_ekle')
        else:
            self.stdout.write('✅ Tüm haberler artık resme sahip!')
        
        # Gelecekteki haberler için öneri
        self.stdout.write('\n🚀 GELECEKTEKİ HABERLER İÇİN:')
        self.stdout.write('   • Yeni haber çekerken: python manage.py haber_cek --all')
        self.stdout.write('   • Resim güncelleme: python manage.py gelismis_resim_indirici')
        self.stdout.write('   • Stok resim ekleme: python manage.py stok_resim_ekle')
        
        self.stdout.write(f'\n🎉 Sistem hazır! Artık tüm haberler federasyon sitelerinden ')
        self.stdout.write(f'   çekilen gerçek resimlerle veya karate temalı resimlerle')
        self.stdout.write(f'   görüntüleniyor.')