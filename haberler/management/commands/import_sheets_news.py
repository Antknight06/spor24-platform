import os
import re
import requests
import gspread
import logging
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from oauth2client.service_account import ServiceAccountCredentials
from haberler.models import Kategori, FederasyonWebsite, FederasyonSosyalMedya

logger = logging.getLogger(__name__)

def fix_turkish_chars(text):
    if not text:
        return ""
    corrections = {
        'Trkiye': 'Türkiye',
        'trkiye': 'türkiye',
        'Gre': 'Güreş',
        'gre': 'güreş',
        'Okuluk': 'Okçuluk',
        'okuluk': 'okçuluk',
        'Atclk': 'Atıcılık',
        'atclk': 'atıcılık',
        'Dallar': 'Dalları',
        'dallar': 'dalları',
        'Branlar': 'Branşları',
        'Gelimekte': 'Gelişmekte',
        'Grme': 'Görme',
        'Engelliler': 'Engelliler',
        'itme': 'İşitme',
        'zcilik': 'İzcilik',
        'Krek': 'Kürek',
        'Oryantiring': 'Oryantiring',
        'zel': 'Özel',
        'Satran': 'Satranç',
        'Sualt': 'Sualtı',
        'Sporlar': 'Sporları',
        'Triatlon': 'Triatlon',
        'niversite': 'Üniversite',
        'Vcut': 'Vücut',
        'Gelitirme': 'Geliştirme',
        'Yzme': 'Yüzme'
    }
    for bad, good in corrections.items():
        text = text.replace(bad, good)
    return text

