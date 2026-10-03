from django.core.management.base import BaseCommand
from haberler.models import Haber
from haberler.services.news_scraper import NewsScrapingService
import re

class Command(BaseCommand):
    help = 'Eksik veya eksik haber içeriklerini düzeltir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='İşlenecek maksimum haber sayısı (0 = tümü)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece analiz yap, değişiklik yapma'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write('🔧 EKSİK İÇERİK DÜZELTME SİSTEMİ')
        self.stdout.write('=' * 50)
        
        # Initialize the scraping service
        scraper = NewsScrapingService()
        
        # Find articles with potentially incomplete content
        haberler_query = Haber.objects.filter(
            otomatik_eklendi=True,
            kaynak_url__isnull=False
        ).exclude(kaynak_url='')
        
        if limit > 0:
            haberler_query = haberler_query[:limit]
        
        haberler = list(haberler_query)
        total_news = len(haberler)
        
        self.stdout.write(f'📊 Toplam {total_news} otomatik eklenmiş haber analiz edilecek')
        
        fixed_count = 0
        failed_count = 0
        
        for i, haber in enumerate(haberler, 1):
            try:
                # Check if content is incomplete
                if self._is_content_incomplete(haber):
                    self.stdout.write(f'🔍 [{i}/{total_news}] Eksik içerik tespit edildi: {haber.baslik[:50]}...')
                    
                    if not dry_run:
                        # Try to recover content
                        fresh_content = scraper.get_news_content(haber.kaynak_url)
                        
                        if fresh_content and len(fresh_content) > 100:
                            # Save the recovered content
                            haber.icerik = fresh_content
                            haber.save(update_fields=['icerik'])
                            fixed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'   ✅ İçerik düzeltildi ({len(fresh_content)} karakter)')
                            )
                        else:
                            failed_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'   ⚠️  İçerik kurtarılamadı')
                            )
                    else:
                        self.stdout.write(f'   📝 DRY RUN - Değişiklik yapılmayacak')
                        fixed_count += 1  # Count as if it would be fixed
                
                # Progress indicator
                if i % 10 == 0:
                    self.stdout.write(f'📊 İşlendi: {i}/{total_news}')
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Hata [{i}]: {haber.baslik[:30]}... - {e}')
                )
        
        # Summary
        self.stdout.write('\n📋 ÖZET:')
        self.stdout.write(f'   📊 Analiz edilen: {total_news} haber')
        self.stdout.write(f'   ✅ Düzeltilebilen: {fixed_count} haber')
        self.stdout.write(f'   ❌ Başarısız: {failed_count} haber')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN - Gerçek değişiklik yapılmadı')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Eksik içerik düzeltme işlemi tamamlandı!')
            )

    def _is_content_incomplete(self, haber):
        """Check if news content is incomplete or missing"""
        content = haber.icerik.strip()
        
        # Empty content
        if not content:
            return True
            
        # Very short content (less than 100 characters)
        if len(content) < 100:
            return True
            
        # Content that looks like navigation only
        navigation_indicators = [
            'ANASAYFA', 'HABERLER', 'İLETİŞİM', 'KURUMSAL',
            'Geri\n', 'TKF MENÜ', 'SOSYAL MEDYA'
        ]
        
        # Check if content starts with navigation
        for indicator in navigation_indicators:
            if content.startswith(indicator):
                return True
                
        # Check if content is mostly navigation/footer text
        if any(nav_text in content[:200] for nav_text in navigation_indicators):
            # Additional check: if content is very short after removing navigation
            cleaned_content = re.sub('|'.join(navigation_indicators), '', content, flags=re.IGNORECASE)
            if len(cleaned_content.strip()) < 100:
                return True
        
        # Content that ends with common navigation/footer patterns
        end_patterns = [
            r'DİĞER HABERLER.*$', 
            r'GENEL HABERLER.*$', 
            r'GÜNCEL DUYURULAR.*$',
            r'ETKİNLİKLER.*$',
            r'FOTO GALERİ.*$',
            r'VİDEO GALERİ.*$',
            r'KURUMSAL.*$'
        ]
        
        for pattern in end_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                # Check if the content before this pattern is too short
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    before_content = content[:match.start()].strip()
                    if len(before_content) < 200:
                        return True
        
        # Content with mostly repeated navigation text
        nav_count = 0
        for indicator in navigation_indicators:
            nav_count += len(re.findall(re.escape(indicator), content, re.IGNORECASE))
        
        # If navigation text appears too frequently
        if nav_count > 3 and len(content) < 500:
            return True
            
        return False