from django.core.management.base import BaseCommand
from haberler.models import Haber, FederasyonWebsite
import re

class Command(BaseCommand):
    help = 'Türkiye Boks Federasyonu haberlerinin içeriklerini temizler'

    def handle(self, *args, **options):
        self.stdout.write('🥊 TÜRKİYE BOKS FEDERASYONU İÇERİK TEMİZLEME SİSTEMİ')
        self.stdout.write('=' * 60)
        
        try:
            # Türkiye Boks Federasyonu'nu bul
            federation = FederasyonWebsite.objects.get(ad='Türkiye Boks Federasyonu')
        except FederasyonWebsite.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Türkiye Boks Federasyonu veritabanında bulunamadı')
            )
            return
        
        # Federasyona ait tüm haberleri bul
        news_items = Haber.objects.filter(federasyon_website=federation)
        
        if not news_items.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  Türkiye Boks Federasyonu için haber bulunamadı')
            )
            return
        
        self.stdout.write(f'📊 Toplam {news_items.count()} haber bulundu')
        
        # Her bir haberi temizle
        cleaned_count = 0
        for news in news_items:
            original_content = news.icerik
            
            # Temizleme işlemi
            cleaned_content = self._clean_content(original_content)
            
            # İçerik değiştiyse güncelle
            if cleaned_content != original_content:
                news.icerik = cleaned_content
                news.save()
                cleaned_count += 1
                self.stdout.write(f'✅ Temizlendi: {news.baslik[:50]}...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İŞLEM TAMAMLANDI! '
                f'Toplam {cleaned_count} haber temizlendi.'
            )
        )
    
    def _clean_content(self, content):
        """İçeriği temizler"""
        if not content:
            return content
        
        # Remove navigation text at the beginning
        # Telefon ve email adreslerini kaldır
        content = re.sub(r'^Telefon:\s*\n?\d[^\n]*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'^E-Posta Adresi:\s*\n?[^\n]*@.*?\n?', '', content, flags=re.MULTILINE)
        
        # Toggle navigation metnini kaldır
        content = re.sub(r'^Toggle navigation\s*\n?', '', content, flags=re.MULTILINE)
        
        # Federasyon menü öğelerini kaldır
        menu_items = [
            'Bakanlık', 'Federasyonumuz', 'Başkanımız', 'Yönetim Kurulu',
            'Ana Statü', 'Talimatlar', 'İhaleler', 'Yönetmelikler',
            'İdari Personel', 'Türk Boks Tarihi', 'Dünya Boks Tarihi',
            'İletişim', 'Faaliyet Takvimi', 'Hakemler', 'Kurullar',
            'MERKEZ HAKEM KOMİTESİ', 'PLANLAMA VE KOORDİNASYON KURULU',
            'BİLİM KURULU', 'HUKUK KURULU', 'SAĞLIK KURULU',
            'ORGANİZASYON VE DIŞ İLİŞKİLER KURULU', 'ONUR KURULU',
            'ETİK KURULU', 'BASIN KURULU', 'TEKNİK KURULU',
            'EĞİTİM KURULU', 'DENETLEME KURULU', 'DİSİPLİN KURULU'
        ]
        
        for item in menu_items:
            content = re.sub(rf'^{re.escape(item)}\s*\n?', '', content, flags=re.MULTILINE)
        
        # Remove common website navigation patterns
        content = re.sub(r'Anasayfa\s*\n?Haber\s*\n?DÜNYA BOKS ŞAMPİYONASINDA İKİ GÜMÜŞ, BİR BRONZ MADALYA KAZANDIK\s*\n?Comments \(.*?\)\s*\n?', '', content, flags=re.MULTILINE)
        
        # Remove date and comment patterns
        content = re.sub(r'Eyl \d{1,2}\s*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'Ağu \d{1,2}\s*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'Comments \(.*?\)\s*\n?', '', content, flags=re.MULTILINE)
        
        # Remove navigation text at the end
        # Look for the pattern that indicates the end of actual content
        end_patterns = [
            r'\n\s*Paylaş:.*$',
            r'\n\s*Arat.*$',
            r'\n\s*Güncel Duyurular.*$',
            r'\n\s*Son Haberler.*$',
            r'\n\s*Telefon:.*$',
            r'\n\s*E-Posta:.*$',
            r'\n\s*Adres:.*$',
            r'\n\s*Faks:.*$',
            r'\n\s*Flaticon-.*$',
            r'\n\s*Kurumsal.*$',
            r'\n\s*Vizyonumuz ve Misyonumuz.*$',
            r'\n\s*Federasyon.*$',
            r'\n\s*Hakkımızda.*$',
            r'\n\s*Fotoğraf Galerisi.*$',
            r'\n\s*Hızlı Linkler.*$',
            r'\n\s*Ana Sayfa.*$',
            r'\n\s*Türk Boks Federasyonu ©.*$'
        ]
        
        # Apply each pattern to clean the end of content
        for pattern in end_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove extra whitespace and clean up content
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'^\s+', '', content)  # Remove leading whitespace
        content = re.sub(r'\s+$', '', content)  # Remove trailing whitespace
        
        return content