from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from haberler.models import FederasyonWebsite, Haber, BekleyenHaber
from haberler.services.news_scraper import NewsScrapingService
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Federasyon sitelerinde yeni haber olup olmadığını kontrol eder ve admin\'e bildirir'

    def add_arguments(self, parser):
        parser.add_argument(
            '--federation-id',
            type=int,
            help='Belirli bir federasyon ID\'si (boş bırakılırsa tüm federasyonlar kontrol edilir)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=3,
            help='Her federasyondan kontrol edilecek haber sayısı (varsayılan: 3)'
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Email göndermeden sadece konsola yaz'
        )

    def handle(self, *args, **options):
        federation_id = options['federation_id']
        limit = options['limit']
        no_email = options['no_email']
        
        self.stdout.write('🔍 YENİ HABERLERİ KONTROL EDİYOR')
        self.stdout.write('=' * 50)
        
        # Federasyonları belirle
        if federation_id:
            federations = FederasyonWebsite.objects.filter(id=federation_id, aktif=True)
        else:
            federations = FederasyonWebsite.objects.filter(aktif=True)
        
        if not federations.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  Kontrol edilecek federasyon bulunamadı')
            )
            return
        
        self.stdout.write(f'📊 Toplam {federations.count()} federasyon kontrol edilecek')
        
        # Yeni haberleri takip et
        new_news_found = []
        pending_news_created = []
        federations_with_new_news = []
        
        for federation in federations:
            self.stdout.write(f'\n🔄 {federation.ad} kontrol ediliyor...')
            
            try:
                # Özel işlemler için federasyon adına göre farklı yaklaşım
                if 'Boks' in federation.ad:
                    news_items = self._scrape_boxing_federation(federation, limit)
                else:
                    # Diğer federasyonlar için standart scraping
                    scraping_service = NewsScrapingService()
                    news_items = scraping_service.scrape_federation_news(federation)
                    if news_items:
                        news_items = news_items[:limit]
                
                if not news_items:
                    self.stdout.write(f'   ⚠️  {federation.ad} için haber bulunamadı')
                    continue
                
                new_count = 0
                for news_item in news_items:
                    # Haber zaten veritabanında var mı kontrol et
                    if Haber.objects.filter(kaynak_url=news_item['url']).exists():
                        continue
                        
                    if BekleyenHaber.objects.filter(kaynak_url=news_item['url']).exists():
                        self.stdout.write(f'   ⚠️  Beklemede: {news_item["title"][:50]}...')
                        continue
                        
                    # Başlık benzerliği kontrolü (%85 benzerlik filtresi)
                    if self.is_duplicate_title(news_item['title'], federation):
                        self.stdout.write(f'   ⏭️  Atlandı (benzer başlık): {news_item["title"][:50]}...')
                        continue
                        
                    # Get full content
                    full_content = scraping_service.get_news_content(news_item['url'])
                    if not full_content:
                        full_content = news_item['summary']
                        
                    # Extract image URL
                    image_urls = scraping_service.get_news_images(news_item['url'])
                    image_url = image_urls[0] if image_urls else None
                    
                    # Create pending news
                    pending_news = BekleyenHaber.objects.create(
                        baslik=news_item['title'],
                        ozet=news_item['summary'],
                        icerik=full_content,
                        kaynak_url=news_item['url'],
                        kaynak_resim_url=image_url,
                        federasyon_website=federation
                    )
                    
                    new_count += 1
                    pending_news_created.append(pending_news)
                    new_news_found.append({
                        'id': pending_news.id,
                        'federation': federation.ad,
                        'title': news_item['title'],
                        'url': news_item['url'],
                        'summary': news_item['summary'],
                        'image_url': image_url
                    })
                    self.stdout.write(f'   🆕 YENİ: {news_item["title"][:50]}...')
                
                if new_count > 0:
                    federations_with_new_news.append(federation)
                    self.stdout.write(f'   📢 {federation.ad}: {new_count} yeni haber beklemede')
                else:
                    self.stdout.write(f'   ✅ {federation.ad}: Yeni haber bulunamadı')
                
                # Update success status
                federation.hata_durumu = False
                federation.son_hata_mesaji = ""
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {federation.ad} hatası: {e}')
                )
                logger.error(f"Federation check error for {federation.ad}: {e}")
                
                # Update error status
                federation.hata_durumu = True
                federation.son_hata_mesaji = str(e)
        
        # Update the last check time for all federations
        for federation in federations:
            federation.son_tarama = datetime.now()
            # If this federation had new news, update the last new news time
            if federation in federations_with_new_news:
                federation.son_yeni_haber_zamani = datetime.now()
            federation.save()
        
        # Sonuçları bildir
        if new_news_found:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Toplam {len(new_news_found)} yeni haber bulundu ve bekleme listesine eklendi!'
                )
            )
            
            # Email gönder (eğer devre dışı bırakılmamışsa)
            if not no_email:
                self._send_notification_email(new_news_found)
            
            # Telegram bildirimleri gönder
            try:
                from haberler.services.notification_service import NotificationService
                notification_service = NotificationService()
                notification_service.send_new_news_notifications(new_news_found)
                self.stdout.write(self.style.SUCCESS("📢 Telegram bildirimleri başarıyla gönderildi."))
            except Exception as tg_err:
                self.stdout.write(self.style.WARNING(f"⚠️ Telegram bildirimleri gönderilemedi: {tg_err}"))
            
            # Detaylı bilgi göster
            for news in new_news_found:
                self.stdout.write(f'\n📰 {news["federation"]}')
                self.stdout.write(f'   Başlık: {news["title"]}')
                self.stdout.write(f'   URL: {news["url"]}')
                self.stdout.write(f'   Özet: {news["summary"][:100]}...')
        else:
            self.stdout.write(
                self.style.WARNING('\n✅ Yeni haber bulunamadı.')
            )

    def _scrape_boxing_federation(self, federation, limit):
        """Türkiye Boks Federasyonu için özel scraping"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # SSL doğrulamasını devre dışı bırak
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(federation.haberler_url, timeout=30, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # "Son Haberler" ve "Güncel Duyurular" bölümlerini bul
            sections = soup.find_all(['h2', 'h3'], string=re.compile(r'(Son Haberler|Güncel Duyurular)', re.IGNORECASE))
            
            news_items = []
            processed_urls = set()
            
            for section in sections:
                # Bölümün altındaki haberleri bul
                container = section.find_parent(['div', 'section', 'article'])
                if not container:
                    container = section.parent
                
                # Container içindeki tüm linkleri bul
                links = container.find_all('a', href=True) if container else []
                
                for link in links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    # Geçerli bir başlık ve URL kontrolü
                    if not title or len(title) < 5 or not href:
                        continue
                    
                    # Tam URL oluştur
                    full_url = urljoin(federation.ana_url, href)
                    
                    # Aynı URL'yi iki kez işlememek için
                    if full_url in processed_urls:
                        continue
                    processed_urls.add(full_url)
                    
                    # Özet metin al
                    summary = ""
                    parent = link.parent
                    if parent:
                        # Aynı parent içindeki diğer metinleri özet olarak kullan
                        siblings = parent.find_next_siblings()
                        for sibling in siblings[:2]:  # İlk 2 kardeş element
                            text = sibling.get_text(strip=True)
                            if text and len(text) > 20:
                                summary = text[:500]
                                break
                    
                    news_items.append({
                        'title': title[:200],
                        'url': full_url,
                        'summary': summary[:500] if summary else title[:500],
                    })
                    
                    if len(news_items) >= limit:
                        break
                
                if len(news_items) >= limit:
                    break
            
            return news_items
            
        except Exception as e:
            logger.error(f"Boxing federation scraping error: {e}")
            return []

    def _send_notification_email(self, new_news_list):
        """Admin'e email bildirimi gönder"""
        try:
            if not hasattr(settings, 'ADMIN_EMAIL') or not settings.ADMIN_EMAIL:
                self.stdout.write(
                    self.style.WARNING('⚠️  ADMIN_EMAIL ayarı bulunamadı, email gönderilemedi')
                )
                return
            
            # Email içeriğini hazırla
            subject = f'Yeni Spor Haberleri Beklemede - Toplam {len(new_news_list)}'
            
            message_lines = [
                'Merhaba Admin,',
                '',
                f'Sistem {len(new_news_list)} yeni spor haberi buldu ve onay için bekleme listesine ekledi:',
                ''
            ]
            
            for i, news in enumerate(new_news_list, 1):
                message_lines.extend([
                    f'{i}. {news["federation"]}',
                    f'   Başlık: {news["title"]}',
                    f'   URL: {news["url"]}',
                    f'   Özet: {news["summary"]}',
                    ''
                ])
            
            message_lines.extend([
                'Bu haberleri onaylamak için aşağıdaki adımları izleyin:',
                '1. Django admin paneline giriş yapın',
                '2. "Bekleyen Haberler" bölümüne gidin',
                '3. Haberleri inceleyin ve "Onayla" seçeneğini kullanın',
                ''
            ])
            
            message = '\n'.join(message_lines)
            
            # Email gönder
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS('📧 Admin\'e email bildirimi gönderildi')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'📧 Email gönderme hatası: {e}')
            )
            logger.error(f"Email sending error: {e}")

    def is_duplicate_title(self, title, federation):
        """Check if a similar news title exists in the database within this federation/category"""
        from difflib import SequenceMatcher
        from haberler.models import Kategori
        
        category = Kategori.objects.filter(federasyon_website=federation).first()
        if not category:
            return False
            
        recent_published = list(Haber.objects.filter(kategori=category).order_by('-olusturma_tarihi')[:30].values_list('baslik', flat=True))
        recent_pending = list(BekleyenHaber.objects.filter(federasyon_website=federation).order_by('-olusturma_tarihi')[:30].values_list('baslik', flat=True))
        
        for existing_title in recent_published + recent_pending:
            ratio = SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if ratio >= 0.85:
                return True
        return False