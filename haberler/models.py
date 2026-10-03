from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.utils.text import slugify
from django.core.files.base import ContentFile
from ckeditor.fields import RichTextField
import logging
import io
import hashlib
import textwrap
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class FederasyonWebsite(models.Model):
    ad = models.CharField(max_length=100)
    ana_url = models.URLField(validators=[URLValidator()])
    haberler_url = models.URLField(validators=[URLValidator()])
    aktif = models.BooleanField(default=True)
    son_tarama = models.DateTimeField(null=True, blank=True)
    son_yeni_haber_zamani = models.DateTimeField(null=True, blank=True, help_text="En son yeni haberin bulunduğu zaman")
    logo = models.ImageField(upload_to='federasyon_logolari/', blank=True, null=True, help_text="Federasyon logosu (haber resmi yoksa kullanılır)")
    
    # CSS selectors for scraping
    haber_listesi_selector = models.CharField(max_length=200, help_text="CSS selector for news list")
    haber_baslik_selector = models.CharField(max_length=200, help_text="CSS selector for news title")
    haber_link_selector = models.CharField(max_length=200, help_text="CSS selector for news link")
    haber_tarih_selector = models.CharField(max_length=200, blank=True, help_text="CSS selector for news date")
    haber_ozet_selector = models.CharField(max_length=200, blank=True, help_text="CSS selector for news summary")
    haber_resim_selector = models.CharField(max_length=200, blank=True, help_text="CSS selector for news detail image")
    
    son_hata_mesaji = models.TextField(blank=True, null=True, help_text="Son taramada alınan hata mesajı")
    hata_durumu = models.BooleanField(default=False, help_text="Son tarama hatalı bitti mi?")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    # Social Media URL fields (from migration 0032)
    facebook_url = models.URLField(blank=True, null=True, help_text="Facebook URL'si")
    instagram_url = models.URLField(blank=True, null=True, help_text="Instagram URL'si")
    x_url = models.URLField(blank=True, null=True, help_text="X / Twitter URL'si")
    youtube_url = models.URLField(blank=True, null=True, help_text="YouTube URL'si")
    
    class Meta:
        verbose_name_plural = "Federasyon Websiteleri"
    
    def __str__(self):
        return self.ad

class FederasyonSosyalMedya(models.Model):
    federasyon = models.OneToOneField(FederasyonWebsite, on_delete=models.CASCADE, related_name='sosyal_medya', verbose_name="Federasyon")
    instagram_kullanici_adi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Instagram Kullanıcı Adı")
    facebook_sayfasi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Facebook Sayfası/Kullanıcı Adı")
    x_sayfasi = models.CharField(max_length=100, blank=True, null=True, verbose_name="X / Twitter Kullanıcı Adı")

    class Meta:
        verbose_name = "Federasyon Sosyal Medya Hesabı"
        verbose_name_plural = "Federasyon Sosyal Medya Hesapları"

    def __str__(self):
        return f"{self.federasyon.ad} Sosyal Medya Hesapları"

class Kategori(models.Model):
    ad = models.CharField(max_length=100)
    slug = models.SlugField(max_length=1000, unique=True)
    aciklama = models.TextField(blank=True)
    federasyon_website = models.ForeignKey(FederasyonWebsite, on_delete=models.SET_NULL, null=True, blank=True)
    # --- YENİ EKLENECEK SATIR ---
    menude_goster = models.BooleanField(default=True, verbose_name="Menüde Göster")
    # ----------------------------

    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Kategoriler"
        ordering = ['ad']
    
    def __str__(self):
        return self.ad

