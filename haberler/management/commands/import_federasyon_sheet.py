from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import FederasyonWebsite, Kategori
import urllib.request
import csv

class Command(BaseCommand):
    help = 'Google Sheets tablosundaki tüm federasyonları ve sosyal medya bağlantılarını içeri aktarır/günceller'

    def handle(self, *args, **options):
        url = "https://docs.google.com/spreadsheets/d/1sXaFJrGOzWOwjCaNd573dsEbBaWujDMNcxpniIDpyB0/export?format=csv"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        try:
            self.stdout.write("Google Sheets CSV dosyası indiriliyor...")
            with urllib.request.urlopen(req) as response:
                csv_data = response.read().decode('utf-8')
            
            reader = csv.reader(csv_data.splitlines())
            rows = list(reader)
            if not rows:
                self.stdout.write(self.style.ERROR("Tablo boş veya okunamadı!"))
                return
                
            data_rows = rows[1:]
            self.stdout.write(self.style.SUCCESS(f"Tablodan {len(data_rows)} federasyon satırı okundu."))
            
            # İsim normalizasyon fonksiyonu (benzer isimleri eşleştirmek için)
            def normalize_name(name):
                return name.lower().replace(" ", "").replace("-", "").replace("ı", "i").replace("ü", "u").replace("ö", "o").replace("ş", "s").replace("ç", "c").replace("ğ", "g")

            existing_feds = list(FederasyonWebsite.objects.all())
            existing_map = {normalize_name(fed.ad): fed for fed in existing_feds}
            
            created_count = 0
            updated_count = 0
            
            for row in data_rows:
                if len(row) < 3 or not row[1].strip():
                    continue
                    
                fed_name = row[1].strip()
                web_url = row[2].strip()
                instagram = row[3].strip() if len(row) > 3 else ""
                facebook = row[4].strip() if len(row) > 4 else ""
                x_url = row[5].strip() if len(row) > 5 else ""
                youtube = row[6].strip() if len(row) > 6 else ""
                
                # Linkleri temizle
                def clean_url(u):
                    if not u or u == "-" or u.lower() == "yok":
                        return ""
                    if not u.startswith("http"):
                        u = "https://" + u
                    return u
                    
                web_url = clean_url(web_url)
                instagram = clean_url(instagram)
                facebook = clean_url(facebook)
                x_url = clean_url(x_url)
                youtube = clean_url(youtube)
                
                if not web_url:
                    continue
                    
                norm_name = normalize_name(fed_name)
                
                # Federasyon isminden kategori adı çıkar
                category_name = fed_name.replace("Türkiye", "").replace("Federasyonu", "").strip()
                category_name = category_name.replace("Gelişmekte Olan Spor Branşları", "GOSBF")
                category_name = category_name.strip()
                if not category_name:
                    category_name = fed_name
                    
                if norm_name in existing_map:
                    # Mevcut olanı güncelle
                    fed = existing_map[norm_name]
                    fed.instagram_url = instagram or fed.instagram_url
                    fed.facebook_url = facebook or fed.facebook_url
                    fed.x_url = x_url or fed.x_url
                    fed.youtube_url = youtube or fed.youtube_url
                    fed.ana_url = web_url or fed.ana_url
                    fed.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"! Güncellendi: {fed.ad}"))
                else:
                    # Yeni ekle
                    fed = FederasyonWebsite.objects.create(
                        ad=fed_name,
                        ana_url=web_url,
                        haberler_url=web_url,
                        instagram_url=instagram,
                        facebook_url=facebook,
                        x_url=x_url,
                        youtube_url=youtube,
                        aktif=False,  # Varsayılan olarak pasif (selector'ları manuel ayarlanana kadar)
                        haber_listesi_selector=".news-list .item",
                        haber_baslik_selector="h3",
                        haber_link_selector="a",
                        haber_tarih_selector=".date",
                        haber_ozet_selector=".summary"
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ Eklendi: {fed.ad}"))
                    
                # Kategori varlığından ve ilişkisinden emin ol
                if category_name:
                    slug = slugify(category_name.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g'))
                    kategori, cat_created = Kategori.objects.get_or_create(
                        slug=slug,
                        defaults={
                            'ad': category_name,
                            'federasyon_website': fed
                        }
                    )
                    if not cat_created and not kategori.federasyon_website:
                        kategori.federasyon_website = fed
                        kategori.save()
                        
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 İşlem başarıyla tamamlandı!\n"
                    f"   • Yeni Eklenen: {created_count}\n"
                    f"   • Güncellenen: {updated_count}\n"
                    f"   • Toplam Federasyon: {FederasyonWebsite.objects.count()}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Hata oluştu: {str(e)}"))
