from django.core.management.base import BaseCommand
from django.utils import timezone
from haberler.models import Haber
from django.core.management import call_command
import subprocess
import sys
import os

class Command(BaseCommand):
    help = 'Tüm federasyon haberlerinin tarihlerini düzeltir (Boks ve Kickboks)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--federasyon',
            type=str,
            choices=['boks', 'kickboks', 'aikido', 'all'],
            default='all',
            help='Hangi federasyonun tarihleri düzeltilecek (varsayılan: all)',
        )
        parser.add_argument(
            '--fix-duplicates',
            action='store_true',
            help='Aynı tarihteki haberleri de düzelt',
        )

    def handle(self, *args, **options):
        self.stdout.write('🥊🥋 FEDERASYON HABERLERİ TARİH DÜZELTİCİ')
        self.stdout.write('=' * 70)
        
        federasyon = options['federasyon']
        
        if federasyon in ['boks', 'all']:
            self.stdout.write('\n🥊 BOKS FEDERASYONU TARİH DÜZELTİCİ')
            self.stdout.write('=' * 50)
            self.fix_boks_dates(options)
        
        if federasyon in ['kickboks', 'all']:
            self.stdout.write('\n🥋 KICKBOKS FEDERASYONU TARİH DÜZELTİCİ')
            self.stdout.write('=' * 50)
            self.fix_kickboks_dates(options)
        
        if federasyon in ['aikido', 'all']:
            self.stdout.write('\n🥋 AİKİDO FEDERASYONU TARİH DÜZELTİCİ')
            self.stdout.write('=' * 50)
            self.fix_aikido_dates(options)
        
        # Genel rapor
        self.show_general_report()

    def fix_boks_dates(self, options):
        """Boks haberlerinin tarihlerini düzeltir"""
        
        try:
            # Boks için kapsamlı tarih düzeltme
            args = []
            if options['fix_duplicates']:
                args.append('--fix-duplicates')
            
            call_command('boks_tarih_kapsamli_duzelt', *args, verbosity=1)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Boks tarih düzeltme hatası: {e}'))

    def fix_kickboks_dates(self, options):
        """Kickboks haberlerinin tarihlerini düzeltir"""
        
        try:
            # Kickboks için kapsamlı tarih düzeltme
            args = []
            if options['fix_duplicates']:
                args.append('--fix-duplicates')
            
            call_command('kickboks_tarih_kapsamli_duzelt', *args, verbosity=1)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Kickboks tarih düzeltme hatası: {e}'))

    def fix_aikido_dates(self, options):
        """Aikido haberlerinin tarihlerini düzeltir"""
        
        try:
            # Aikido için kapsamlı tarih düzeltme
            args = []
            if options['fix_duplicates']:
                args.append('--fix-duplicates')
            
            call_command('aikido_tarih_kapsamli_duzelt', *args, verbosity=1)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Aikido tarih düzeltme hatası: {e}'))

    def show_general_report(self):
        """Genel raporu gösterir"""
        
        self.stdout.write('\n📊 GENEL DURUM RAPORU')
        self.stdout.write('=' * 50)
        
        # Boks istatistikleri
        boks_haberler = Haber.objects.filter(kategori__slug='boks')
        boks_stats = self.get_category_stats(boks_haberler, 'Boks')
        
        # Kickboks istatistikleri
        kickboks_haberler = Haber.objects.filter(kategori__slug='kickboks')
        kickboks_stats = self.get_category_stats(kickboks_haberler, 'Kickboks')
        
        # Aikido istatistikleri
        aikido_haberler = Haber.objects.filter(kategori__slug='aikido')
        aikido_stats = self.get_category_stats(aikido_haberler, 'Aikido')
        
        # Toplam istatistikler
        total_haberler = boks_haberler.count() + kickboks_haberler.count() + aikido_haberler.count()
        total_reasonable = boks_stats['reasonable'] + kickboks_stats['reasonable'] + aikido_stats['reasonable']
        total_success_rate = (total_reasonable / total_haberler * 100) if total_haberler > 0 else 0
        
        self.stdout.write(f'\n📈 TOPLAM İSTATİSTİKLER:')
        self.stdout.write(f'   📰 Toplam haber: {total_haberler}')
        self.stdout.write(f'   ✅ Makul tarihli: {total_reasonable} ({total_success_rate:.1f}%)')
        
        # Başarı değerlendirmesi
        if total_success_rate >= 95:
            self.stdout.write(self.style.SUCCESS('\n🎉 Mükemmel! Tüm federasyon haberleri başarıyla düzeltildi.'))
        elif total_success_rate >= 85:
            self.stdout.write(self.style.SUCCESS('\n✅ Çok iyi! Federasyon haberleri başarıyla düzeltildi.'))
        elif total_success_rate >= 70:
            self.stdout.write(self.style.WARNING('\n⚠️ İyi. Daha fazla iyileştirme yapılabilir.'))
        else:
            self.stdout.write(self.style.ERROR('\n❌ Yetersiz. Daha fazla çalışma gerekiyor.'))
        
        # Öneriler
        self.show_recommendations(boks_stats, kickboks_stats, aikido_stats)

    def get_category_stats(self, haberler, category_name):
        """Kategori istatistiklerini alır"""
        
        total_count = haberler.count()
        now = timezone.now()
        
        # Makul tarih aralığındaki haberler
        reasonable_dates = haberler.filter(
            olusturma_tarihi__year__gte=2020,
            olusturma_tarihi__year__lte=2025,
            olusturma_tarihi__lte=now
        ).count()
        
        success_rate = (reasonable_dates / total_count * 100) if total_count > 0 else 0
        
        # Aynı gün çok fazla haber
        from collections import Counter
        dates = [h.olusturma_tarihi.strftime('%Y-%m-%d') for h in haberler]
        date_counts = Counter(dates)
        suspicious_dates = len([d for d, c in date_counts.items() if c > 3])
        
        self.stdout.write(f'\n📊 {category_name.upper()} İSTATİSTİKLERİ:')
        self.stdout.write(f'   📰 Toplam haber: {total_count}')
        self.stdout.write(f'   ✅ Makul tarihli: {reasonable_dates} ({success_rate:.1f}%)')
        self.stdout.write(f'   ⚠️ Şüpheli tarih grupları: {suspicious_dates}')
        
        return {
            'total': total_count,
            'reasonable': reasonable_dates,
            'suspicious_dates': suspicious_dates,
            'success_rate': success_rate
        }

    def show_recommendations(self, boks_stats, kickboks_stats, aikido_stats):
        """Önerileri gösterir"""
        
        self.stdout.write('\n💡 ÖNERİLER:')
        
        # Boks önerileri
        if boks_stats['success_rate'] < 95:
            self.stdout.write('\n🥊 Boks için:')
            if boks_stats['suspicious_dates'] > 0:
                self.stdout.write('   • --fix-duplicates ile aynı tarihteki haberleri düzeltin')
            if boks_stats['success_rate'] < 90:
                self.stdout.write('   • Boks federasyonu sitesinden daha fazla tarih kaynağı bulun')
                self.stdout.write('   • Manuel kontrol yapın')
        
        # Kickboks önerileri
        if kickboks_stats['success_rate'] < 95:
            self.stdout.write('\n🥋 Kickboks için:')
            if kickboks_stats['suspicious_dates'] > 0:
                self.stdout.write('   • --fix-duplicates ile aynı tarihteki haberleri düzeltin')
            if kickboks_stats['success_rate'] < 90:
                self.stdout.write('   • Kickboks federasyonu sitesinin teknik sorunları çözülmeli')
                self.stdout.write('   • Alternatif tarih kaynakları bulunmalı')
                self.stdout.write('   • Manuel kontrol daha etkili olabilir (az sayıda haber)')
        
        # Aikido önerileri
        if aikido_stats['success_rate'] < 95:
            self.stdout.write('\n🥋 Aikido için:')
            if aikido_stats['suspicious_dates'] > 0:
                self.stdout.write('   • --fix-duplicates ile aynı tarihteki haberleri düzeltin')
            if aikido_stats['success_rate'] < 90:
                self.stdout.write('   • URL\'lerden tarih çıkarma en etkili yöntem')
                self.stdout.write('   • Aikido etkinlik tarihlerini manuel kontrol edin')
                self.stdout.write('   • Sitemap\'ten daha fazla tarih bilgisi alınabilir')
        
        # Genel öneriler
        self.stdout.write('\n🔧 Genel öneriler:')
        self.stdout.write('   • Otomatik haber çekme sistemine tarih düzeltme entegre edildi')
        self.stdout.write('   • Günlük olarak: python manage.py haber_cek --all')
        self.stdout.write('   • Haftalık kontrol: python manage.py federasyon_tarih_duzelt')
        
        # Kullanım örnekleri
        self.stdout.write('\n📝 KULLANIM ÖRNEKLERİ:')
        self.stdout.write('   # Tüm federasyonlar:')
        self.stdout.write('   python manage.py federasyon_tarih_duzelt --fix-duplicates')
        self.stdout.write('')
        self.stdout.write('   # Sadece boks:')
        self.stdout.write('   python manage.py federasyon_tarih_duzelt --federasyon=boks')
        self.stdout.write('')
        self.stdout.write('   # Sadece kickboks:')
        self.stdout.write('   python manage.py federasyon_tarih_duzelt --federasyon=kickboks')
        self.stdout.write('')
        self.stdout.write('   # Sadece aikido:')
        self.stdout.write('   python manage.py federasyon_tarih_duzelt --federasyon=aikido')