class Command(BaseCommand):
    help = 'Google E-Tablo üzerinden resmi federasyon web sayfalarını ve sosyal medya adreslerini günceller ve senkronize eder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Verileri gerçekten kaydetmeden sadece simüle eder'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('[INFO] SPREADSHEET FEDERASYON VE SOSYAL MEDYA ENTEGRASYONU BASLATILDI')
        self.stdout.write('=' * 60)

        # PostgreSQL sequence reset to prevent IntegrityError
        from django.db import connection
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT setval(pg_get_serial_sequence('\"haberler_federasyonwebsite\"','id'), coalesce(max(\"id\"), 1), max(\"id\") IS NOT null) FROM \"haberler_federasyonwebsite\";")
                cursor.execute("SELECT setval(pg_get_serial_sequence('\"haberler_federasyonsosyalmedya\"','id'), coalesce(max(\"id\"), 1), max(\"id\") IS NOT null) FROM \"haberler_federasyonsosyalmedya\";")
                cursor.execute("SELECT setval(pg_get_serial_sequence('\"haberler_kategori\"','id'), coalesce(max(\"id\"), 1), max(\"id\") IS NOT null) FROM \"haberler_kategori\";")
                cursor.execute("SELECT setval(pg_get_serial_sequence('\"haberler_haber\"','id'), coalesce(max(\"id\"), 1), max(\"id\") IS NOT null) FROM \"haberler_haber\";")
                self.stdout.write(self.style.SUCCESS("Database sequence sync completed successfully."))
            except Exception as seq_err:
                self.stdout.write(self.style.WARNING(f"Sequence sync warning: {seq_err}"))

        # 1. Google Sheets Yetkilendirmesi
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials_file = 'credentials.json'

        if not os.path.exists(credentials_file):
            self.stdout.write(self.style.ERROR(f"Hata: '{credentials_file}' dosyasi bulunamadi!"))
            return

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            client = gspread.authorize(creds)
            spreadsheet_id = '1sXaFJrGOzWOwjCaNd573dsEbBaWujDMNcxpniIDpyB0'
            sheet = client.open_by_key(spreadsheet_id).sheet1
        except Exception as auth_err:
            self.stdout.write(self.style.ERROR(f"Google Sheets yetkilendirme hatasi: {auth_err}"))
            return

        # 2. Verileri Oku
        try:
            records = sheet.get_all_records()
            self.stdout.write(self.style.SUCCESS(f"Google E-Tablodan toplam {len(records)} federasyon satiri okundu."))
            self.stdout.write(f"Kolon Basliklari: {sheet.row_values(1)}")
        except Exception as read_err:
            self.stdout.write(self.style.ERROR(f"E-Tablo verisi okunurken hata olustu: {read_err}"))
            return

        updated_count = 0
        created_count = 0

        for index, record in enumerate(records):
            fed_name = record.get('FEDERASYON ADI', '').strip()
            fed_name = fix_turkish_chars(fed_name)
            web_url = record.get('FEDERASYONLAR WEB', '').strip()
            instagram_url = record.get('INSTAGRAM', '').strip()
            facebook_url = record.get('FACEBOOK', '').strip()
            x_url = record.get('X.COM', '').strip()
            youtube_url = record.get('YOUTUBE', '').strip()

            if not fed_name:
                continue

            # Karakter bozulmalarını düzelt (Trkiye -> Türkiye)
            fed_name = fed_name.replace('Trkiye', 'Türkiye').replace('trkiye', 'türkiye')
            fed_name = fed_name.replace('TRKİYE', 'TÜRKİYE').replace('trk', 'türk')

            self.stdout.write(f"Isleniyor: {fed_name}")

            # Sosyal medya kullanıcı adlarını (handles) ayıkla
            instagram_handle = self._extract_handle(instagram_url)
            facebook_handle = self._extract_handle(facebook_url)
            x_handle = self._extract_handle(x_url)

            # Web sitelerinde / varsa temizle
            if web_url and not web_url.startswith('http'):
                web_url = 'https://' + web_url

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"   [Dry-Run] Federasyon: '{fed_name}' | Web: {web_url} | Insta: @{instagram_handle} | X: @{x_handle}"))
                continue

            # FederasyonWebsitesini bul veya oluştur
            fed_obj, created = FederasyonWebsite.objects.get_or_create(
                ad=fed_name,
                defaults={
                    'ana_url': web_url if web_url else 'https://www.google.com',
                    'haberler_url': web_url if web_url else 'https://www.google.com',
                    'aktif': True,
                    'haber_listesi_selector': '.news-list .news-item',  # Default selectors
                    'haber_baslik_selector': 'h3',
                    'haber_link_selector': 'a'
                }
            )

            # Bilgileri güncelle
            fed_obj.instagram_url = instagram_url
            fed_obj.facebook_url = facebook_url
            fed_obj.x_url = x_url
            fed_obj.youtube_url = youtube_url
            if web_url:
                fed_obj.ana_url = web_url
                # Eğer haberler_url ayarlanmamışsa veya varsayılan google ise güncelle
                if fed_obj.haberler_url == 'https://www.google.com' or not fed_obj.haberler_url:
                    fed_obj.haberler_url = web_url
            
            fed_obj.save()

            # Sosyal medya modelini güncelle
            sosyal_obj, _ = FederasyonSosyalMedya.objects.get_or_create(federasyon=fed_obj)
            sosyal_obj.instagram_kullanici_adi = instagram_handle
            sosyal_obj.facebook_sayfasi = facebook_handle
            sosyal_obj.x_sayfasi = x_handle
            sosyal_obj.save()

            # Kategori kontrolü ve akıllı ilişkilendirme
            category_name = self._get_short_category_name(fed_name)
            category_slug = slugify(category_name)
            
            # Kategori oluştur veya bul, federasyona ata
            kategori, cat_created = Kategori.objects.get_or_create(
                ad=category_name,
                defaults={
                    'slug': category_slug,
                    'federasyon_website': fed_obj,
                    'menude_goster': True
                }
            )
            
            # Eğer kategori varsa ama federasyon atanmamışsa ata
            if not kategori.federasyon_website:
                kategori.federasyon_website = fed_obj
                kategori.save()

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"   [YENI] Federasyon basariyla eklendi ve kategoriyle iliskilendirildi."))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"   [GUNCELLE] Federasyon bilgileri güncellendi."))

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f"Islem tamamlandi! {created_count} yeni federasyon eklendi, {updated_count} federasyon güncellendi."))

    def _extract_handle(self, url):
        """Sosyal medya profil URL'sinden kullanıcı adını (handle) ayıklar"""
        if not url:
            return ""
        
        # URL sonundaki slash'ı temizle
        url = url.strip().rstrip('/')
        
        # Regex ile kullanıcı adını bul
        # Örn: https://www.instagram.com/aticilikfederasyonu/ -> aticilikfederasyonu
        # Örn: https://x.com/taf_1923 -> taf_1923
        pattern = r'(?:https?://)?(?:www\.)?(?:instagram\.com|facebook\.com|x\.com|twitter\.com|youtube\.com)/@?([a-zA-Z0-9_\-\.]+)'
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            # Query parametrelerini temizle (Örn: ?locale=tr_TR)
            handle = match.group(1)
            if '?' in handle:
                handle = handle.split('?')[0]
            return handle
        return ""

    def _get_short_category_name(self, fed_name):
        """Federasyon isminden akıllıca kısa spor kategorisi ismi türetir"""
        # "Türkiye Karate Federasyonu" -> "Karate"
        # "Türkiye Atıcılık Federasyonu" -> "Atıcılık"
        name_lower = fed_name.lower()
        
        # Özel durumlar
        if 'kyokushin' in name_lower:
            return 'Kyokushin Karate'
        if 'kick' in name_lower:
            return 'Kickboks'
        if 'muay' in name_lower:
            return 'Muay Thai'
        if 'wushu' in name_lower:
            return 'Wushu Kung Fu'
        if 'gures' in name_lower or 'güreş' in name_lower:
            return 'Güreş'
        if 'atletizm' in name_lower:
            return 'Atletizm'
        if 'badminton' in name_lower:
            return 'Badminton'
        if 'boks' in name_lower:
            return 'Boks'
        if 'judo' in name_lower:
            return 'Judo'
        if 'taekwondo' in name_lower or 'tekvando' in name_lower:
            return 'Taekwondo'
        if 'aikido' in name_lower:
            return 'Aikido'
        if 'jitsu' in name_lower:
            return 'Jiu Jitsu'
            
        # Genel kural: "Türkiye ... Federasyonu" -> "..."
        match = re.search(r'Türkiye\s+(.*?)\s+Federasyonu', fed_name, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        return fed_name
