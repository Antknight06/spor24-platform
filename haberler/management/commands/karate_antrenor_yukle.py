import os
import re
from django.core.management.base import BaseCommand
from haberler.models import KarateAntrenor
from django.db import transaction

class Command(BaseCommand):
    help = '3050 kişilik antrenör listesini SIRA NO HATASI GİDERİLMİŞ MOD ile yükler'

    def handle(self, *args, **options):
        file_path = 'Tüm antrenörler.txt'

        if not os.path.exists(file_path):
            if os.path.exists(os.path.join('ANT_News', file_path)):
                 file_path = os.path.join('ANT_News', file_path)
            else:
                self.stdout.write(self.style.ERROR(f'Dosya bulunamadı! {file_path}'))
                return

        self.stdout.write('Dosya okunuyor...')
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # Tırnak temizliği
        clean_content = re.sub(r"'", '', raw_content)
        lines = [line.strip() for line in clean_content.split('\n') if line.strip()]

        self.stdout.write(f'Temizlenen satır sayısı: {len(lines)}. Veritabanı sıfırlanıyor...')
        
        # Temiz başlangıç
        KarateAntrenor.objects.all().delete()

        antrenor_nesneleri = []
        current_block = []
        beklenen_sira = 1 
        
        for line in lines:
            # Sıra numarası takibi (1, 2, 3...)
            if line == str(beklenen_sira):
                # DÜZELTME BURADA: Eğer beklenen sıra 1 ise, önceki blok BAŞLIKTIR (S.No vs), kaydetme!
                # Sadece beklenen_sira 1'den büyükse (yani 2'yi bulduysak 1'i kaydet gibi) işlem yap.
                if current_block and beklenen_sira > 1:
                    obj = self.parse_block(current_block)
                    if obj:
                        antrenor_nesneleri.append(obj)
                
                current_block = [line]
                beklenen_sira += 1
            else:
                current_block.append(line)

        # Döngü bittiğinde eldeki son bloğu (3050. kayıt) kaydet
        if current_block:
            obj = self.parse_block(current_block)
            if obj:
                antrenor_nesneleri.append(obj)

        with transaction.atomic():
            KarateAntrenor.objects.bulk_create(antrenor_nesneleri)

        self.stdout.write(self.style.SUCCESS(f'İşlem Tamamlandı! {len(antrenor_nesneleri)} kayıt başarıyla yüklendi.'))

    def parse_block(self, block):
        try:
            if not block: return None
            sira = block[0]
            
            # Ekstra güvenlik: Sıra no sayı değilse atla
            if not sira.isdigit(): return None

            ad_list = []
            kariyer = ""
            kusak = ""
            bolge = ""
            yer = ""
            tarih = ""
            vize = ""

            # 1. AD SOYAD AYRIŞTIRMA
            idx = 1
            while idx < len(block):
                satir = block[idx]
                
                # KARIYER KONTROLÜ
                if "ANTRENÖR" in satir or "MONİTÖR" in satir:
                    break
                
                # KUŞAK KONTROLÜ (1. DAN formatı)
                if re.search(r'\d+\.\s*(DAN|KYU|Dan|Kyu)', satir):
                    break
                
                # TARİH KONTROLÜ
                if re.search(r'\d{2}\.\d{2}\.\d{4}', satir):
                    break
                
                ad_list.append(satir)
                idx += 1
            
            adi_soyadi = " ".join(ad_list)

            # 2. DİĞER VERİLERİ ÇEKME
            kalan_satirlar = block[idx:]
            
            for item in kalan_satirlar:
                if "ANTRENÖR" in item or "MONİTÖR" in item:
                    kariyer = item
                    break
            
            for item in kalan_satirlar:
                if re.search(r'\d+\.\s*(DAN|KYU)', item):
                    kusak = item
                    break

            tarih_match = None
            for item in kalan_satirlar:
                match = re.search(r'(\d{2}\.\d{2}\.\d{4})', item)
                if match:
                    tarih = match.group(1)
                    tarih_match = item
                    break
            
            for item in kalan_satirlar:
                # 4 haneli yıl kontrolü (19.. veya 20..)
                if item.isdigit() and len(item) == 4 and (item.startswith('19') or item.startswith('20')):
                    vize = item
                    break

            yer_adaylari = []
            for item in kalan_satirlar:
                if item == kariyer: continue
                if item == kusak: continue
                if item == vize: continue
                if tarih_match and item == tarih_match: continue
                if "[source" in item: continue
                
                yer_adaylari.append(item)

            if len(yer_adaylari) > 0:
                bolge = yer_adaylari[0]
            if len(yer_adaylari) > 1:
                yer = yer_adaylari[1]

            return KarateAntrenor(
                sira_no=sira,
                adi_soyadi=adi_soyadi,
                kariyer=kariyer,
                kusak=kusak,
                bolge=bolge,
                verildigi_yer=yer,
                verildigi_tarih=tarih,
                vize_yili=vize
            )

        except Exception as e:
            print(f"Hata (Sıra {block[0]}): {e}")
            return None
