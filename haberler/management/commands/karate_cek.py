import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from haberler.models import KarateSehir, KarateKulup, KarateAntrenor
import urllib3

# SSL hatalarını görmezden gel
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Karate Federasyonu Verilerini (Koordinatlı Tıklama ile) Çeker'

    def get_viewstate_and_inputs(self, soup):
        """Sayfadaki tüm gizli inputları (ViewState dahil) toplar"""
        payload = {}
        for inp in soup.find_all('input'):
            if inp.get('name'):
                # Eğer value None ise boş string yap
                val = inp.get('value')
                payload[inp.get('name')] = val if val is not None else ''
        return payload

    def handle(self, *args, **kwargs):
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://karatefed.org.tr'
        }

        # ==================================================================
        # 1. ANTRENÖRLERİ ÇEK (Tek Seferde Tüm Liste - 2025)
        # ==================================================================
        url_ant = "https://karatefed.org.tr/FedWeb/ant_sec.asp"
        headers['Referer'] = url_ant
        self.stdout.write(self.style.WARNING(f"\n=== 1. ANTRENÖRLER ÇEKİLİYOR (2025) ==="))

        try:
            # A) Sayfayı Analiz Et (GET)
            r1 = session.get(url_ant, headers=headers, verify=False)
            r1.encoding = 'windows-1254'
            soup = BeautifulSoup(r1.content, 'html.parser')
            
            # Gizli inputları al
            payload = self.get_viewstate_and_inputs(soup)
            
            # Select kutularını bul
            selects = soup.find_all('select')
            
            # Yıl kutusunun adını bul (VizeYili, Durum2 vb.)
            yil_input_name = "VizeYili" # Varsayılan
            for s in selects:
                # Kutu adında 'Yil' veya 'Vize' geçiyorsa veya içinde '2025' seçeneği varsa
                if "Yil" in str(s.get('name', '')) or "Vize" in str(s.get('name', '')) or "2025" in s.text:
                    yil_input_name = s.get('name')
                    break
            
            # Diğer kutular (Bölge, Kariyer vb.) için '0' (TAMAMI) değerini ayarla
            for s in selects:
                name = s.get('name')
                if name == yil_input_name:
                    payload[name] = '2025' # Hedef Yıl
                else:
                    payload[name] = '0' # TAMAMI

            # Tıklama Simülasyonu (Koordinat ŞART!)
            # 'Goster' butonunun adı ne olursa olsun x ve y ekle
            payload['Goster.x'] = '15'
            payload['Goster.y'] = '15'
            # Eğer 'Goster' adında bir input varsa onu silebiliriz, koordinat yeterli
            if 'Goster' in payload: del payload['Goster']

            self.stdout.write(f"   -> Yıl Kutusu: '{yil_input_name}' -> '2025' gönderiliyor...")

            # B) POST İsteği
            r2 = session.post(url_ant, headers=headers, data=payload, verify=False)
            r2.encoding = 'windows-1254'
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            
            rows = soup2.find_all('tr')
            self.stdout.write(f"   -> {len(rows)} satır veri döndü.")

            kayit_sayisi = 0
            # KarateAntrenor tablosunu temizle (Yıl değiştiği için eski veri kalmasın)
            # KarateAntrenor.objects.all().delete() # İsterseniz açabilirsiniz

            for row in rows:
                cols = row.find_all('td')
                # Tablo: [Sıra, Ad Soyad, Kariyer, Kuşak, Bölge, Verildiği Yer, Tarih, Vize Yılı]
                if len(cols) >= 5:
                    ad_soyad = cols[1].get_text(strip=True)
                    
                    # Başlık satırını ve boşları atla
                    if not ad_soyad or "Adı Soyadı" in ad_soyad: continue

                    kademe = cols[2].get_text(strip=True)
                    sehir_adi = cols[4].get_text(strip=True)
                    
                    if sehir_adi:
                        sehir_obj, _ = KarateSehir.objects.get_or_create(ad=sehir_adi)
                        KarateAntrenor.objects.update_or_create(
                            ad_soyad=ad_soyad,
                            defaults={
                                'sehir': sehir_obj,
                                'kademe': kademe,
                                'kulup': "" # Bu listede kulüp yok
                            }
                        )
                        kayit_sayisi += 1
            
            if kayit_sayisi > 0:
                self.stdout.write(self.style.SUCCESS(f"   -> BAŞARILI: {kayit_sayisi} Antrenör kaydedildi."))
            else:
                self.stdout.write(self.style.ERROR("   -> HATA: Liste boş. Sayfa içeriği kontrol ediliyor..."))
                # Hata ayıklama için body'nin bir kısmını yazdır
                # print(soup2.body.get_text()[:300])

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   -> HATA: {e}"))


        self.stdout.write("-" * 40)


        # ==================================================================
        # 2. KULÜPLERİ ÇEK (İl İl Tarama)
        # ==================================================================
        url_kulup = "https://karatefed.org.tr/FedWeb/klup_sec.asp"
        headers['Referer'] = url_kulup
        self.stdout.write(self.style.WARNING(f"\n=== 2. KULÜPLER ÇEKİLİYOR ==="))

        try:
            # A) Analiz
            r1 = session.get(url_kulup, headers=headers, verify=False)
            soup = BeautifulSoup(r1.content, 'html.parser')
            
            # Inputları al
            payload_base = self.get_viewstate_and_inputs(soup)
            
            # Şehir kutusunu bul
            select = soup.find('select')
            bolge_name = select.get('name') if select else "Bolge"
            
            self.stdout.write("   -> 81 İl taranıyor...")
            
            # Veritabanını temizle
            KarateKulup.objects.all().delete()
            
            total_kulup = 0
            for plaka in range(1, 82):
                payload = payload_base.copy()
                payload[bolge_name] = str(plaka)
                
                # Koordinat Tıklaması
                payload['Goster.x'] = '15'
                payload['Goster.y'] = '15'
                if 'Goster' in payload: del payload['Goster']
                
                try:
                    r2 = session.post(url_kulup, headers=headers, data=payload, verify=False)
                    r2.encoding = 'windows-1254'
                    soup2 = BeautifulSoup(r2.text, 'html.parser')
                    
                    rows = soup2.find_all('tr')
                    sehirdeki = 0
                    
                    for row in rows:
                        # Satırda "Detay" butonu var mı? Varsa veridir.
                        if "Detay" not in row.text: continue

                        cols = row.find_all('td')
                        # Tablo: [Detay, Kulüp Adı] (2 sütunlu yapı)
                        if len(cols) >= 2:
                            kulup_adi = cols[1].get_text(strip=True)
                            
                            if kulup_adi and "Kulüp Adı" not in kulup_adi:
                                # Şehir adını plakadan oluştur
                                sehir_obj, _ = KarateSehir.objects.get_or_create(ad=f"Şehir-{plaka}")
                                
                                KarateKulup.objects.create(
                                    ad=kulup_adi,
                                    sehir=sehir_obj,
                                    yetkili=""
                                )
                                sehirdeki += 1
                                total_kulup += 1
                    
                    if sehirdeki > 0:
                        print(f"[{plaka}:{sehirdeki}]", end=" ", flush=True)
                    else:
                        print(".", end="", flush=True)

                except Exception:
                    pass # Hata olursa o şehri atla
            
            self.stdout.write(self.style.SUCCESS(f"\n   -> BAŞARILI: Toplam {total_kulup} Kulüp kaydedildi."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   -> HATA: {e}"))
