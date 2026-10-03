from django.core.management.base import BaseCommand
from django.utils import timezone
from haberler.models import Kategori, Haber
from collections import defaultdict
from datetime import datetime

class Command(BaseCommand):
    help = 'Kategorilerdeki haberleri analiz eder ve raporlar'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n📊 KATEGORİ HABER ANALİZİ\n')
        )
        self.stdout.write('=' * 50)
        
        # Get all categories
        categories = Kategori.objects.all()
        
        if not categories.exists():
            self.stdout.write(
                self.style.WARNING('Hiç kategori bulunamadı.')
            )
            return
        
        # Analysis results
        future_dated_news = []
        high_frequency_categories = []
        category_distribution = defaultdict(lambda: defaultdict(int))
        
        # Process each category
        for category in categories:
            # Get all news for this category
            news_items = Haber.objects.filter(kategori=category)
            
            if not news_items.exists():
                continue
            
            # Group news by date
            news_by_date = defaultdict(list)
            for news in news_items:
                # Check for future dated news
                if news.olusturma_tarihi.date() > timezone.now().date():
                    future_dated_news.append({
                        'category': category.ad,
                        'news': news.baslik,
                        'date': news.olusturma_tarihi.date()
                    })
                
                # Group by date for frequency analysis
                news_by_date[news.olusturma_tarihi.date()].append(news)
                
                # Group by month/year for distribution analysis
                month_year = news.olusturma_tarihi.strftime('%Y-%m')
                category_distribution[category.ad][month_year] += 1
            
            # Check for days with 4 or more news items
            for date, news_list in news_by_date.items():
                if len(news_list) >= 4:
                    high_frequency_categories.append({
                        'category': category.ad,
                        'date': date,
                        'count': len(news_list),
                        'news_titles': [news.baslik for news in news_list[:3]]  # Show first 3 titles
                    })
        
        # Report future dated news
        self.stdout.write('\n📅 Gelecek Tarihli Haberler:')
        if future_dated_news:
            for item in future_dated_news:
                self.stdout.write(
                    f'   ⏰ {item["category"]} - {item["news"]} ({item["date"]})'
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('   ✅ Gelecek tarihli haber bulunamadı.')
            )
        
        # Report categories with high frequency news
        self.stdout.write('\n📈 Günlük 4 veya Daha Fazla Haber Olan Kategoriler:')
        if high_frequency_categories:
            for item in high_frequency_categories:
                self.stdout.write(
                    f'   📰 {item["category"]} - {item["date"]} tarihinde {item["count"]} haber'
                )
                for title in item["news_titles"]:
                    self.stdout.write(f'      • {title}')
        else:
            self.stdout.write(
                self.style.SUCCESS('   ✅ Günlük 4 veya daha fazla haber olan kategori bulunamadı.')
            )
        
        # Report distribution by month/year
        self.stdout.write('\n📆 Kategori Bazında Ay-Yıl Dağılımı:')
        for category_name, months in category_distribution.items():
            self.stdout.write(f'\n   📁 {category_name}:')
            sorted_months = sorted(months.items(), key=lambda x: x[0])
            for month, count in sorted_months:
                year = month[:4]
                month_num = month[5:]
                month_name = self.get_month_name(month_num)
                self.stdout.write(f'      {year} {month_name}: {count} haber')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Analiz tamamlandı! Toplam {categories.count()} kategori incelendi.')
        )
    
    def get_month_name(self, month_num):
        """Convert month number to Turkish month name"""
        months = {
            '01': 'Ocak',
            '02': 'Şubat',
            '03': 'Mart',
            '04': 'Nisan',
            '05': 'Mayıs',
            '06': 'Haziran',
            '07': 'Temmuz',
            '08': 'Ağustos',
            '09': 'Eylül',
            '10': 'Ekim',
            '11': 'Kasım',
            '12': 'Aralık'
        }
        return months.get(month_num, month_num)