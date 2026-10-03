from django.core.management.base import BaseCommand
from haberler.models import Haber
import re
from django.db import transaction

class Command(BaseCommand):
    help = 'Haber içeriklerindeki navigasyon menüsü ve sidebar yazılarını temizler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece analiz yap, değişiklik yapma'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Temizlenecek maksimum haber sayısı (0 = tümü)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        self.stdout.write('🧹 HABER İÇERİKLERİ TEMİZLEME SİSTEMİ')
        self.stdout.write('=' * 50)
        
        # Navigation and sidebar content patterns to remove
        navigation_patterns = [
            # Main navigation menu items
            r'Karate-Do Nedir\?',
            r'Tarihçe',
            r'Vizyonumuz',
            r'Misyonumuz',
            r'Stratejik Plan',
            r'Arama Yap',
            r'ANASAYFA',
            r'KURUMSAL',
            r'HABERLER',
            r'İLETİŞİM',
            
            # Personnel and organization
            r'T\.C\. Gençlik ve Spor Bakanımız',
            r'Onursal Başkanımız[^\.]*',
            r'Federasyon Başkanımız[^\.]*',
            r'Genel Sekreterimiz[^\.]*',
            r'Başkan Danışmanımız[^\.]*',
            r'Kurullarımız',
            
            # System and features
            r'KULÜP BİLGİ SİSTEMİ',
            r'FAALİYET TAKVİMİ',
            r'KARATE TÜRK TV',
            r'Y\.T\.K\.F\.Web Sitesi',
            r'TKF MENÜ',
            r'SOSYAL MEDYA',
            r'İletişim Formu',
            
            # Sidebar content
            r'DİĞER HABERLER',
            r'GENEL HABERLER',
            r'GÜNCEL DUYURULAR',
            r'ETKİNLİKLER',
            r'Foto Galeri',
            r'Video Galeri',
            r'Devamı Oku',
            r'Daha Fazla',
            
            # Federation specific
            r'Türkiye Karate Federasyonu',
            
            # Generic patterns
            r'Hakkı [A-Z]+',
            r'Esat [A-Z]+',
            r'Orhan [A-Z]+',
            r'Ercüment [A-Z]+',
            r'Hacı [A-Z]+',
            r'Adem [A-Z]+',
            r'Alihan [A-Z]+',
        ]
        
        # Compile patterns
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in navigation_patterns]
        
        # Get news to clean
        haberler_query = Haber.objects.all()
        if limit > 0:
            haberler_query = haberler_query[:limit]
        
        haberler = list(haberler_query)
        total_news = len(haberler)
        
        self.stdout.write(f'📊 Toplam {total_news} haber analiz edilecek')
        
        cleaned_count = 0
        significant_changes = 0
        
        for i, haber in enumerate(haberler, 1):
            try:
                original_content = haber.icerik
                original_length = len(original_content)
                
                if original_length == 0:
                    continue
                
                # Clean the content
                cleaned_content = self._clean_content(original_content, compiled_patterns)
                new_length = len(cleaned_content)
                
                # Calculate reduction percentage
                reduction_percent = ((original_length - new_length) / original_length * 100) if original_length > 0 else 0
                
                if new_length != original_length:
                    cleaned_count += 1
                    
                    if reduction_percent > 50:  # Significant change
                        significant_changes += 1
                        self.stdout.write(
                            f'🔍 [{i}/{total_news}] {haber.baslik[:50]}...'
                        )
                        self.stdout.write(
                            f'   📏 {original_length} → {new_length} karakter (%{reduction_percent:.1f} azalma)'
                        )
                        
                        if dry_run:
                            self.stdout.write(f'   📝 ÖNIZLEME: {cleaned_content[:200]}...')
                        
                    if not dry_run:
                        haber.icerik = cleaned_content
                        haber.save(update_fields=['icerik'])
                
                # Progress indicator for every 10 items
                if i % 10 == 0:
                    self.stdout.write(f'📊 İşlendi: {i}/{total_news}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Hata [{i}]: {haber.baslik[:30]}... - {e}')
                )
        
        # Summary
        self.stdout.write('\n📋 ÖZET:')
        self.stdout.write(f'   📊 Analiz edilen: {total_news} haber')
        self.stdout.write(f'   ✅ Değiştirilen: {cleaned_count} haber')
        self.stdout.write(f'   🔥 Büyük değişiklik: {significant_changes} haber')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN - Gerçek değişiklik yapılmadı')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Temizleme işlemi tamamlandı!')
            )

    def _clean_content(self, content, patterns):
        """Clean content by removing navigation and sidebar text"""
        cleaned = content
        
        # Strategy: Extract the actual news content from the mess
        # The real content usually starts after the date pattern
        
        # Look for date pattern that indicates start of real content
        date_pattern = r'(\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}\s+\d{1,2}:\d{2})'
        date_match = re.search(date_pattern, content)
        
        if date_match:
            # Found date, extract content after it
            start_pos = date_match.end()
            
            # Find where the actual article ends (before "DİĞER HABERLER" or similar)
            end_patterns = [
                r'DİĞER HABERLER',
                r'GENEL HABERLER',
                r'GÜNCEL DUYURULAR',
                r'ETKİNLİKLER',
                r'Daha Fazla Göster',
                r'Devamı Oku',
                r'FOTO GALERİ',
                r'VİDEO GALERİ',
                r'KURUMSAL',
                r'Bize Ulaşın',
                r'Copyright',
                r'BİLGİ BANKASI'
            ]
            
            end_pos = len(content)
            for end_pattern in end_patterns:
                match = re.search(end_pattern, content[start_pos:], re.IGNORECASE)
                if match:
                    potential_end = start_pos + match.start()
                    end_pos = min(end_pos, potential_end)
            
            # Extract the clean content
            article_content = content[start_pos:end_pos].strip()
            
            # Clean up any remaining navigation bits
            article_content = re.sub(r'\s+', ' ', article_content)
            
            # Remove any stray navigation elements that might remain
            cleanup_patterns = [
                r'^[^a-zA-ZğüşıöçĞÜŞİÖÇ]*',  # Remove leading non-letter characters
                r'Geri$',
                r'TKF MENÜ.*?SOSYAL MEDYA',
            ]
            
            for cleanup in cleanup_patterns:
                article_content = re.sub(cleanup, '', article_content, flags=re.IGNORECASE | re.DOTALL)
            
            article_content = article_content.strip()
            
            if len(article_content) > 50:  # Reasonable content length
                return article_content
        
        # Fallback: if no date pattern found, try to extract by removing known navigation
        # Remove the entire navigation block from the beginning
        navigation_start = r'^.*?İLETİŞİM'
        cleaned = re.sub(navigation_start, '', content, flags=re.DOTALL)
        
        # Remove sidebar content from the end
        sidebar_patterns = [
            r'DİĞER HABERLER.*$',
            r'GENEL HABERLER.*$',
            r'GÜNCEL DUYURULAR.*$',
            r'ETKİNLİKLER.*$',
            r'FOTO GALERİ.*$',
            r'VİDEO GALERİ.*$',
            r'KURUMSAL.*$',
            r'BİLGİ BANKASI.*$',
            r'BAĞLANTILAR.*$',
            r'BANKA HESAP.*$',
            r'Copyright.*$',
        ]
        
        for sidebar_pattern in sidebar_patterns:
            cleaned = re.sub(sidebar_pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up formatting
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # If still too short, it might be all navigation
        if len(cleaned) < 50:
            return ""
        
        return cleaned

    def _extract_meaningful_content(self, haber):
        """Try to extract meaningful content when article is mostly navigation"""
        # Use title and summary as fallback content
        meaningful_content = f"{haber.baslik}\n\n"
        
        if haber.ozet and haber.ozet != haber.baslik:
            meaningful_content += haber.ozet
        else:
            meaningful_content += "Bu haberin detaylı içeriği henüz mevcut değil."
        
        return meaningful_content