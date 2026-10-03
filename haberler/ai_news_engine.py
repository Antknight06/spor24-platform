# -*- coding: utf-8 -*-
"""
SPOR24 Haber Merkezi - Yapay Zeka Özgünleştirme & Haber Değeri Motoru
Google AI Studio Destekli Çoklu Model Otomasyon Servisi
"""

import os
import re
import json
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv('/var/www/ant_news_full/.env')
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

# Sıralı yedekli model listesi (kota aşımı veya hata anında otomatik bir sonrakine geçer)
AVAILABLE_MODELS = [
    'gemini-flash-lite-latest',
    'gemini-3.1-flash-lite',
    'gemini-flash-latest',
    'gemini-2.5-flash'
]
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

TON_ACIKLAMALARI = {
    'standart': 'Manşet dili, heyecan verici, akıcı, milli gurur ve sporcu odaklı, profesyonel spor basını üslubu.',
    'taktik': 'Taktiksel analiz, rakiplerin güçlü/zayıf yönleri, kadro değerlendirmesi, istatistik ve oyun stratejisi ağırlıklı.',
    'flash': 'Kısa, dinamik, hızlı okunabilir flaş haber / son dakika formatı.',
    'roportaj': 'Sporcu ve antrenör görüşlerine, duyguya ve motivasyona odaklanan hikayeleştirici dil.'
}

def clean_json_response(raw_text):
    """Parses JSON safely even if model includes markdown code blocks or unescaped newlines."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text, strict=False)
    except Exception:
        result = {}
        skor_m = re.search(r'"haber_degeri_skoru"\s*:\s*(\d+)', text)
        result['haber_degeri_skoru'] = int(skor_m.group(1)) if skor_m else 75
        
        analiz_m = re.search(r'"ai_analiz"\s*:\s*"(.*?)"(?=,\s*"[a-zA-Z_]+"\s*:|\s*})', text, re.DOTALL)
        result['ai_analiz'] = analiz_m.group(1).replace('\\"', '"') if analiz_m else "Analiz oluşturuldu."
        
        baslik_m = re.search(r'"ozgun_baslik"\s*:\s*"(.*?)"(?=,\s*"[a-zA-Z_]+"\s*:|\s*})', text, re.DOTALL)
        result['ozgun_baslik'] = baslik_m.group(1).replace('\\"', '"') if baslik_m else "Özgün Başlık"
        
        ozet_m = re.search(r'"ozgun_ozet"\s*:\s*"(.*?)"(?=,\s*"[a-zA-Z_]+"\s*:|\s*})', text, re.DOTALL)
        result['ozgun_ozet'] = ozet_m.group(1).replace('\\"', '"') if ozet_m else ""
        
        icerik_m = re.search(r'"ozgun_icerik"\s*:\s*"(.*?)"(?=,\s*"[a-zA-Z_]+"\s*:|\s*})', text, re.DOTALL)
        result['ozgun_icerik'] = icerik_m.group(1).replace('\\"', '"').replace('\\n', '\n') if icerik_m else text
        
        return result

def ozgunlestir_haber(bekleyen_haber, ton='standart'):
    """
    Bekleyen haberi Google Gemini modelleri ile özgünleştirir, 
    haber değeri skoru üretir ve nesneye kaydeder.
    Herhangi bir model 429 veya hata verirse otomatik olarak yedek modele geçer.
    """
    if not GEMINI_API_KEY:
        error_msg = "GEMINI_API_KEY sunucu ortamında tanımlı değil."
        logger.error(error_msg)
        bekleyen_haber.ai_durum = 'hata'
        bekleyen_haber.ai_analiz = error_msg
        bekleyen_haber.save(update_fields=['ai_durum', 'ai_analiz'])
        return False, error_msg

    bekleyen_haber.ai_durum = 'isleniyor'
    bekleyen_haber.save(update_fields=['ai_durum'])

    ton_talimati = TON_ACIKLAMALARI.get(ton, TON_ACIKLAMALARI['standart'])

    system_instruction = f"""
Sen SPOR24.NET'in kıdemli spor yazı işleri müdürü ve baş editörüsün.
Görevin, Türk federasyonlarının resmi sitelerinden çekilen kuru, bürokratik veya dağınık basın bültenlerini;
akıcı, heyecan verici, tarafsız, profesyonel spor basını dilinde (Ters Piramit kuralı, 5N1K, SEO uyumlu) özgün bir haber haline getirmektir.

Tercih Edilen Üslup: {ton_talimati}

Çıktıyı SADECE geçerli bir JSON objesi olarak ver:
{{
  "haber_degeri_skoru": 85,
  "ai_analiz": "Haber değeri gerekçesi ve editoryal değerlendirme notu",
  "ozgun_baslik": "Vurucu Başlık",
  "ozgun_ozet": "Haber spotu (1-2 cümle, 5N1K)",
  "ozgun_icerik": "<p>Haber metni temiz HTML formatında (h2, p, ul, li, blockquote etiketleriyle)...</p>",
  "etiketler": ["Etiket1", "Etiket2", "Etiket3"]
}}

