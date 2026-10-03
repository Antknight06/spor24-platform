from django.core.management.base import BaseCommand
from haberler.models import Haber
from haberler.services.news_scraper import NewsScrapingService
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

class Command(BaseCommand):
    help = 'Her haberin doğru resimle eşleşmesini sağla - yanlış resim atamasını düzelt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='İşlenecek haber sayısı (varsayılan: 10)'
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Tüm haberleri düzelt'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        fix_all = options['fix_all']
        
        # Kaynak URL'si olan haberleri al
        queryset = Haber.objects.filter(
            kaynak_url__isnull=False,
            kaynak_url__contains='karate.gov.tr'
        ).exclude(kaynak_url='')
        
        if not fix_all:
            queryset = queryset[:limit]
        
        haberler = queryset
        
        if not haberler.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  İşlenecek karate.gov.tr haberı bulunamadı.')
            )
            return
        
        self.stdout.write(f'🔧 {haberler.count()} haber için resim eşleştirmesi düzeltiliyor...\n')
        
        success_count = 0
        failed_count = 0
        
        for haber in haberler:
            try:
                self.stdout.write(f'📰 İşleniyor: {haber.baslik[:50]}...')
                
                # Mevcut yanlış resmi sil
                if haber.resim:
                    old_image_name = haber.resim.name
                    haber.resim.delete(save=False)
                    self.stdout.write(f'   🗑️  Yanlış resim silindi: {old_image_name}')
                
                # Bu haberin kendi sayfasından doğru resmi çek
                success = self._get_exact_image_for_article(haber)
                
                if success:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Doğru resim atandı: {haber.resim.name}')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Doğru resim bulunamadı')
                    )
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Resim eslestime duzeltmesi tamamlandi! '
                f'✅ {success_count} basarili, ⚠️ {failed_count} basarisiz'
            )
        )

    def _get_exact_image_for_article(self, haber):
        """Bu haberin kendi sayfasindaki tam resmi bul ve ata"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(haber.kaynak_url, timeout=30, headers=headers, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Bu sayfadaki ANA resmi bul (sadece ilk ve en önemlisini)
            main_image_selectors = [
                'img.haber-detay-image',  # Ana haber resmi
                '.haber-detay-image'      # Ana haber resmi (class)
            ]
            
            # Önce ana resmi ara
            for selector in main_image_selectors:
                images = soup.select(selector)
                if images:
                    img = images[0]  # Sadece ilk (ana) resmi al
                    src = img.get('src') or img.get('data-src')
                    if src and self._is_main_article_image(src):
                        full_url = self._build_correct_url(src, haber.kaynak_url)
                        self.stdout.write(f'   🎯 Ana resim bulundu: {src}')
                        return self._download_and_assign_image(full_url, haber, src)
            
            # Ana resim bulunamadıysa, haber klasöründeki ilk resmi al
            fallback_selectors = [
                'img[src*=\"/uploads/haberler/\"][src*=\"IMG\"]:first-of-type',
                'img[src*=\"/uploads/haberler/\"][src*=\".jpeg\"]:first-of-type',
                'img[src*=\"/uploads/haberler/\"][src*=\".jpg\"]:first-of-type'
            ]
            
            for selector in fallback_selectors:
                images = soup.select(selector)
                if images:
                    img = images[0]  # Sadece ilk resmi al
                    src = img.get('src') or img.get('data-src')
                    if src and self._is_main_article_image(src):
                        full_url = self._build_correct_url(src, haber.kaynak_url)
                        self.stdout.write(f'   📸 Yedek resim bulundu: {src}')
                        return self._download_and_assign_image(full_url, haber, src)
            
            return False
            
        except Exception as e:
            self.stdout.write(f'   ❌ Sayfa analiz hatası: {e}')
            return False

    def _is_main_article_image(self, src):
        """Resmin ana makale resmi olup olmadigini kontrol et"""
        src_lower = src.lower()
        
        # Arkaplan, logo, ikon gibi resimleri atla
        skip_patterns = [
            'arkaplan', 'logo', 'icon', 'yukleniyor', 'loading',
            'banner', 'header', 'footer', 'social'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False
        
        # Haber resmi klasöründe olmalı
        return '/uploads/haberler/' in src_lower

    def _build_correct_url(self, src, base_url):
        """Dogru tam URL'yi olustur"""
        if src.startswith('http'):
            return src
        elif src.startswith('tema/'):
            return f'https://karate.gov.tr/{src}'
        else:
            return urljoin(base_url, src)

    def _download_and_assign_image(self, image_url, haber, original_src):
        """Resmi indir ve habere ata"""
        try:
            # URL'nin erişilebilir olup olmadığını kontrol et
            head_response = requests.head(image_url, timeout=10, verify=False)
            if head_response.status_code != 200:
                self.stdout.write(f'   ❌ Resim erişilemez: {head_response.status_code}')
                return False
            
            # NewsScrapingService kullanarak resmi indir
            scraper = NewsScrapingService()
            
            # Turkish character encoding fix
            try:
                image_file = scraper.download_and_process_image(image_url, haber.baslik)
            except UnicodeEncodeError:
                # Fallback: use safe title
                safe_title = (haber.baslik
                             .replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u')
                             .replace('ş', 's').replace('ç', 'c').replace('ö', 'o'))
                image_file = scraper.download_and_process_image(image_url, safe_title)
            
            if image_file:
                haber.resim.save(image_file.name, image_file, save=True)
                return True
            
            return False
            
        except Exception as e:
            self.stdout.write(f'   ❌ Indirme hatasi: {e}')
            return False