class Haber(models.Model):
    baslik = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=1000, unique=True)
    ozet = models.TextField(max_length=500)
    icerik = RichTextField()
    resim = models.FileField(upload_to='haberler/', blank=True, null=True)
    @property
    def is_pdf(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.pdf'

    @property
    def is_svg(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.svg'

    @property
    def is_image(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.jfif', '.bmp', '.tiff', '.heic', '.heif']

    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE, related_name='haberler')
    yazar = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Scraping related fields
    kaynak_url = models.URLField(max_length=1000, blank=True, null=True, help_text="Original source URL")
    video_url = models.URLField(max_length=1000, blank=True, null=True, help_text="Video URL (Telegram CDN / Instagram)")
    is_video = models.BooleanField(default=False, help_text="Haber bir video mu?")
    federasyon_website = models.ForeignKey(FederasyonWebsite, on_delete=models.SET_NULL, null=True, blank=True)
    otomatik_eklendi = models.BooleanField(default=False, help_text="Was this news added automatically?")
    
    olusturma_tarihi = models.DateTimeField(default=timezone.now)
    haber_tarihi = models.DateTimeField(null=True, blank=True, help_text="Original news publication date")
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    yayinlandi = models.BooleanField(default=True)
    anasayfa_haberi = models.BooleanField(default=False)
    manset_haberi = models.BooleanField(default=False)
    manset_sabitlendi = models.BooleanField(default=False, help_text="📌 Manşette Sabitle (En üstte kalsın)")
    haber_degeri_skoru = models.IntegerField(default=0, blank=True, null=True, help_text="AI Haber Değeri Skoru (1-100)")
    kose_yazisi = models.BooleanField(default=False, help_text="Köşe yazısı mı?")
    goruntulenme_sayisi = models.PositiveIntegerField(default=0, help_text="Haberin görüntülenme sayısı")
    
    class Meta:
        ordering = ['-olusturma_tarihi']
        verbose_name_plural = "Haberler"
        constraints = [
            models.UniqueConstraint(
                fields=['kaynak_url'], 
                condition=models.Q(kaynak_url__isnull=False),
                name='unique_source_url'
            )
        ]
    
    def __str__(self):
        return self.baslik

class BekleyenYetkiliHaberi(models.Model):
    """Model for news items submitted by authorized users (yetkili) waiting for admin approval"""
    baslik = models.CharField(max_length=1000)
    ozet = models.TextField(max_length=500)
    icerik = models.TextField()
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE)
    yazar = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Yetkili kullanıcı")
    kose_yazisi = models.BooleanField(default=False, help_text="Köşe yazısı mı?")
    resim = models.FileField(upload_to='bekleyen_haberler/', blank=True, null=True)
    @property
    def is_pdf(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.pdf'

    @property
    def is_svg(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.svg'

    @property
    def is_image(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.jfif', '.bmp', '.tiff', '.heic', '.heif']

    olusturma_tarihi = models.DateTimeField(default=timezone.now)
    onaylandi = models.BooleanField(default=False)
    reddedildi = models.BooleanField(default=False)
    onay_tarihi = models.DateTimeField(null=True, blank=True)
    red_tarihi = models.DateTimeField(null=True, blank=True)
    onaylayan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='onaylanan_yetkili_haberleri')
    red_nedeni = models.TextField(blank=True, null=True, help_text="Reddedilme nedeni")
    
    class Meta:
        ordering = ['-olusturma_tarihi']
        verbose_name_plural = "Bekleyen Yetkili Haberleri"
    
    def __str__(self):
        status = 'Onaylandı' if self.onaylandi else 'Beklemede' if not self.reddedildi else 'Reddedildi'
        type_str = 'Köşe Yazısı' if self.kose_yazisi else 'Haber'
        return f"{self.baslik} ({type_str} - {status})"
    
    def approve(self, admin_user):
        """Approve yetkili news and create a Haber object"""
        from django.utils.text import slugify
        
        if self.onaylandi or self.reddedildi:
            raise ValueError("Bu haber zaten onaylanmış veya reddedilmiş")
        
        final_baslik = self.baslik
        final_ozet = self.ozet or self.baslik
        final_icerik = self.icerik or self.ozet or self.baslik

        # Generate unique slug from title
        base_slug = slugify(final_baslik)
        if not base_slug:
            base_slug = "haber"
        
        slug = base_slug
        counter = 1
        while Haber.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create the actual news item
        score = getattr(self, 'haber_degeri_skoru', 85)
        haber = Haber.objects.create(
            baslik=final_baslik,
            slug=slug,
            ozet=final_ozet,
            icerik=final_icerik,
            kategori=self.kategori,
            yazar=self.yazar,
            kose_yazisi=self.kose_yazisi,
            otomatik_eklendi=False,  # This is manually created by yetkili
            yayinlandi=True,
            haber_tarihi=self.olusturma_tarihi,
            olusturma_tarihi=timezone.now(),
            haber_degeri_skoru=score,
            manset_haberi=True
        )
        
        # Copy image if exists
        if self.resim:
            haber.resim = self.resim
            haber.save()
        
        # If no image was provided, create custom-designed category image (following user preferences)
        if not self.resim:
            try:
                # Use the enhanced comprehensive design system (respects user's design preferences)
                from apply_comprehensive_designs import create_comprehensive_category_default_image
                create_comprehensive_category_default_image(haber)
                logger.info(f"Enhanced category image created for: {haber.kategori.ad}")
            except Exception as custom_img_error:
                logger.error(f"Error creating custom image: {custom_img_error}")
        
        # Update pending news status
        self.onaylandi = True
        self.reddedildi = False
        self.onay_tarihi = timezone.now()
        self.onaylayan = admin_user
        self.save()
        
        return haber
    
    def reject(self, admin_user, reason=""):
        """Reject the pending yetkili news item"""
        if self.onaylandi or self.reddedildi:
            raise ValueError("Bu haber zaten onaylanmış veya reddedilmiş")
        
        self.onaylandi = False
        self.reddedildi = True
        self.red_tarihi = timezone.now()
        self.onaylayan = admin_user
        self.red_nedeni = reason
        self.save()


class BekleyenHaber(models.Model):
    """Model for news items waiting for admin approval"""
    baslik = models.CharField(max_length=1000)
    ozet = models.TextField(max_length=500)
    icerik = models.TextField()
    kaynak_url = models.URLField(max_length=1000, help_text="Original source URL")
    kaynak_resim_url = models.URLField(max_length=500, blank=True, null=True, help_text="Original news image URL")
    video_url = models.URLField(max_length=1000, blank=True, null=True, help_text="Video URL (Telegram CDN / Instagram)")
    is_video = models.BooleanField(default=False, help_text="Haber bir video mu?")
    resim = models.FileField(upload_to='bekleyen_haberler/', blank=True, null=True, help_text="Manüel yüklenen veya değiştirilen görsel")
    @property
    def is_pdf(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.pdf'

    @property
    def is_svg(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.svg'

    @property
    def is_image(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.jfif', '.bmp', '.tiff', '.heic', '.heif']

    federasyon_website = models.ForeignKey(FederasyonWebsite, on_delete=models.CASCADE)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, blank=True, help_text="Haberin ekleneceği kategori")
    olusturma_tarihi = models.DateTimeField(default=timezone.now)
    haber_tarihi = models.DateTimeField(null=True, blank=True, help_text="Original news publication date")
    onaylandi = models.BooleanField(default=False)
    reddedildi = models.BooleanField(default=False)
    onay_tarihi = models.DateTimeField(null=True, blank=True)
    red_tarihi = models.DateTimeField(null=True, blank=True)
    onaylayan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='onaylanan_haberler')
    
    # AI Özgünleştirme & Haber Stüdyosu Alanları
    ozgun_baslik = models.CharField(max_length=1000, blank=True, null=True, help_text="AI tarafından özgünleştirilmiş başlık")
    ozgun_ozet = models.TextField(blank=True, null=True, help_text="AI tarafından hazırlanan spot/özet")
    ozgun_icerik = models.TextField(blank=True, null=True, help_text="AI tarafından zenginleştirilmiş HTML içerik")
    haber_degeri_skoru = models.IntegerField(default=0, blank=True, null=True, help_text="AI Haber Değeri Skoru (1-100)")
    ai_analiz = models.TextField(blank=True, null=True, help_text="AI editoryal analiz ve değerlendirme notu")
    ai_durum = models.CharField(
        max_length=50, 
        default='ham', 
        choices=[('ham', 'Ham'), ('isleniyor', 'İşleniyor'), ('hazir', 'Özgün Taslak Hazır'), ('hata', 'Hata Oluştu')],
        help_text="AI işleme durumu"
    )
    
    class Meta:
        ordering = ['-olusturma_tarihi']
        verbose_name_plural = "Bekleyen Haberler"
    
    def __str__(self):
        return f"{self.baslik} ({'Onaylandı' if self.onaylandi else 'Beklemede' if not self.reddedildi else 'Reddedildi'})"
    
    def approve(self, admin_user):
        """Approve pending news and create a Haber object"""
        from django.utils.text import slugify
        
        if self.onaylandi or self.reddedildi:
            raise ValueError("Bu haber zaten onaylanmış veya reddedilmiş")
        
        # Title, summary and content: prefer AI rewritten version if available
        final_baslik = (self.ozgun_baslik.strip() if self.ozgun_baslik else None) or self.baslik
        final_ozet = (self.ozgun_ozet.strip() if self.ozgun_ozet else None) or self.ozet
        final_icerik = (self.ozgun_icerik.strip() if self.ozgun_icerik else None) or self.icerik

        # Generate unique slug from title
        base_slug = slugify(final_baslik)
        if not base_slug:
            base_slug = "haber"
        
        slug = base_slug
        counter = 1
        while Haber.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Get or create appropriate category for this federation
        kategori = self.kategori
        
        # If no category assigned to the pending news, check if federation has one
        if not kategori and self.federasyon_website and self.federasyon_website.kategori_set.exists():
            kategori = self.federasyon_website.kategori_set.first()
        
        # If still no category, create one for this federation
        if not kategori:
            kategori, created = Kategori.objects.get_or_create(
                slug=slugify(self.federasyon_website.ad),
                defaults={
                    'ad': self.federasyon_website.ad,
                    'aciklama': f'{self.federasyon_website.ad} haberleri',
                    'federasyon_website': self.federasyon_website
                }
            )
        
        # Get or create bot user for news creation
        bot_user, created = User.objects.get_or_create(
            username='newsbot',
            defaults={
                'email': 'newsbot@antnews.com',
                'first_name': 'News',
                'last_name': 'Bot',
                'is_active': True
            }
        )
        
        # Determine manset status based on AI news score (threshold: 80+)
        skor = self.haber_degeri_skoru or 0
        is_manset = (skor >= 80)

        # Create the actual news item
        haber = Haber.objects.create(
            baslik=final_baslik,
            slug=slug,
            ozet=final_ozet,
            icerik=final_icerik,
            kategori=kategori,
            yazar=bot_user,
            kaynak_url=self.kaynak_url,
            video_url=self.video_url,
            is_video=self.is_video,
            federasyon_website=self.federasyon_website,
            otomatik_eklendi=True,
            yayinlandi=True,
            anasayfa_haberi=True,
            manset_haberi=True,
            haber_degeri_skoru=skor,
            haber_tarihi=self.haber_tarihi or self.olusturma_tarihi,
            olusturma_tarihi=timezone.now()
        )
        
        # Try to download and attach image
        image_attached = False
        
        # 1. First choice: Manual image uploaded by admin
        if self.resim:
            try:
                haber.resim.save(self.resim.name, self.resim.file, save=True)
                image_attached = True
                logger.info(f"Manual image attached from BekleyenHaber: {self.resim.name}")
            except Exception as manual_img_err:
                logger.error(f"Error copying manual image: {manual_img_err}")
                
        # 2. Second choice: Download and fit original scraped image
        if not image_attached:
            try:
                from haberler.services.news_scraper import NewsScrapingService
                scraper = NewsScrapingService()
                
                # First, try our saved image URL, then fallback to scraping
                from urllib.parse import urljoin
                image_url = self.kaynak_resim_url
                if image_url:
                    image_url = image_url.strip()
                    if not image_url.startswith(('http://', 'https://', '/media/')) and self.kaynak_url:
                        image_url = urljoin(self.kaynak_url, image_url)
                else:
                    image_urls = scraper.get_news_images(self.kaynak_url)
                    if image_urls:
                        image_url = image_urls[0]
                
                if image_url:
                    # Download and fit (crop/resize) original image to 1200x675 (16:9)
                    image_file = scraper.download_and_process_image_fit(
                        image_url, self.baslik, target_size=(1200, 675)
                    )
                    if image_file:
                        haber.resim.save(image_file.name, image_file, save=True)
                        image_attached = True
                        logger.info(f"Original image attached and fitted from: {image_url}")
            except Exception as img_error:
                logger.error(f"Error fetching original image: {img_error}")
                
        # 3. Third choice: Federation Logo
        if not image_attached and self.federasyon_website and self.federasyon_website.logo:
            try:
                logo_file = self.federasyon_website.logo
                haber.resim.save(logo_file.name, logo_file.file, save=True)
                image_attached = True
                logger.info(f"Federation logo attached as news image: {logo_file.name}")
            except Exception as logo_err:
                logger.error(f"Error copying federation logo: {logo_err}")
        
        # If no image was attached, safely assign authentic official federation logo
        if not image_attached:
            try:
                if self.federasyon_website and self.federasyon_website.logo:
                    haber.resim = str(self.federasyon_website.logo)
                else:
                    haber.resim = 'federasyon_logolari/turkiye-karate-federasyonu.png'
                haber.save(update_fields=['resim'])
                logger.info(f"Official logo assigned as safe fallback image for: {haber.baslik}")
            except Exception as custom_img_error:
                logger.error(f"Error assigning fallback logo: {custom_img_error}")
        
        # Update pending news status
        self.onaylandi = True
        self.reddedildi = False
        self.onay_tarihi = timezone.now()
        self.onaylayan = admin_user
        self.save()
        
        return haber
    
    def _create_category_default_image(self, haber):
        """Create a custom-designed image for the category if no original image found"""

        
        # Category color themes
        category_themes = {
            'boks': {
                'primary': (220, 53, 69),    # Red
                'secondary': (255, 215, 0),  # Gold
                'icon': '🥊',  # Boxing glove
                'name': 'BOKS'
            },
            'karate': {
                'primary': (255, 87, 51),    # Orange
                'secondary': (255, 255, 255), # White
                'icon': '🥋',  # Karate uniform
                'name': 'KARATE'
            },
            'taekwondo': {
                'primary': (0, 123, 255),    # Blue
                'secondary': (255, 215, 0),  # Gold
                'icon': '🥋',  # Martial arts
                'name': 'TAEKWONDO'
            },
            'judo': {
                'primary': (255, 165, 0),    # Orange
                'secondary': (255, 255, 255), # White
                'icon': '🥋',  # Judo
                'name': 'JUDO'
            },
            'muaythai': {
                'primary': (220, 20, 60),    # Crimson
                'secondary': (255, 215, 0),  # Gold
                'icon': '🥊',  # Fighting
                'name': 'MUAY THAI'
            },
            'kickboks': {
                'primary': (142, 68, 173),   # Purple
                'secondary': (255, 215, 0),  # Gold
                'icon': '🥊',  # Kickboxing
                'name': 'KİCKBOKS'
            },
            'gures': {
                'primary': (25, 25, 112),    # Navy
                'secondary': (255, 215, 0),  # Gold
                'icon': '🤼',  # Wrestling
                'name': 'GÜREŞ'
            },
            'mma': {
                'primary': (128, 128, 128),  # Gray
                'secondary': (255, 69, 0),   # Red-Orange
                'icon': '🥊',  # MMA
                'name': 'MMA'
            },
            'wushu-kung-fu': {
                'primary': (255, 140, 0),    # Dark Orange
                'secondary': (139, 0, 0),    # Dark Red
                'icon': '🥋',  # Kung Fu
                'name': 'WUSHU KUNG FU'
            },
            'jiu-jitsu': {
                'primary': (72, 61, 139),    # Dark Slate Blue
                'secondary': (255, 255, 255), # White
                'icon': '🥋',  # Brazilian Jiu-Jitsu
                'name': 'JIU JITSU'
            }
        }
        
        # Get category theme or use default
        category_slug = haber.kategori.slug if haber.kategori else 'default'
        theme = category_themes.get(category_slug, {
            'primary': (25, 25, 112),      # Navy Blue
            'secondary': (255, 255, 255),  # White
            'icon': '🥋',            # Generic sports
            'name': haber.kategori.ad.upper() if haber.kategori else 'SPOR'
        })
        
        # Image dimensions
        width, height = 1200, 630
        
        # Create image with gradient background
        image = Image.new('RGB', (width, height), theme['primary'])
        draw = ImageDraw.Draw(image)
        
        # Create diagonal gradient effect
        for y in range(height):
            for x in range(0, width, 4):  # Skip pixels for performance
                # Calculate gradient position
                gradient_pos = (x + y) / (width + height)
                
                # Mix primary and darker version
                r = int(theme['primary'][0] * (1 - gradient_pos * 0.4))
                g = int(theme['primary'][1] * (1 - gradient_pos * 0.4))
                b = int(theme['primary'][2] * (1 - gradient_pos * 0.4))
                
                # Ensure colors stay within bounds
                r, g, b = max(0, r), max(0, g), max(0, b)
                
                draw.line([(x, y), (x + 3, y)], fill=(r, g, b))
        
        # Add decorative elements
        self._add_decorative_shapes(draw, width, height, theme)
        
        # Add category name
        self._add_category_text(draw, width, height, theme)
        
        # Add news title (if it fits)
        self._add_news_title(draw, width, height, haber.baslik, theme)
        
        # Add sport icon
        self._add_sport_icon(draw, width, height, theme)
        
        # Save image
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=90, optimize=True)
        output.seek(0)
        
        # Generate filename
        safe_title = slugify(haber.baslik)[:30]
        unique_id = hashlib.md5(f"{haber.id}_{haber.baslik}".encode()).hexdigest()[:8]
        filename = f"category_{category_slug}_{safe_title}_{unique_id}.jpg"
        
        # Save to news item
        haber.resim.save(filename, ContentFile(output.read()), save=True)
        
    def _add_decorative_shapes(self, draw, width, height, theme):
        """Add decorative geometric shapes"""
        try:
            # Add some geometric patterns
            primary = theme['primary']
            secondary = theme['secondary']
            
            # Create semi-transparent overlay color
            overlay_color = tuple(min(255, c + 30) for c in primary)
            
            # Add diagonal lines
            for i in range(0, width + height, 60):
                draw.line([(i, 0), (i - height, height)], fill=overlay_color, width=2)
            
            # Add corner accents
            corner_size = 100
            draw.polygon([(0, 0), (corner_size, 0), (0, corner_size)], fill=secondary)
            draw.polygon([(width - corner_size, height), (width, height), (width, height - corner_size)], fill=secondary)
            
        except Exception:
            pass  # Skip decorations if they fail
    
    def _add_category_text(self, draw, width, height, theme):
        """Add category name text"""
        try:
            # Try to load a font
            try:
                font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 48)
            except:
                try:
                    font = ImageFont.truetype('arial.ttf', 48)
                except:
                    font = ImageFont.load_default()
            
            text = theme['name']
            
            # Calculate text position (top center)
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(text) * 30  # Fallback estimate
            
            x = (width - text_width) // 2
            y = 80
            
            # Add text shadow
            draw.text((x + 3, y + 3), text, fill=(0, 0, 0, 128), font=font)
            # Add main text
            draw.text((x, y), text, fill=theme['secondary'], font=font)
            
        except Exception:
            pass  # Skip text if it fails
    
    def _add_news_title(self, draw, width, height, title, theme):
        """Add news title text (wrapped)"""
        try:
            # Try to load a smaller font for the title
            try:
                font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
            except:
                try:
                    font = ImageFont.truetype('arial.ttf', 24)
                except:
                    font = ImageFont.load_default()
            
            # Wrap the title text
            max_chars_per_line = 50
            wrapped_lines = textwrap.wrap(title, width=max_chars_per_line)
            
            # Limit to 3 lines
            if len(wrapped_lines) > 3:
                wrapped_lines = wrapped_lines[:3]
                wrapped_lines[2] = wrapped_lines[2][:47] + "..."
            
            # Calculate starting position (center bottom area)
            line_height = 35
            total_height = len(wrapped_lines) * line_height
            start_y = height - total_height - 100
            
            # Draw each line
            for i, line in enumerate(wrapped_lines):
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                except:
                    text_width = len(line) * 15  # Fallback estimate
                
                x = (width - text_width) // 2
                y = start_y + (i * line_height)
                
                # Add text shadow
                draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 180), font=font)
                # Add main text
                draw.text((x, y), line, fill=theme['secondary'], font=font)
                
        except Exception:
            pass  # Skip title if it fails
    
    def _add_sport_icon(self, draw, width, height, theme):
        """Add sport icon/emoji"""
        try:
            # Try to add emoji icon (may not work on all systems)
            try:
                icon_font = ImageFont.truetype('seguiemj.ttf', 80)
                icon = theme['icon']
                
                # Position in bottom right
                x = width - 150
                y = height - 150
                
                draw.text((x, y), icon, font=icon_font)
            except:
                # Fallback: draw a simple geometric shape
                x = width - 120
                y = height - 120
                size = 60
                
                # Draw a circle as fallback icon
                draw.ellipse([x, y, x + size, y + size], 
                           fill=theme['secondary'], 
                           outline=theme['primary'], 
                           width=4)
                
        except Exception:
            pass  # Skip icon if it fails
    
    def reject(self, admin_user):
        """Reject the pending news item"""
        if self.onaylandi or self.reddedildi:
            raise ValueError("Bu haber zaten onaylanmış veya reddedilmiş")
        
        self.onaylandi = False
        self.reddedildi = True
        self.red_tarihi = timezone.now()
        self.onaylayan = admin_user
        self.save()

    def _create_sequential_stock_image(self, haber):
        """Create a premium category cover image using sequential stock images with a dark overlay and title text"""
        from PIL import Image, ImageDraw, ImageFont, ImageOps
        from django.core.files.base import ContentFile
        from django.utils.text import slugify
        from django.conf import settings
        import io
        import os
        import hashlib
        import textwrap
        
        category_slug = haber.kategori.slug if haber.kategori else 'default'
        
        # Check stock images folder: media/stock_images/<category_slug>/
        media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')
        stock_dir = os.path.join(media_root, 'stock_images', category_slug)
        
        # Count published Haber objects in this category that have stock image filenames
        stock_news_count = Haber.objects.filter(
            kategori=haber.kategori,
            otomatik_eklendi=True,
            resim__contains="stock_fit_"
        ).count()
        
        # Determine image index (1 to 10) dynamically
        image_num = (stock_news_count % 10) + 1
        stock_img_name = f"{image_num}.jpg"
        stock_img_path = os.path.join(stock_dir, stock_img_name)
        
        # Check if the file exists, if not try .png or fallback to any file in directory
        if not os.path.exists(stock_img_path):
            png_path = os.path.join(stock_dir, f"{image_num}.png")
            if os.path.exists(png_path):
                stock_img_path = png_path
            elif os.path.exists(stock_dir):
                files = [f for f in os.listdir(stock_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if files:
                    stock_img_path = os.path.join(stock_dir, files[stock_news_count % len(files)])
        
        # Load the base image
        try:
            if os.path.exists(stock_img_path):
                base_image = Image.open(stock_img_path)
            else:
                # Color theme fallback if no stock image found
                colors = {
                    'boks': (220, 53, 69),
                    'karate': (255, 87, 51),
                    'taekwondo': (0, 123, 255),
                    'judo': (255, 165, 0),
                    'muaythai': (220, 20, 60),
                    'kickboks': (142, 68, 173),
                    'gures': (25, 25, 112),
                    'mma': (128, 128, 128),
                }
                bg_color = colors.get(category_slug, (25, 25, 112))
                base_image = Image.new('RGB', (1200, 675), bg_color)
        except Exception:
            base_image = Image.new('RGB', (1200, 675), (25, 25, 112))
            
        # Fit to 1200x675 (16:9) aspect ratio without distortion
        base_image = ImageOps.fit(base_image, (1200, 675), method=Image.Resampling.LANCZOS)
        
        # Apply dark overlay
        overlay = Image.new('RGBA', (1200, 675), (0, 0, 0, 160)) # 160/255 opacity
        combined = Image.alpha_composite(base_image.convert('RGBA'), overlay)
        
        # Draw category name and wrapped news title
        draw = ImageDraw.Draw(combined)
        font_path = "C:/Windows/Fonts/arial.ttf"
        try:
            font_title = ImageFont.truetype(font_path, 46)
            font_cat = ImageFont.truetype(font_path, 30)
        except Exception:
            font_title = ImageFont.load_default()
            font_cat = ImageFont.load_default()
            
        category_name = haber.kategori.ad.upper() if haber.kategori else "SPOR"
        draw.text((80, 80), category_name, fill=(255, 255, 255), font=font_cat)
        
        # Wrap title text
        wrapped_lines = textwrap.wrap(haber.baslik, width=45)
        y_text = 200
        for line in wrapped_lines[:4]:
            draw.text((80, y_text), line, fill=(255, 255, 255), font=font_title)
            y_text += 70
            
        # Save processed image
        output = io.BytesIO()
        combined.convert('RGB').save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        safe_title = slugify(haber.baslik)[:30]
        unique_id = hashlib.md5(f"{haber.id}_{haber.baslik}".encode()).hexdigest()[:8]
        filename = f"stock_fit_{category_slug}_{safe_title}_{unique_id}.jpg"
        
        # Save to news item
        haber.resim.save(filename, ContentFile(output.read()), save=True)

class Yorum(models.Model):
    haber = models.ForeignKey(Haber, on_delete=models.CASCADE, related_name='yorumlar')
    yazar = models.ForeignKey(User, on_delete=models.CASCADE)
    icerik = models.TextField()
    olusturma_tarihi = models.DateTimeField(default=timezone.now)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    onaylandi = models.BooleanField(default=True)
    ust_yorum = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='alt_yorumlar')
    
    class Meta:
        ordering = ['-olusturma_tarihi']
        verbose_name_plural = "Yorumlar"
    
    def __str__(self):
        return f"{self.yazar.username} - {self.haber.baslik}"
    
    @property
    def is_reply(self):
        return self.ust_yorum is not None

class Favori(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    haber = models.ForeignKey(Haber, on_delete=models.CASCADE)
    olusturma_tarihi = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('kullanici', 'haber')
        ordering = ['-olusturma_tarihi']
        verbose_name_plural = "Favoriler"
    
    def __str__(self):
        return f'{self.kullanici.username} - {self.haber.baslik}'

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('yetkili', 'Yetkili'),
        ('abone', 'Abone'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='abone')
    bio = models.TextField(blank=True, max_length=500, verbose_name="Biyografi")
    location = models.CharField(blank=True, max_length=30, verbose_name="Konum")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Doğum Tarihi")
    
    # Fields from migration 0031
    can_add_column = models.BooleanField(default=True, verbose_name="Köşe Yazısı Yazma Yetkisi")
    can_add_news = models.BooleanField(default=True, verbose_name="Haber Ekleme Yetkisi")
    can_edit_news = models.BooleanField(default=True, verbose_name="Kendi Haberlerini Düzenleme Yetkisi")
    can_manage_comments = models.BooleanField(default=True, verbose_name="Yorum Yönetimi Yetkisi")
    profil_resmi = models.ImageField(upload_to='profil_resimleri/', blank=True, null=True, verbose_name="Profil Fotoğrafı")
    anasayfa_yazari = models.BooleanField(default=False, verbose_name="Ana Sayfa Yazar Slider'ında Göster")
    
    def __str__(self):
        return f'{self.user.username} - {self.get_user_type_display()}'

class KoseYazari(UserProfile):
    class Meta:
        proxy = True
        verbose_name = "Köşe Yazarı"
        verbose_name_plural = "Köşe Yazarları"

class BultenAbone(models.Model):
    eposta = models.EmailField(unique=True, verbose_name="E-posta")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    kullanici_adi = models.CharField(max_length=150, blank=True, null=True, verbose_name="Kullanıcı Adı")
    isim = models.CharField(max_length=100, blank=True, null=True, verbose_name="İsim")
    soyisim = models.CharField(max_length=100, blank=True, null=True, verbose_name="Soyisim")
    kayit_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")

    class Meta:
        verbose_name = "Bülten Abonesi"
        verbose_name_plural = "Bülten Aboneleri"
        ordering = ['-kayit_tarihi']

    def __str__(self):
        return f"{self.isim or ''} {self.soyisim or ''} ({self.eposta})"

class Reklam(models.Model):
    REKLAM_TİPİ_CHOICES = [
        ('bik_ihale', 'BİK Resmi İhale İlanı'),
        ('bik_duyuru', 'BİK Resmi Duyuru İlanı'),
        ('google_adsense', 'Google AdSense (JS Kodu)'),
        ('google_analytics', 'Google Analytics (JS Kodu)'),
        ('custom_banner', 'Özel Afiş/Görsel Reklam'),
        ('video_file', 'Video Dosyası (MP4/WebM)'),
        ('youtube_loop', 'YouTube Video Döngüsü (Muted/Autoplay)'),
        ('iframe_page', 'Dış Web Sayfası (Iframe)'),
    ]
    
    KONUM_CHOICES = [
        ('manset_4', 'Manşet Slider - 4. Sıra'),
        ('manset_8', 'Manşet Slider - 8. Sıra'),
        ('manset_12', 'Manşet Slider - 12. Sıra'),
        ('grid_5', 'Haber Izgarası - 5. Sıra'),
        ('grid_10', 'Haber Izgarası - 10. Sıra'),
        ('grid_15', 'Haber Izgarası - 15. Sıra'),
        ('grid_20', 'Haber Izgarası - 20. Sıra'),
        ('global_head', 'Global - HTML Head İçi'),
        ('global_body', 'Global - HTML Body Sonu'),
        ('header_ad', 'Header - Logo Yanı Reklamı'),
    ]

    sira_no = models.IntegerField(default=1, verbose_name="Reklam Numarası / Sıra No")
    baslik = models.CharField(max_length=200, verbose_name="Reklam Başlığı")
    reklam_tipi = models.CharField(max_length=30, choices=REKLAM_TİPİ_CHOICES, verbose_name="Reklam Tipi")
    konum = models.CharField(max_length=30, choices=KONUM_CHOICES, verbose_name="Reklam Konumu")
    resim = models.FileField(upload_to='promosyonlar/', blank=True, null=True, verbose_name="Afiş/Görsel")
    video = models.FileField(upload_to='promosyonlar/videolar/', blank=True, null=True, verbose_name="Video Dosyası", help_text="Sadece .mp4, .webm formatları desteklenir. Otomatik döngü ve sessiz oynatılır.")
    youtube_url = models.URLField(blank=True, null=True, verbose_name="YouTube Video Linki", help_text="Örnek: https://www.youtube.com/watch?v=VIDEO_ID")
    iframe_url = models.URLField(blank=True, null=True, verbose_name="Dış Web Sayfası URL", help_text="İframe içinde gösterilecek dış web sayfası adresi. Örnek: https://aysunkezbanant.com/")
    
    @property
    def is_pdf(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.pdf'

    @property
    def is_svg(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.svg'

    @property
    def is_image(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.jfif', '.bmp', '.tiff', '.heic', '.heif']

    @property
    def is_video(self):
        import os
        if not self.video:
            return False
        ext = os.path.splitext(self.video.name)[1].lower()
        return ext in ['.mp4', '.webm', '.ogg']

    @property
    def youtube_id(self):
        import urllib.parse as urlparse
        if not self.youtube_url:
            return ""
        parsed = urlparse.urlparse(self.youtube_url)
        if parsed.hostname == 'youtu.be':
            return parsed.path[1:]
        if parsed.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed.path == '/watch':
                p = urlparse.parse_qs(parsed.query)
                return p.get('v', [''])[0]
            if parsed.path.startswith(('/embed/', '/v/')):
                return parsed.path.split('/')[2]
        return ""

    hedef_url = models.URLField(blank=True, null=True, verbose_name="Hedef URL Linki")
    detaylar = models.TextField(blank=True, null=True, verbose_name="Reklam Detayları (BİK İlan Bilgileri vb.)")
    kod = models.TextField(blank=True, null=True, verbose_name="AdSense/Analytics JS Kodu")
    aktif = models.BooleanField(default=True, verbose_name="Aktif mi?")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reklam"
        verbose_name_plural = "Reklamlar"
        ordering = ['sira_no']

    def __str__(self):
        return f"{self.sira_no} - {self.baslik} ({self.get_konum_display()})"

class BekleyenSosyalMedyaHaberi(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram 📸'),
        ('twitter', 'X / Twitter 🐦'),
        ('facebook', 'Facebook 👥'),
        ('youtube', 'YouTube 🎥'),
    ]
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, verbose_name="Platform")
    federasyon_website = models.ForeignKey(FederasyonWebsite, on_delete=models.CASCADE, verbose_name="Federasyon")
    paylasim_id = models.CharField(max_length=100, unique=True, verbose_name="Gönderi Benzersiz ID")
    baslik = models.CharField(max_length=200, verbose_name="Başlık / Özet")
    icerik = models.TextField(verbose_name="Gönderi Metni İçeriği")
    kaynak_url = models.URLField(max_length=500, verbose_name="Gönderi Bağlantısı (URL)")
    kaynak_resim_url = models.URLField(max_length=600, blank=True, null=True, verbose_name="Orijinal Resim URL")
    resim = models.FileField(upload_to='bekleyen_sosyal_medya/', blank=True, null=True, verbose_name="Yerel Görsel")
    @property
    def is_pdf(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.pdf'

    @property
    def is_svg(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext == '.svg'

    @property
    def is_image(self):
        import os
        if not self.resim:
            return False
        ext = os.path.splitext(self.resim.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.jfif', '.bmp', '.tiff', '.heic', '.heif']

    gonderi_tipi = models.CharField(
        max_length=20,
        choices=[('post', 'Fotoğraf/Gönderi 🖼️'), ('reel', 'Reel Video 🎥'), ('story', 'Hikaye/Story ⏳')],
        default='post',
        verbose_name="Gönderi Tipi"
    )
    paylasim_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Paylaşım Tarihi")
    
    onaylandi = models.BooleanField(default=False, verbose_name="Onaylandı mı?")
    reddedildi = models.BooleanField(default=False, verbose_name="Reddedildi mi?")
    onay_tarihi = models.DateTimeField(null=True, blank=True)
    onaylayan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='onaylanan_sosyal_gonderiler')

    class Meta:
        verbose_name = "Bekleyen Sosyal Medya Haberi"
        verbose_name_plural = "Bekleyen Sosyal Medya Haberleri"
        ordering = ['-paylasim_tarihi']

    def __str__(self):
        return f"[{self.get_platform_display()}] {self.federasyon_website.ad} - {self.baslik[:30]}"
        
    def approve(self, admin_user):
        """Approve pending social media news and create a Haber object"""
        from django.utils.text import slugify
        
        if self.onaylandi or self.reddedildi:
            raise ValueError("Bu haber zaten onaylanmış veya reddedilmiş")
        
        # Generate unique slug from title
        base_slug = slugify(self.baslik)
        if not base_slug:
            base_slug = "sosyal-medya-haberi"
        
        slug = base_slug
        counter = 1
        while Haber.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Get or create category
        kategori = None
        if self.federasyon_website and self.federasyon_website.kategori_set.exists():
            kategori = self.federasyon_website.kategori_set.first()
        
        if not kategori:
            kategori, created = Kategori.objects.get_or_create(
                slug=slugify(self.federasyon_website.ad),
                defaults={
                    'ad': self.federasyon_website.ad,
                    'aciklama': f'{self.federasyon_website.ad} haberleri',
                    'federasyon_website': self.federasyon_website
                }
            )
        
        # Get or create social bot user
        bot_user, created = User.objects.get_or_create(
            username='socialbot',
            defaults={
                'email': 'socialbot@antnews.com',
                'first_name': 'Sosyal Medya',
                'last_name': 'Bot',
                'is_active': True
            }
        )
        # Create profile if not exists
        UserProfile.objects.get_or_create(user=bot_user, defaults={'user_type': 'yetkili'})
        
        # Parse media URLs from hidden comment
        import re
        media_urls = []
        cleaned_content = self.icerik
        comment_match = re.search(r'<!--MEDIA_URLS:\[(.*?)\]-->', self.icerik)
        if comment_match:
            media_urls = [x.strip() for x in comment_match.group(1).split(',') if x.strip()]
            cleaned_content = re.sub(r'<!--MEDIA_URLS:\[.*?\]-->', '', self.icerik).strip()
            
        # Append HTML video player or gallery of multiple media elements
        gallery_html = ''
        if media_urls:
            has_video = any(".mp4" in m.lower() or "video" in m.lower() for m in media_urls)
            if len(media_urls) > 1 or has_video:
                gallery_html = '\n<br><hr><br>\n<div class="news-media-gallery" style="margin-top: 25px; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px;">'
                for idx, m_url in enumerate(media_urls):
                    is_vid = ".mp4" in m_url.lower() or "video" in m_url.lower()
                    if is_vid:
                        gallery_html += f'''
                            <div class="gallery-item video-item" style="border-radius: 8px; overflow: hidden; background: #000; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 10px;">
                                <video controls style="width: 100%; height: auto; display: block; max-height: 480px; margin: 0 auto;">
                                    <source src="{m_url}" type="video/mp4">
                                    Tarayıcınız video oynatmayı desteklemiyor.
                                </video>
                            </div>
                        '''
                    else:
                        gallery_html += f'''
                            <div class="gallery-item image-item" style="border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 10px;">
                                <img src="{m_url}" alt="Sosyal Medya Görseli {idx+1}" style="width: 100%; height: auto; display: block; object-fit: cover; max-height: 480px; margin: 0 auto;">
                            </div>
                        '''
                gallery_html += '</div>'
                cleaned_content += gallery_html

        # Create the actual news item
        haber = Haber.objects.create(
            baslik=self.baslik,
            slug=slug,
            ozet=cleaned_content[:200] + ('...' if len(cleaned_content) > 200 else ''),
            icerik=cleaned_content,
            kategori=kategori,
            yazar=bot_user,
            kaynak_url=self.kaynak_url,
            federasyon_website=self.federasyon_website,
            otomatik_eklendi=True,
            yayinlandi=True,
            haber_tarihi=self.paylasim_tarihi or self.olusturma_tarihi,
            olusturma_tarihi=timezone.now()
        )
        
        image_attached = False
        
        # 1. Manual image uploaded by admin
        if self.resim:
            try:
                haber.resim.save(self.resim.name, self.resim.file, save=True)
                image_attached = True
            except Exception as e:
                logger.error(f"Error copying manual image: {e}")
                
        # 2. Scraped image URL (Supports remote http/https AND local /media/ paths)
        if not image_attached and self.kaynak_resim_url:
            raw_url = self.kaynak_resim_url.strip()
            if raw_url.startswith('http://') or raw_url.startswith('https://'):
                try:
                    from haberler.services.news_scraper import NewsScrapingService
                    scraper = NewsScrapingService()
                    image_file = scraper.download_and_process_image_fit(
                        raw_url, self.baslik, target_size=(1200, 675)
                    )
                    if image_file:
                        haber.resim.save(image_file.name, image_file, save=True)
                        image_attached = True
                except Exception as e:
                    logger.error(f"Error downloading social media image: {e}")
            elif raw_url.startswith('/media/') or raw_url.startswith('media/'):
                try:
                    from PIL import Image, ImageOps
                    import io, os, hashlib
                    from django.conf import settings
                    from django.core.files.base import ContentFile
                    from django.utils.text import slugify

                    clean_rel = raw_url
                    if clean_rel.startswith('/media/'):
                        clean_rel = clean_rel[len('/media/'):]
                    elif clean_rel.startswith('media/'):
                        clean_rel = clean_rel[len('media/'):]
                    media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')
                    abs_path = os.path.join(media_root, clean_rel)
                    
                    if os.path.exists(abs_path):
                        with Image.open(abs_path) as img:
                            fitted = ImageOps.fit(img.convert('RGB'), (1200, 675), method=Image.Resampling.LANCZOS)
                            buf = io.BytesIO()
                            fitted.save(buf, format='JPEG', quality=88, optimize=True)
                            buf.seek(0)
                            unique_id = hashlib.md5(f"{self.id}_{self.baslik}".encode()).hexdigest()[:8]
                            filename = f"social_{slugify(self.baslik)[:30]}_{unique_id}.jpg"
                            haber.resim.save(filename, ContentFile(buf.read()), save=True)
                            image_attached = True
                except Exception as e:
                    logger.error(f"Error copying local media image: {e}")
                
        # 3. Federation Logo
        if not image_attached and self.federasyon_website and self.federasyon_website.logo:
            try:
                logo_file = self.federasyon_website.logo
                haber.resim.save(logo_file.name, logo_file.file, save=True)
                image_attached = True
            except Exception as logo_err:
                logger.error(f"Error copying federation logo: {logo_err}")
                
        # 4. Stock Category Image Fallback
        if not image_attached:
            try:
                stock_news_count = Haber.objects.filter(
                    kategori=haber.kategori,
                    otomatik_eklendi=True,
                    resim__contains="stock_fit_"
                ).count()
                
                from PIL import Image, ImageOps, ImageDraw, ImageFont
                import io, os, hashlib, textwrap
                from django.conf import settings
                from django.core.files.base import ContentFile
                
                category_slug = haber.kategori.slug
                media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')
                stock_dir = os.path.join(media_root, 'stock_images', category_slug)
                image_num = (stock_news_count % 10) + 1
                stock_img_path = os.path.join(stock_dir, f"{image_num}.jpg")
                
                if os.path.exists(stock_img_path):
                    base_image = Image.open(stock_img_path)
                else:
                    # Fallback to genel folder if category folder is missing
                    genel_img_path = os.path.join(media_root, 'stock_images', 'genel', f"{image_num}.jpg")
                    if os.path.exists(genel_img_path):
                        base_image = Image.open(genel_img_path)
                    else:
                        base_image = Image.new('RGB', (1200, 675), (20, 35, 60))
                    
                base_image = ImageOps.fit(base_image, (1200, 675), method=Image.Resampling.LANCZOS)
                
                overlay = Image.new('RGBA', (1200, 675), (0, 0, 0, 140))
                combined = Image.alpha_composite(base_image.convert('RGBA'), overlay)
                draw = ImageDraw.Draw(combined)
                
                # Robust multi-platform font resolution
                font_paths = [
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "C:/Windows/Fonts/arial.ttf"
                ]
                font_path = None
                for fp in font_paths:
                    if os.path.exists(fp):
                        font_path = fp
                        break
                
                try:
                    if font_path:
                        font_title = ImageFont.truetype(font_path, 44)
                        font_cat = ImageFont.truetype(font_path, 28)
                    else:
                        font_title = ImageFont.load_default()
                        font_cat = ImageFont.load_default()
                except Exception:
                    font_title = ImageFont.load_default()
                    font_cat = ImageFont.load_default()
                    
                draw.text((80, 80), haber.kategori.ad.upper(), fill=(255, 255, 255), font=font_cat)
                wrapped_lines = textwrap.wrap(haber.baslik, width=45)
                y_text = 200
                for line in wrapped_lines[:4]:
                    draw.text((80, y_text), line, fill=(255, 255, 255), font=font_title)
                    y_text += 65
                    
                output = io.BytesIO()
                combined.convert('RGB').save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                unique_id = hashlib.md5(f"{haber.id}_{haber.baslik}".encode()).hexdigest()[:8]
                filename = f"stock_fit_{category_slug}_{slugify(haber.baslik)[:30]}_{unique_id}.jpg"
                haber.resim.save(filename, ContentFile(output.read()), save=True)
                image_attached = True
            except Exception as e:
                logger.error(f"Error creating stock image fallback: {e}")
        
        # Update pending state
        self.onaylandi = True
        self.reddedildi = False
        self.onay_tarihi = timezone.now()
        self.onaylayan = admin_user
        self.save()
        return haber

    def reject(self, admin_user):
        """Reject the pending social media news item"""
        if self.onaylandi or self.reddedildi:
            raise ValueError("Bu haber zaten onaylanmış veya reddedilmiş")
        
        self.onaylandi = False
        self.reddedildi = True
        self.onay_tarihi = timezone.now()
        self.onaylayan = admin_user
        self.save()

# --- Karate Veri Modelleri ---

class KarateSehir(models.Model):
    ad = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.ad
    
    class Meta:
        verbose_name = "Karate Şehri"
        verbose_name_plural = "Karate Şehirleri"

class KarateKulup(models.Model):
    ad = models.CharField(max_length=255, verbose_name="Kulüp Adı")
    sehir = models.ForeignKey(KarateSehir, on_delete=models.CASCADE, related_name="kulupler")
    yetkili = models.CharField(max_length=150, blank=True, null=True, verbose_name="Kulüp Yetkilisi")
    
    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = "Karate Kulübü"
        verbose_name_plural = "Karate Kulüpleri"

class KarateAntrenor(models.Model):
    ad_soyad = models.CharField(max_length=150, verbose_name="Ad Soyad")
    kademe = models.CharField(max_length=100, blank=True, null=True, verbose_name="Antrenörlük Kademesi")
    kulup = models.CharField(max_length=255, blank=True, null=True, verbose_name="Bağlı Olduğu Kulüp")
    sehir = models.ForeignKey(KarateSehir, on_delete=models.CASCADE, related_name="antrenorler")

    class Meta:
        verbose_name = "Karate Antrenörü"
        verbose_name_plural = "Karate Antrenörleri"

    def __str__(self):
        return self.ad_soyad


class Sporcu(models.Model):
    GENDER_CHOICES = [
        ('Erkek', 'Erkek'),
        ('Kadın', 'Kadın'),
    ]
    tc = models.CharField(max_length=11, unique=True, verbose_name="TC Kimlik No")
    ad_soyad = models.CharField(max_length=255, verbose_name="Adı Soyadı")
    cinsiyet = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="Cinsiyeti")
    uyruk = models.CharField(max_length=50, default="T.C.", verbose_name="Uyruğu")
    dogum_tarihi = models.CharField(max_length=50, blank=True, null=True, verbose_name="Doğum Tarihi")
    baba_adi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Baba Adı")
    anne_adi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Anne Adı")
    cep_telefonu = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cep Telefonu")
    yedek_telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Diğer Tel No")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail Adresi")
    adres = models.TextField(blank=True, null=True, verbose_name="Posta Adresi")
    il_ilce = models.CharField(max_length=100, blank=True, null=True, verbose_name="Adres İl/İlçe")
    kulup = models.CharField(max_length=255, blank=True, null=True, verbose_name="Kulübü")
    lisans_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="Lisans No")
    sicil_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sicil No")
    lisans_vize_yili = models.CharField(max_length=4, blank=True, null=True, verbose_name="Lisans Vize Yılı")
    kemer = models.CharField(max_length=50, blank=True, null=True, verbose_name="Mevcut Kuşağı")
    sonraki_kemer = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sonraki Kemer Hedefi")
    fotograf = models.ImageField(upload_to='sporcu_fotolari/', blank=True, null=True, verbose_name="Sporcu Fotoğrafı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Notlar / Durum")
    is_web_kayit = models.BooleanField(default=False, verbose_name="Yeni Kayıt (Web)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    antrenor = models.ForeignKey(KarateAntrenor, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Antrenörü")

    class Meta:
        verbose_name = "Sporcu"
        verbose_name_plural = "Sporcular"

    def __str__(self):
        return f"{self.ad_soyad} - {self.tc}"


class KusakSinavBasvuru(models.Model):
    STATUS_CHOICES = [
        ('bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'),
    ]
    sporcu = models.ForeignKey(Sporcu, on_delete=models.CASCADE, related_name="sinav_basvurulari", verbose_name="Sporcu")
    mevcut_kemer = models.CharField(max_length=50, verbose_name="Mevcut Kemer")
    talep_edilen_kemer = models.CharField(max_length=50, verbose_name="Talep Edilen Kemer")
    dekont = models.FileField(upload_to='dekontlar/', blank=True, null=True, verbose_name="Sınav Dekontu")
    ucret_odendi = models.BooleanField(default=False, verbose_name="Ücret Yatırıldı mı?")
    notlar = models.TextField(blank=True, null=True, verbose_name="Sporcu Notu")
    durum = models.CharField(max_length=20, choices=STATUS_CHOICES, default='bekliyor', verbose_name="Başvuru Durumu")
    basvuru_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Başvuru Tarihi")
    onay_tarihi = models.DateTimeField(blank=True, null=True, verbose_name="Onaylanma Tarihi")

    class Meta:
        verbose_name = "Kuşak Sınav Başvurusu"
        verbose_name_plural = "Kuşak Sınav Başvuruları"
        ordering = ['-basvuru_tarihi']

    def __str__(self):
        return f"{self.sporcu.ad_soyad} - {self.talep_edilen_kemer} Sınavı"


class Kunye(models.Model):
    imtiyaz_sahibi = models.CharField(max_length=200, blank=True, verbose_name="İmtiyaz Sahibi (Yayın Sahibi)")
    sorumlu_yazi_isleri_muduru = models.CharField(max_length=200, blank=True, verbose_name="Sorumlu Yazı İşleri Müdürü")
    editorler = models.TextField(blank=True, verbose_name="Editörler", help_text="Her satıra bir isim gelecek şekilde yazın")
    web_tasarim_bilgi = models.CharField(max_length=200, blank=True, verbose_name="Web Tasarım ve Barındırma")
    adres = models.TextField(blank=True, verbose_name="Yönetim Yeri / Adres")
    telefon = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    eposta = models.CharField(max_length=100, blank=True, verbose_name="E-posta")
    yer_saglayici = models.CharField(max_length=200, blank=True, verbose_name="Yer Sağlayıcı")
    ticari_unvan = models.CharField(max_length=200, blank=True, verbose_name="Ticari Unvan")
    tuzel_kisi_temsilcisi = models.CharField(max_length=200, blank=True, verbose_name="Tüzel Kişi Temsilcisi")
    uets = models.CharField(max_length=200, blank=True, verbose_name="UETS Adresi")
    yayinci = models.CharField(max_length=200, blank=True, verbose_name="Yayıncı")

    class Meta:
        verbose_name = "Künye"
        verbose_name_plural = "Künyeler"

    def __str__(self):
        return "Künye Bilgileri"


class TaramaLog(models.Model):
    TARAMA_DURUM_CHOICES = [
        ('basarili', 'Başarılı'),
        ('hata', 'Hata'),
    ]
    federasyon_website = models.ForeignKey(FederasyonWebsite, on_delete=models.CASCADE, related_name='tarama_loglari')
    tarama_zamani = models.DateTimeField(auto_now_add=True)
    durum = models.CharField(max_length=20, choices=TARAMA_DURUM_CHOICES, verbose_name="Tarama Durumu")
    eklenen_sayi = models.IntegerField(default=0, verbose_name="Eklenen Haber Sayısı")
    mesaj = models.TextField(blank=True, null=True, verbose_name="Açıklama / Mesaj")

    class Meta:
        verbose_name = 'Tarama Logu'
        verbose_name_plural = 'Tarama Logları'
        ordering = ['-tarama_zamani']

    def __str__(self):
        return f"{self.federasyon_website.ad} - {self.tarama_zamani.strftime('%d.%m.%Y %H:%M')} ({self.durum})"


class Ad(models.Model):
    REKLAM_KONUMU_CHOICES = [
        ('slider_1', 'Slider 1. Kare'),
        ('slider_2', 'Slider 2. Kare'),
        ('slider_3', 'Slider 3. Kare'),
        ('slider_4', 'Slider 4. Kare'),
        ('slider_5', 'Slider 5. Kare'),
        ('slider_6', 'Slider 6. Kare'),
        ('slider_7', 'Slider 7. Kare'),
        ('slider_8', 'Slider 8. Kare'),
        ('slider_9', 'Slider 9. Kare'),
        ('slider_10', 'Slider 10. Kare'),
        ('kart_1', 'Haber Kartı 1. Kart'),
        ('kart_2', 'Haber Kartı 2. Kart'),
        ('kart_3', 'Haber Kartı 3. Kart'),
        ('kart_4', 'Haber Kartı 4. Kart'),
        ('kart_5', 'Haber Kartı 5. Kart'),
        ('kart_6', 'Haber Kartı 6. Kart'),
        ('kart_7', 'Haber Kartı 7. Kart'),
        ('kart_8', 'Haber Kartı 8. Kart'),
        ('kart_9', 'Haber Kartı 9. Kart'),
        ('kart_10', 'Haber Kartı 10. Kart'),
        ('kart_11', 'Haber Kartı 11. Kart'),
        ('kart_12', 'Haber Kartı 12. Kart'),
        ('kart_13', 'Haber Kartı 13. Kart'),
        ('kart_14', 'Haber Kartı 14. Kart'),
        ('kart_15', 'Haber Kartı 15. Kart'),
        ('kart_16', 'Haber Kartı 16. Kart'),
        ('kart_17', 'Haber Kartı 17. Kart'),
        ('kart_18', 'Haber Kartı 18. Kart'),
        ('header', 'Header Reklamı'),
        ('footer', 'Footer Reklamı'),
    ]
    konum = models.CharField(max_length=20, choices=REKLAM_KONUMU_CHOICES, unique=True, verbose_name="Reklam Konumu")
    baslik = models.CharField(max_length=200, verbose_name="Reklam Başlığı")
    resim = models.ImageField(upload_to='reklamlar/', blank=True, null=True, verbose_name="Reklam Görseli")
    hedef_url = models.URLField(blank=True, null=True, verbose_name="Hedef Web Sayfası URL'si", help_text="Tıklandığında yönlendirilecek web sayfası adresi")
    aktif = models.BooleanField(default=True, verbose_name="Aktif mi?")
    iframe_goster = models.BooleanField(default=False, help_text="Aktif edildiğinde, görsel yerine hedef URL'deki web sitesi canlı olarak kartın içinde gösterilir.", verbose_name="Canlı Web Sitesi (Iframe) Olarak Göster?")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reklam'
        verbose_name_plural = 'Reklamlar'

    def __str__(self):
        return f"{self.baslik} ({self.get_konum_display()})"




class Yazar(User):
    class Meta:
        proxy = True
        verbose_name = "Yazar"
        verbose_name_plural = "Yazarlar"

    @property
    def toplam_okunma(self):
        from django.db.models import Sum
        total = self.haber_set.aggregate(total_views=Sum('goruntulenme_sayisi'))['total_views']
        return total or 0

    @property
    def haber_sayisi(self):
        return self.haber_set.filter(kose_yazisi=False).count()

    @property
    def yazi_sayisi(self):
        return self.haber_set.filter(kose_yazisi=True).count()


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        UserProfile.objects.get_or_create(user=instance)

# Import engagement models to register them with the app
from .models_engagement import Poll, PollChoice, PollVote, Quiz, QuizQuestion, UserQuizScore

