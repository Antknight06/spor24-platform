from django.core.management.base import BaseCommand
from django.utils import timezone
from haberler.models import Haber
import subprocess
import sys
import os

class Command(BaseCommand):
    help = 'Kempo federasyonu haberlerinin tarihlerini kapsamlı şekilde düzeltir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Tüm kempo haberlerini işle',
        )
        parser.add_argument(
            '--fix-duplicates',
            action='store_true',
            help='Aynı tarihteki haberleri de düzelt',
        )

    def handle(self, *args, **options):
        self.stdout.write('🥋 KAPSAMLI KEMPO TARİH DÜZELTİCİ')
        self.stdout.write('=' * 70)
        
        # Başlangıç durumu
        initial_stats = self.get_stats()
        self.show_stats("BAŞLANGIÇ DURUMU", initial_stats)
        
        # 1. Temel tarih düzeltme
        self.stdout.write('\n📋 1. TEMEL TARİH DÜZELTME')
        self.stdout.write('-' * 40)
        self.run_basic_date_fix()
        
        # 2. Aynı tarihteki haberleri düzelt
        if options['fix_duplicates']:
            self.stdout.write('\n🔄 2. AYNI TARİHTEKİ HABERLERİ DÜZELT')
            self.stdout.write('-' * 40)
            self.run_duplicate_date_fix()
        
        # Son durum
        final_stats = self.get_stats()
        self.show_stats("SON DURUM", final_stats)
        
        # Başarı raporu
        self.show_success_report(initial_stats, final_stats)

    def get_stats(self):
        """İstatistikleri alır"""
        kempo_haberler = Haber.objects.filter(kategori__slug='kempo')
        
        total_count = kempo_haberler.count()
        now = timezone.now()
        
        # Makul tarih aralığındaki haberler
        reasonable_dates = kempo_haberler.filter(
            olusturma_tarihi__year__gte=2020,
            olusturma_tarihi__year__lte=2025,
            olusturma_tarihi__lte=now
        ).count()
        
        # Aynı gün çok fazla haber
        from collections import Counter
        dates = [h.olusturma_tarihi.strftime('%Y-%m-%d') for h in kempo_haberler]
        date_counts = Counter(dates)
        suspicious_dates = len([d for d, c in date_counts.items() if c > 2])
        
        return {
            'total': total_count,
            'reasonable': reasonable_dates,
            'suspicious_dates': suspicious_dates,
            'success_rate': (reasonable_dates / total_count * 100) if total_count > 0 else 0
        }

    def show_stats(self, title, stats):
        """İstatistikleri gösterir"""
        self.stdout.write(f'\n📊 {title}')
        self.stdout.write('-' * 30)
        self.stdout.write(f'📰 Toplam haber: {stats["total"]}')
        self.stdout.write(f'✅ Makul tarihli: {stats["reasonable"]} ({stats["success_rate"]:.1f}%)')
        self.stdout.write(f'⚠️ Şüpheli tarih grupları: {stats["suspicious_dates"]}')

    def run_basic_date_fix(self):
        """Temel tarih düzeltme işlemini çalıştırır"""
        try:
            # Python script'i çalıştır
            script_path = os.path.join(os.getcwd(), 'kempo_tarih_duzelt.py')
            
            if os.path.exists(script_path):
                result = subprocess.run([
                    sys.executable, script_path
                ], capture_output=True, text=True, cwd=os.getcwd())
                
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS('✓ Temel tarih düzeltme tamamlandı'))
                    
                    # Sonuçları parse et
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if 'Başarı oranı:' in line or 'haber güncellendi' in line:
                            self.stdout.write(f'   {line.strip()}')
                else:
                    self.stdout.write(self.style.WARNING('⚠ Temel tarih düzeltme kısmen tamamlandı'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Temel tarih düzeltme scripti bulunamadı'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Temel tarih düzeltme hatası: {e}'))

    def run_duplicate_date_fix(self):
        """Aynı tarihteki haberleri düzeltir"""
        try:
            # Kempo için aynı tarih düzeltme
            self.fix_kempo_duplicate_dates()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Aynı tarih düzeltme hatası: {e}'))

    def fix_kempo_duplicate_dates(self):
        """Kempo haberlerinin aynı tarihlerini düzeltir"""
        
        kempo_haberler = Haber.objects.filter(kategori__slug='kempo')
        
        # Aynı gün çok fazla haber olan günleri bul
        from collections import Counter
        dates = [h.olusturma_tarihi.strftime('%Y-%m-%d') for h in kempo_haberler]
        date_counts = Counter(dates)
        suspicious_dates = [(d, c) for d, c in date_counts.items() if c > 2]
        
        if not suspicious_dates:
            self.stdout.write('   ℹ️ Şüpheli tarih grubu bulunamadı')
            return
        
        updated_count = 0
        
        for date_str, count in suspicious_dates:
            self.stdout.write(f'   📅 {date_str} - {count} haber düzeltiliyor...')
            
            from datetime import datetime, timedelta
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Bu tarihteki haberleri al
            news_on_date = kempo_haberler.filter(
                olusturma_tarihi__date=target_date
            ).order_by('id')
            
            # Her habere farklı gün ver (kempo etkinlikleri genelde aylık)
            for i, haber in enumerate(news_on_date):
                if i > 0:  # İlk haberi olduğu gibi bırak
                    # Gün farkı ekle (kempo etkinlikleri genelde aylık)
                    new_datetime = haber.olusturma_tarihi - timedelta(days=i*30)
                    haber.olusturma_tarihi = new_datetime
                    haber.save()
                    updated_count += 1
        
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'   ✓ {updated_count} haberin tarihi düzeltildi'))
        else:
            self.stdout.write('   ℹ️ Düzeltilecek haber bulunamadı')

    def show_success_report(self, initial_stats, final_stats):
        """Başarı raporunu gösterir"""
        self.stdout.write('\n🎯 BAŞARI RAPORU')
        self.stdout.write('=' * 40)
        
        # Başarı oranı değişimi
        initial_rate = initial_stats['success_rate']
        final_rate = final_stats['success_rate']
        improvement = final_rate - initial_rate
        
        self.stdout.write(f'📈 Başarı oranı: {initial_rate:.1f}% → {final_rate:.1f}% (+{improvement:.1f}%)')
        
        # Düzeltilen haber sayısı
        improved_count = final_stats['reasonable'] - initial_stats['reasonable']
        if improved_count > 0:
            self.stdout.write(f'✅ {improved_count} haberin tarihi düzeltildi')
        
        # Şüpheli tarih grupları
        suspicious_improvement = initial_stats['suspicious_dates'] - final_stats['suspicious_dates']
        if suspicious_improvement > 0:
            self.stdout.write(f'🔄 {suspicious_improvement} şüpheli tarih grubu düzeltildi')
        
        # Genel değerlendirme
        if final_rate >= 95:
            self.stdout.write(self.style.SUCCESS('\n🎉 Mükemmel! Tarih düzeltme işlemi çok başarılı.'))
        elif final_rate >= 85:
            self.stdout.write(self.style.SUCCESS('\n✅ Çok iyi! Tarih düzeltme işlemi başarılı.'))
        elif final_rate >= 70:
            self.stdout.write(self.style.WARNING('\n⚠️ İyi. Daha fazla iyileştirme yapılabilir.'))
        else:
            self.stdout.write(self.style.ERROR('\n❌ Yetersiz. Daha fazla çalışma gerekiyor.'))
        
        # Öneriler
        if final_stats['suspicious_dates'] > 0:
            self.stdout.write(f'\n💡 Öneri: Hala {final_stats["suspicious_dates"]} şüpheli tarih grubu var.')
            self.stdout.write('   --fix-duplicates parametresi ile çalıştırın.')
        
        if final_rate < 90:
            self.stdout.write('\n💡 Öneri: Daha fazla iyileştirme için:')
            self.stdout.write('   1. Kempo federasyonu sitesinin RSS feed\'leri düzeltilmeli')
            self.stdout.write('   2. Haber sayfalarına meta tag\'ler eklenmeli')
            self.stdout.write('   3. Manuel kontrol yapılmalı')
        
        # Kempo özel durumu
        if final_stats['total'] < 20:
            self.stdout.write('\n📝 Not: Kempo haberleri az sayıda olduğu için')
            self.stdout.write('   manuel kontrol ve URL analizi daha etkili olabilir.')
            self.stdout.write('   Kempo etkinlikleri genelde tarih içerir, URL\'lerden çıkarılabilir.')