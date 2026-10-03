import re
from django.core.management.base import BaseCommand
from haberler.models import Haber

class Command(BaseCommand):
    help = 'Clean up existing news content by removing unwanted navigation and menu text'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit the number of articles to process (default: 100)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually making changes',
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        # Get news articles that were automatically imported
        haberler = Haber.objects.filter(otomatik_eklendi=True)[:limit]
        
        self.stdout.write(f"Processing {len(haberler)} news articles...")
        if dry_run:
            self.stdout.write("(DRY RUN - no changes will be made)")
        
        cleaned_count = 0
        # More specific navigation patterns that are clearly not content
        nav_patterns = [
            'ANASAYFA', 'KURUMSAL', 'HABERLER', 'İLETİŞİM',
            'T.C. Gençlik ve Spor Bakanımız', 'Onursal Başkanımız',
            'Federasyon Başkanımız', 'Genel Sekreterimiz',
            'Başkan Danışmanımız', 'Kurullarımız',
            'KULÜP BİLGİ SİSTEMİ', 'FAALİYET TAKVİMİ',
            'KARATE TÜRK TV', 'Y.T.K.F.Web Sitesi',
            'SOSYAL MEDYA', 'Etkinlikler', 'Duyurular',
            'Faaliyet Programı', 'Resmi Evraklar',
            'Federasyon Talimatları', 'Fotoğraf Galerisi',
            'Video Galeri', 'İletişim Formu', 'TKF MENÜ',
            # Removed 'Gazze Karate Turnuvası Açılış Töreni Gerçekleştirildi' as it's actual content
            'Karate-Do Nedir?', 'Tarihçe', 'Vizyonumuz', 'Misyonumuz',
            'Stratejik Plan', 'Arama Yap',
            # Additional patterns for content at the end of articles
            'Daha Fazla Göster', 'Devamı Oku', 'GÜNCEL DUYURULAR', 
            'ETKİNLİKLER', 'DİĞER HABERLER', 'GENEL HABERLER',
            # Specific unwanted text patterns
            'Suudi Antrenörler Derneği Başkanı’ndan Dostluk Plaketi',
            'Gençlik ve Spor Bakanımız Sayın Osman Aşkın Bak, Diyarbakır’da Bizleri Yalnız Bırakmadı'
        ]
        
        # Regex patterns for date lines
        nav_regex_patterns = [
            r'\d{1,2} \w+ 2025 \d{1,2}:\d{2}'
        ]
        
        # Also add patterns that indicate navigation/menu sections
        nav_indicators = [
            'Menü', 'MENU', 'NAVIGATION', 'NAVİGASYON'
        ]
        
        for haber in haberler:
            original_content = haber.icerik
            
            # Clean the content
            cleaned_content = self.clean_content(original_content, nav_patterns, nav_regex_patterns, nav_indicators)
            
            # Only update if content was actually changed and not emptied
            if cleaned_content != original_content and cleaned_content.strip():
                if not dry_run:
                    haber.icerik = cleaned_content
                    haber.save(update_fields=['icerik'])
                cleaned_count += 1
                self.stdout.write(f"  ✓ Cleaned: {haber.baslik}")
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Would clean {cleaned_count} news articles out of {len(haberler)} processed (dry run)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleaned {cleaned_count} news articles out of {len(haberler)} processed"
                )
            )
    
    def clean_content(self, content, nav_patterns, nav_regex_patterns, nav_indicators):
        """Clean content by removing unwanted navigation and menu text"""
        if not content:
            return content
        
        # Split content into lines
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Skip lines containing navigation patterns
            line_upper = line.upper()
            is_nav_line = any(pattern in line for pattern in nav_patterns) or \
                         any(indicator in line_upper for indicator in nav_indicators)
            
            # Check regex patterns
            if not is_nav_line:
                for regex_pattern in nav_regex_patterns:
                    if re.search(regex_pattern, line):
                        is_nav_line = True
                        break
            
            # Additional check: very short lines with common navigation words
            if not is_nav_line and len(line.strip()) < 20:
                short_nav_words = ['ANASAYFA', 'HABERLER', 'İLETİŞİM', 'GALERİ']
                is_nav_line = any(word in line_upper for word in short_nav_words)
            
            if not is_nav_line:
                cleaned_lines.append(line)
        
        # Join the cleaned lines
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Remove extra whitespace but be less aggressive
        cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)  # Limit to double newlines
        cleaned_content = re.sub(r'[ \t]+', ' ', cleaned_content)  # Remove extra spaces/tabs
        
        return cleaned_content.strip()