KRİTİK EDİTORYAL KURALLAR:
1. BAŞLIK: Asla '21 Eylül 2026', 'Duyuru', 'Faaliyet Raporu' gibi bürokratik veya tarihli girişlerle başlamamalı. Merak uyandıran, milli gurur, sporcu ve rekabet odaklı, 50-85 karakter arası olmalı.
2. SPORCU & RAKİP LİSTELERİ: Sporcu veya rakip isimleri dümdüz metin yerine şık <ul> ve <li> listesiyle ayrıştırılmalı.
3. ARA BAŞLIKLAR: Metin içinde en az 2 adet <h2> ara başlık bulunmalı.
4. SPOR24 BİLGİ KUTUSU: Metin içinde mutlaka bir adet <blockquote> etiketi içerisinde "📌 SPOR24 BİLGİ KUTUSU: ..." başlığıyla spor dalı, turnuva tarihi/statüsü veya ilginç bir arka plan bilgisi (E-E-A-T katma değeri) eklenmeli.
5. TEMİZ HTML: Asla markdown işaretleri (**, ##, ```) HTML içine karıştırılmamalı, doğrudan tertemiz HTML üretilmeli.
6. KURUMSAL İMZA: Metnin en altına *Haber Kaynağı: [Federasyon] | Editoryal Düzenleme: SPOR24 Haber Merkezi* notu eklenmeli.
7. SKORLAMA (1-100):
   - 75-100 (Yüksek Değer): Uluslararası şampiyona, olimpiyat, dünya kupası elemesi, madalya, milli takım.
   - 50-74 (Orta Değer): Ulusal lig sonuçları, gelişim kampları, yerel turnuvalar.
   - 0-49 (Düşük Değer): Bürokratik kararlar, hakem vize yenileme, vefat/başsağlığı, genel kurul ilanları, ihale duyuruları.
"""

    fed_ad = bekleyen_haber.federasyon_website.ad if bekleyen_haber.federasyon_website else "Genel Spor"
    user_prompt = f"""
Federasyon: {fed_ad}
Kaynak URL: {bekleyen_haber.kaynak_url}
Ham Başlık: {bekleyen_haber.baslik}
Ham Özet: {bekleyen_haber.ozet}
Ham İçerik: {bekleyen_haber.icerik}
"""

    payload = {
        'system_instruction': {'parts': [{'text': system_instruction}]},
        'contents': [{'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'response_mime_type': 'application/json',
            'temperature': 0.35,
            'maxOutputTokens': 8192
        }
    }

    last_error = ""

    # İki tur döngü: Her model denenir, 429 durumunda bir sonraki modele geçilir
    for pass_num in range(2):
        for model_name in AVAILABLE_MODELS:
            url = GEMINI_URL_TEMPLATE.format(model=model_name, key=GEMINI_API_KEY)
            try:
                res = requests.post(url, json=payload, timeout=35)
                if res.status_code == 429:
                    last_error = f"{model_name} 429 Hız Sınırı"
                    logger.warning(f"{model_name} 429 verdi, sonraki modele geçiliyor...")
                    continue

                if res.status_code != 200:
                    last_error = f"{model_name} API Hatası ({res.status_code}): {res.text[:150]}"
                    logger.warning(last_error)
                    continue

                data = res.json()
                raw_text = data['candidates'][0]['content']['parts'][0]['text']
                parsed = clean_json_response(raw_text)

                bekleyen_haber.ozgun_baslik = parsed.get('ozgun_baslik', '').strip()
                bekleyen_haber.ozgun_ozet = parsed.get('ozgun_ozet', '').strip()
                bekleyen_haber.ozgun_icerik = parsed.get('ozgun_icerik', '').strip()
                bekleyen_haber.haber_degeri_skoru = int(parsed.get('haber_degeri_skoru', 50))
                bekleyen_haber.ai_analiz = parsed.get('ai_analiz', '').strip()
                bekleyen_haber.ai_durum = 'hazir'
                bekleyen_haber.save(update_fields=[
                    'ozgun_baslik', 'ozgun_ozet', 'ozgun_icerik', 
                    'haber_degeri_skoru', 'ai_analiz', 'ai_durum'
                ])

                logger.info(f"BekleyenHaber #{bekleyen_haber.id} [{model_name}] ile başarıyla özgünleştirildi (Skor: {bekleyen_haber.haber_degeri_skoru})")
                return True, parsed

            except Exception as e:
                last_error = f"{model_name} istisnası: {str(e)}"
                logger.warning(last_error)
                continue

        if pass_num == 0:
            time.sleep(5)  # Tüm modeller denendiyse 5s bekle ve son bir tur daha dene

    # Tüm modeller başarısız olduysa
    err = f"Gemini Modelleri yanıt veremedi. Son hata: {last_error}"
    logger.error(err)
    bekleyen_haber.ai_durum = 'hata'
    bekleyen_haber.ai_analiz = err
    bekleyen_haber.save(update_fields=['ai_durum', 'ai_analiz'])
    return False, err
