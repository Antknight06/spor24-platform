import re
from django.core.management.base import BaseCommand
from haberler.models import KarateSehir, KarateAntrenor

class Command(BaseCommand):
    help = 'Karate Antrenörlerini TXT dosyasından (Yıl Hatası Düzeltilmiş) yükler'

    def handle(self, *args, **kwargs):
        dosya_yolu = 'veri.txt'
        self.stdout.write(self.style.WARNING("Veriler okunuyor..."))

        # ADIM 1: Önceki verileri temizle (Tertemiz başlangıç)
        silinen_sayisi, _ = KarateAntrenor.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Mevcut {silinen_sayisi} antrenör kaydı silindi. Veritabanı sıfırlandı."))

        try:
            with open(dosya_yolu, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Boş satırları ve başlıkları temizle
            temiz_satirlar = [line.strip() for line in lines if line.strip()]
            
            # Filtrelenecek kelimeler
            filtre = ["S.No", "Adı Soyadı", "Antrenörlük Kariyeri", "Kuşak", "Bölge", "Verildiği Yer", "Verildiği Tarih", "Vize Yılı", "Yazdır"]
            veri_havuzu = [satir for satir in temiz_satirlar if satir not in filtre and "Yazdır" not in satir]

            kaydedilen = 0
            
            i = 0
            while i < len(veri_havuzu):
                # Satır bir sayı mı? (Sıra No Adayı)
                curr_line = veri_havuzu[i]
                
                # KONTROL: Mevcut satır sayıysa VE bir sonraki satır SAYI DEĞİLSE (İsimse)
                # Bu kontrol "2025" yılını atlamamızı sağlar çünkü 2025'ten sonra "2" (Sıra No) gelir.
                is_valid_start = False
                if curr_line.isdigit():
                    if i + 1 < len(veri_havuzu):
                        next_line = veri_havuzu[i+1]
                        # Eğer sonraki satır sayı değilse (isimse), bu geçerli bir başlangıçtır
                        if not next_line.isdigit():
                            is_valid_start = True

                if is_valid_start:
                    try:
                        # Veri Yapısı: [SıraNo, Ad, Kademe, Kuşak, Şehir, Yer, Tarih, Yıl]
                        if i + 4 < len(veri_havuzu):
                            ad_soyad = veri_havuzu[i+1]
                            kademe = veri_havuzu[i+2]
                            # i+3 -> Kuşak (Atla)
                            sehir_adi = veri_havuzu[i+4] # Şehir 4. sırada
                            
                            # Şehri Bul veya Yarat
                            sehir, _ = KarateSehir.objects.get_or_create(ad=sehir_adi)
                            
                            # ANTRENÖRÜ KAYDET
                            KarateAntrenor.objects.create(
                                ad_soyad=ad_soyad,
                                sehir=sehir,
                                kademe=kademe,
                                kulup=""
                            )
                            kaydedilen += 1
                        
                        # Bir sonraki geçerli sayıya kadar ilerle
                        i += 1
                        # Sonsuz döngüden kaçınmak için limit
                        limit = 0
                        while i < len(veri_havuzu) and limit < 15:
                            # Bir sonraki potansiyel sıra numarasını arıyoruz
                            # Mevcut i digit ise ve i+1 digit değilse (isimse) dur.
                            if veri_havuzu[i].isdigit():
                                if i + 1 < len(veri_havuzu) and not veri_havuzu[i+1].isdigit():
                                    break # Yeni kayıt başlangıcı bulundu
                            i += 1
                            limit += 1
                            
                    except IndexError:
                        break 
                else:
                    # Sayı değilse veya "2025" gibi geçersiz bir sayıysa ilerle
                    i += 1

            self.stdout.write(self.style.SUCCESS(f"İŞLEM TAMAM!"))
            self.stdout.write(self.style.SUCCESS(f"✅ Toplam Kaydedilen: {kaydedilen}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("HATA: 'veri.txt' dosyası bulunamadı!"))
