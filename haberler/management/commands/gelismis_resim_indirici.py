from django.core.management.base import BaseCommand
from haberler.models import Haber, FederasyonWebsite
from haberler.services.news_scraper import NewsScrapingService
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Gelişmiş resim indirici - Mevcut haberlere federasyon sitelerinden resim bul ve indir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='İşlenecek haber sayısı (varsayılan: 20)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mevcut resimleri de değiştir'
        )
        parser.add_argument(
            '--federation-id',
            type=int,
            help='Sadece belirtilen federasyon haberlerini işle'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        federation_id = options.get('federation_id')
        
        # Hangi haberleri işleyeceğimizi belirle
        queryset = Haber.objects.filter(
            kaynak_url__isnull=False,
            yayinlandi=True
        ).exclude(kaynak_url='')
        
        if not force:
            queryset = queryset.filter(resim__isnull=True)
        
        if federation_id:
            queryset = queryset.filter(federasyon_website_id=federation_id)
        
        haberler = queryset[:limit]
        
        if not haberler.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  İşlenecek haber bulunamadı.')
            )
            return
        
        self.stdout.write(f'🖼️  {haberler.count()} haber için gelişmiş resim arama başlıyor...\n')
        
        scraper = NewsScrapingService()
        success_count = 0
        failed_count = 0
        
        for haber in haberler:
            try:
                self.stdout.write(f'📰 İşleniyor: {haber.baslik[:60]}...')
                
                # Önce mevcut kaynak URL'den resim aramayı dene
                success = self._download_image_from_source(haber, scraper)
                
                # Eğer başarısız olursa, alternatif kaynaklarda ara
                if not success:
                    success = self._search_alternative_images(haber, scraper)
                
                # Son çare olarak federasyon sitesinin ana sayfasından genel resim bul
                if not success and haber.federasyon_website:
                    success = self._get_federation_default_image(haber, scraper)
                
                if success:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Resim başarıyla eklendi')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Resim bulunamadı')
                    )
                
                # Nazik bir bekleme süresi
                time.sleep(2)
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Hata: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 İşlem tamamlandı! '
                f'✅ {success_count} başarılı, ⚠️ {failed_count} başarısız'
            )
        )

    def _download_image_from_source(self, haber, scraper):
        """Haber kaynağından resim indirmeyi dene"""
        try:
            image_urls = scraper.get_news_images(haber.kaynak_url)
            
            if image_urls:
                for image_url in image_urls:
                    # Her resim URL'ini test et
                    try:
                        response = requests.head(image_url, timeout=10)
                        if response.status_code == 200:
                            image_file = scraper.download_and_process_image(
                                image_url, haber.baslik
                            )
                            if image_file:
                                haber.resim.save(image_file.name, image_file, save=True)
                                return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Source image download failed for {haber.baslik}: {e}")
            return False

    def _search_alternative_images(self, haber, scraper):
        """Alternatif kaynaklardan resim ara"""
        try:
            # Haber başlığından anahtar kelimeler çıkar
            keywords = self._extract_keywords(haber.baslik)
            
            # Federasyon sitesinde genel arama yap
            if haber.federasyon_website:
                search_urls = [
                    f"{haber.federasyon_website.ana_url}/galeri",
                    f"{haber.federasyon_website.ana_url}/resimler", 
                    f"{haber.federasyon_website.ana_url}/images",
                    haber.federasyon_website.ana_url
                ]
                
                for search_url in search_urls:
                    try:
                        response = requests.get(search_url, timeout=15)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Karate ile ilgili resimleri bul
                            images = soup.find_all('img')
                            for img in images:
                                src = img.get('src') or img.get('data-src')
                                if src and self._is_relevant_image(src, keywords):
                                    full_url = urljoin(search_url, src)
                                    image_file = scraper.download_and_process_image(
                                        full_url, haber.baslik
                                    )
                                    if image_file:
                                        haber.resim.save(image_file.name, image_file, save=True)
                                        return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Alternative image search failed for {haber.baslik}: {e}")
            return False

    def _get_federation_default_image(self, haber, scraper):
        """Federasyon sitesinden varsayılan bir resim al"""
        try:
            if not haber.federasyon_website:
                return False
                
            response = requests.get(haber.federasyon_website.ana_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Logo veya ana resim ara
                logo_selectors = [
                    'img[alt*="karate"]',
                    'img[src*="logo"]',
                    '.header img',
                    '.logo img',
                    'img[alt*="federasyon"]'
                ]
                
                for selector in logo_selectors:
                    images = soup.select(selector)
                    for img in images:
                        src = img.get('src')
                        if src and not any(skip in src.lower() for skip in ['favicon', 'icon', 'thumb']):
                            full_url = urljoin(haber.federasyon_website.ana_url, src)
                            image_file = scraper.download_and_process_image(
                                full_url, haber.baslik
                            )
                            if image_file:
                                haber.resim.save(image_file.name, image_file, save=True)
                                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Federation default image failed for {haber.baslik}: {e}")
            return False

    def _extract_keywords(self, title):
        """Başlıktan anahtar kelimeleri çıkar"""
        keywords = ['karate', 'federasyon', 'şampiyon', 'müsabaka', 'antrenman']
        title_lower = title.lower()
        
        # Başlıktan spesifik kelimeleri bul
        found_keywords = []
        for word in title.split():
            if len(word) > 3 and word.lower() not in ['için', 'olan', 'ile', 'bir']:
                found_keywords.append(word.lower())
        
        return keywords + found_keywords

    def _is_relevant_image(self, src, keywords):
        """Resmin konuyla ilgili olup olmadığını kontrol et"""
        src_lower = src.lower()
        
        # Skip common non-content images
        skip_patterns = [
            'favicon', 'icon', 'logo', 'banner', 'advertisement',
            'social', 'share', 'pixel', 'tracking', 'spacer'
        ]
        
        for pattern in skip_patterns:
            if pattern in src_lower:
                return False
        
        # Check for relevant keywords
        relevant_keywords = ['karate', 'spor', 'federasyon', 'sporcu', 'antrenman', 'musabaka']
        for keyword in relevant_keywords:
            if keyword in src_lower:
                return True
        
        # Check file extensions
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        return any(ext in src_lower for ext in valid_extensions)