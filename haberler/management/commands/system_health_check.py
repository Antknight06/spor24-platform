import os
import sys
import requests
from django.core.management.base import BaseCommand
from django.db import connection
from haberler.models import Haber, UserProfile, Kategori, TaramaLog

class Command(BaseCommand):
    help = "SPOR24.NET Otomatik Sistem Saglik Botu (Health Checker)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=================================================="))
        self.stdout.write(self.style.SUCCESS("[BOT] SPOR24.NET OTOMATIK SISTEM SAGLIK BOTU BASLATILDI"))
        self.stdout.write(self.style.SUCCESS("=================================================="))

        errors = []
        warnings = []
        checks_passed = 0
        total_checks = 0

        def check_url(name, url, expected_status=200, is_json=False):
            nonlocal checks_passed, total_checks
            total_checks += 1
            try:
                r = requests.get(url, timeout=20, headers={"User-Agent": "Spor24HealthBot/1.0"})
                if r.status_code == expected_status:
                    if is_json:
                        data = r.json()
                        checks_passed += 1
                        self.stdout.write(self.style.SUCCESS(f"[OK] [{name}] {url} -> Status: {r.status_code} OK (JSON Valid)"))
                        return data
                    else:
                        checks_passed += 1
                        self.stdout.write(self.style.SUCCESS(f"[OK] [{name}] {url} -> Status: {r.status_code} OK"))
                        return r.text
                else:
                    err_msg = f"[HA-TA] [{name}] {url} -> BEKLENMEYEN STATUS: {r.status_code} (Beklenen: {expected_status})"
                    errors.append(err_msg)
                    self.stdout.write(self.style.ERROR(err_msg))
                    return None
            except Exception as e:
                err_msg = f"[HATA] [{name}] {url} -> BAGLANTI / ISTEK HATASI: {e}"
                errors.append(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                return None

        # 1. BASE WEBSITE & ADMIN ENDPOINTS
        check_url("Ana Sayfa", "https://spor24.net/")
        check_url("Admin Giris", "https://spor24.net/admin/login/")

        # 2. API ENDPOINTS & PAGINATION
        news_api_data = check_url("Haber API Sayfa 1", "https://spor24.net/api/news/?page=1&page_size=24", is_json=True)
        if news_api_data and isinstance(news_api_data, dict):
            results = news_api_data.get('results', [])
            next_link = news_api_data.get('next')
            self.stdout.write(f"   -> Sayfa 1 Haber Sayisi: {len(results)}")
            self.stdout.write(f"   -> Sonraki Sayfa Linki (Pagination): {next_link}")
            if not next_link:
                warnings.append("API Pagination 'next' parametresi bos dondul!")
            else:
                # Test Page 2
                page2_url = "https://spor24.net" + next_link if next_link.startswith("/") else next_link
                check_url("Haber API Sayfa 2 (Dinamik Yukleme Testi)", page2_url, is_json=True)

        cats_api_data = check_url("Kategori API", "https://spor24.net/api/categories/", is_json=True)
        if cats_api_data and isinstance(cats_api_data, dict):
            cats = cats_api_data.get('results', [])
            self.stdout.write(f"   -> Aktif Kategori / Federasyon Sayisi: {len(cats)}")

        # 3. COLUMNISTS ARCHIVE PAGES
        columnists = UserProfile.objects.filter(user_type='yetkili')
        self.stdout.write(f"\n--- Kose Yazarlari Sayfa Testi (Toplam: {columnists.count()}) ---")
        for col in columnists:
            username = col.user.username
            check_url(f"Yazar {col.user.get_full_name() or username}", f"https://spor24.net/yazar/{username}/")

        # 4. CATEGORY SLUG PAGES
        self.stdout.write("\n--- Kategori / Brans Sayfalari Testi ---")
        test_slugs = ['karate', 'taekwondo', 'judo', 'kickboks', 'muay-thai', 'boks', 'mma', 'gures']
        for slug in test_slugs:
            check_url(f"Kategori {slug}", f"https://spor24.net/kategori/{slug}/")

        # 5. DATABASE ORM & MODEL INTEGRITY
        self.stdout.write("\n--- Veritabani ve Model Saglik Testi ---")
        db_vendor = connection.vendor
        published_count = Haber.objects.filter(yayinlandi=True).count()
        empty_title_count = Haber.objects.filter(baslik__isnull=True).count() + Haber.objects.filter(baslik='').count()

        total_checks += 1
        if empty_title_count == 0:
            checks_passed += 1
            self.stdout.write(self.style.SUCCESS(f"[OK] Veritabani Motoru: {db_vendor.upper()} | Yayinlanan Haber: {published_count} | Basliksiz Bos Haber: 0"))
        else:
            warnings.append(f"Veritabaninda {empty_title_count} adet basliksiz/bos haber bulundu!")

        # SUMMARY REPORT
        self.stdout.write(self.style.SUCCESS("\n=================================================="))
        self.stdout.write(self.style.SUCCESS(f"[SONUC] SAGLIK BOTU TARAMA OZETI: {checks_passed} / {total_checks} TEST BASARILI"))
        self.stdout.write(self.style.SUCCESS("=================================================="))

        if errors:
            self.stdout.write(self.style.ERROR(f"TESPIT EDILEN HATALAR ({len(errors)} Adet):"))
            for err in errors:
                self.stdout.write(self.style.ERROR(f" - {err}"))
        else:
            self.stdout.write(self.style.SUCCESS("TUM SISTEM SAGLIKLI! HICBIR KRITIK HATA BULUNMADI."))

        if warnings:
            self.stdout.write(self.style.WARNING(f"\nUYARILAR ({len(warnings)} Adet):"))
            for w in warnings:
                self.stdout.write(self.style.WARNING(f" - {w}"))

        # Log check execution to TaramaLog database table
        try:
            from haberler.models import FederasyonWebsite
            bot_fed, _ = FederasyonWebsite.objects.get_or_create(
                ad="SPOR24.NET Sistem Sağlık Botu",
                defaults={
                    "ana_url": "https://spor24.net",
                    "haberler_url": "https://spor24.net",
                    "aktif": True,
                    "haber_listesi_selector": "body",
                    "haber_baslik_selector": "h1",
                    "haber_link_selector": "a"
                }
            )
            log_status = "basarili" if len(errors) == 0 else "hata"
            log_msg = f"Bot Taraması: {checks_passed}/{total_checks} başarılı. Hata: {len(errors)}, Uyarı: {len(warnings)}"
            if errors:
                log_msg += " | Hatalar: " + " ; ".join(errors)
            TaramaLog.objects.create(
                federasyon_website=bot_fed,
                durum=log_status,
                eklenen_sayi=0,
                mesaj=log_msg
            )
        except Exception as log_err:
            self.stdout.write(self.style.ERROR(f"Log kayit hatasi: {log_err}"))

