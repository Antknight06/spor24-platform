from django.core.management.base import BaseCommand
from django.utils import timezone
from haberler.models import Haber
import subprocess
import sys
import os

class Command(BaseCommand):
    help = 'Boks federasyonu haberlerinin tarihlerini kapsamlı şekilde düzeltir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Tüm boks haberlerini işle (varsayılan: son 50 haber)',
        )
        parser.add_argument(
            '--fix-duplicates',
            action='store_true',
            help='Aynı tarihteki haberleri de düzelt',
        )

    def handle(self, *args, **options):
        self.stdout.write('🥊 KAPSAMLI BOKS TARİH DÜZELTİCİ')
        self.stdout.write('=' * 60)
        
        # Başlangıç durumu
        initial_stats = self.get_stats()
        self.show_stats("BAŞLANGIÇ DURUMU", initial_stats)
        
        # 1. Temel tarih düzeltme
        self.stdout.write('\n📋 1. TEMEL TARİH DÜZELTME')
        self.stdout.write('-' * 40)
        self.run_basic_date_fix(options)
        
        # 2. Gelişmiş tarih çıkarma
        self.stdout.write('\n🔍 2. GELİŞMİŞ TARİH ÇIKARMA')
        self.stdout.write('-' * 40)
        self.run_advanced_date_extraction()
        
        # 3. Aynı tarihteki haberleri düzelt
        if options['fix_duplicates']:
            self.stdout.write('\n🔄 3. AYNI TARİHTEKİ HABERLERİ DÜZELT')
            self.stdout.write('-' * 40)
            self.run_duplicate_date_fix()
        
        # Son durum
        final_stats = self.get_stats()
        self.show_stats("SON DURUM", final_stats)
        
        # Başarı raporu
        self.show_success_report(initial_stats, final_stats)

    def get_stats(self):
        """İstatistikleri alır"""
        boks_haberler = Haber.objects.filter(kategori__slug='boks')
        
        total_count = boks_haberler.count()
        now = timezone.now()
        
        # Makul tarih aralığındaki haberler
        reasonable_dates = boks_haberler.filter(
            olusturma_tarihi__year__gte=2020,
            olusturma_tarihi__year__lte=2025,
            olusturma_tarihi__lte=now
        ).count()
        
        # Aynı gün çok fazla haber
        from collections import Counter
        dates = [h.olusturma_tarihi.strftime('%Y-%m-%d') for h in boks_haberler]
        date_counts = Counter(dates)
        suspicious_dates = len([d for d, c in date_counts.items() if c > 5])
        
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

    def run_basic_date_fix(self, options):
        """Temel tarih düzeltme işlemini çalıştırır"""
        try:
            limit = 100 if options['all'] else 50
            
            # Management command'i çalıştır
            from django.core.management import call_command
            call_command('boks_tarih_duzelt', '--recent', f'--limit={limit}', verbosity=0)
            
            self.stdout.write(self.style.SUCCESS('✓ Temel tarih düzeltme tamamlandı'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Temel tarih düzeltme hatası: {e}'))

    def run_advanced_date_extraction(self):
        """Gelişmiş tarih çıkarma işlemini çalıştırır"""
        try:
            # Python script'i çalıştır
            script_path = os.path.join(os.getcwd(), 'boks_gelismis_api_tarih.py')
            
            if os.path.exists(script_path):
                result = subprocess.run([
                    sys.executable, script_path
                ], capture_output=True, text=True, cwd=os.getcwd())
                
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS('✓ Gelişmiş tarih çıkarma tamamlandı'))
                    
                    # Sonuçları parse et
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if 'haber tarihi alındı' in line or 'haber güncellendi' in line:
                            self.stdout.write(f'   {line.strip()}')
                else:
                    self.stdout.write(self.style.WARNING('⚠ Gelişmiş tarih çıkarma kısmen tamamlandı'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Gelişmiş tarih çıkarma scripti bulunamadı'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Gelişmiş tarih çıkarma hatası: {e}'))

    def run_duplicate_date_fix(self):
        """Aynı tarihteki haberleri düzeltir"""
        try:
            # Python script'i çalıştır
            script_path = os.path.join(os.getcwd(), 'boks_ayni_tarih_duzelt.py')
            
            if os.path.exists(script_path):
                result = subprocess.run([
                    sys.executable, script_path
                ], capture_output=True, text=True, cwd=os.getcwd())
                
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS('✓ Aynı tarihteki haberler düzeltildi'))
                    
                    # Sonuçları parse et
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if 'haber güncellendi' in line:
                            self.stdout.write(f'   {line.strip()}')
                else:
                    self.stdout.write(self.style.WARNING('⚠ Aynı tarih düzeltme kısmen tamamlandı'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Aynı tarih düzeltme scripti bulunamadı'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Aynı tarih düzeltme hatası: {e}'))

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
            self.stdout.write('   1. Yeni tarih kaynakları ekleyin')
            self.stdout.write('   2. Haber içeriklerini daha detaylı analiz edin')
            self.stdout.write('   3. Manuel kontrol yapın')