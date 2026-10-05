"""
SPOR24 Akıllı TAG & AirTag Üretim Motoru (Smart Tags & Digital AirTag Engine)
Haber başlığı, kategorisi ve içeriğinden dinamik, semantik hashtag ve AirTag kodları üretir.
"""

import re
import hashlib
from urllib.parse import quote

# 1. Branş Listesi & Sözlük
SPOR_BRANSLARI = {
    'karate': 'Karate',
    'judo': 'Judo',
    'boks': 'Boks',
    'taekwondo': 'Taekwondo',
    'tekvando': 'Taekwondo',
    'wushu': 'Wushu',
    'kung fu': 'KungFu',
    'muay thai': 'MuayThai',
    'kickboks': 'Kickboks',
    'gures': 'Güreş',
    'güreş': 'Güreş',
    'mma': 'MMA',
    'jiu jitsu': 'JiuJitsu',
    'ju jitsu': 'JuJitsu',
    'hapkido': 'Hapkido',
    'sambo': 'Sambo',
    'savate': 'Savate',
    'kempo': 'Kempo',
    'capoeira': 'Capoeira',
    'kyokushin': 'Kyokushin',
    'kendo': 'Kendo',
    'voleybol': 'Voleybol',
    'basketbol': 'Basketbol',
    'hentbol': 'Hentbol',
    'atletizm': 'Atletizm',
    'yuzme': 'Yüzme',
    'yüzme': 'Yüzme',
    'okculuk': 'Okçuluk',
    'okçuluk': 'Okçuluk',
    'badminton': 'Badminton',
    'halter': 'Halter',
    'cimnastik': 'Cimnastik',
    'kayak': 'Kayak',
    'tenis': 'Tenis',
    'masa tenisi': 'MasaTenisi',
    'bilardo': 'Bilardo',
    'bisiklet': 'Bisiklet',
    'curling': 'Curling',
    'kurek': 'Kürek',
    'kürek': 'Kürek',
    'satranc': 'Satranç',
    'satranç': 'Satranç',
    'buz hokeyi': 'BuzHokeyi',
    'ragbi': 'Ragbi',
    'eskrim': 'Eskrim'
}

# 2. Önemli Şehirler & Lokasyonlar
SEHIRLER = {
    'ankara': 'Ankara',
    'istanbul': 'İstanbul',
    'izmir': 'İzmir',
    'konya': 'Konya',
    'antalya': 'Antalya',
    'erzurum': 'Erzurum',
    'bursa': 'Bursa',
    'adana': 'Adana',
    'trabzon': 'Trabzon',
    'samsun': 'Samsun',
    'sivas': 'Sivas',
    'agri': 'Ağrı',
    'ağrı': 'Ağrı',
    'gaziantep': 'Gaziantep',
    'kocaeli': 'Kocaeli',
    'kayseri': 'Kayseri',
    'mersin': 'Mersin',
    'eskişehir': 'Eskişehir',
    'eskisehir': 'Eskişehir',
    'diyarbakir': 'Diyarbakır',
    'diyarbakır': 'Diyarbakır',
    'sakarya': 'Sakarya',
    'denizli': 'Denizli',
    'isparta': 'Isparta',
    'rize': 'Rize',
    'ordu': 'Ordu',
    'malatya': 'Malatya',
    'duzce': 'Düzce',
    'düzce': 'Düzce',
    'bolu': 'Bolu',
    'madrid': 'Madrid',
    'salzburg': 'Salzburg',
    'misir': 'Mısır',
    'mısır': 'Mısır',
    'sirbistan': 'Sırbistan',
    'sırbistan': 'Sırbistan',
    'belgrad': 'Belgrad',
    'erzurum': 'Erzurum',
    'paris': 'Paris',
    'tokyo': 'Tokyo',
    'baku': 'Bakü',
    'bakü': 'Bakü'
}

# 3. Kategori / Etkinlik Terimleri
ORGANIZASYONLAR = [
    (r'\bu14\b', 'U14'),
    (r'\bu16\b', 'U16'),
    (r'\bu18\b', 'U18'),
    (r'\bu21\b', 'U21'),
    (r'milli\s*takım|millî\s*takım', 'MilliTakım'),
    (r'dan\s*e[gğ]itim|dan\s*s[ıi]nav', 'DanSınavı'),
    (r'antren[oö]r', 'Antrenörlük'),
    (r'hakem', 'Hakemlik'),
    (r'geli[sş]im\s*seminer', 'GelişimSemineri'),
    (r'alt\s*yap[ıi]|altyap[ıi]', 'Altyapı'),
    (r'd[uü]nya\s*[sş]ampiyon', 'DünyaŞampiyonası'),
    (r'avrupa\s*[sş]ampiyon', 'AvrupaŞampiyonası'),
    (r't[uü]rkiye\s*[sş]ampiyon', 'TürkiyeŞampiyonası'),
    (r'balkan\s*[sş]ampiyon', 'BalkanŞampiyonası'),
    (r'series\s*a', 'SeriesA'),
    (r'grand\s*prix', 'GrandPrix'),
    (r'k[ıi][sş]\s*oyunlar', 'KışOyunları'),
    (r'fisu', 'FISU'),
    (r'olimpiyat', 'Olimpiyat'),
    (r'madalya|bronz|g[uü]m[uü][sş]|alt[ıi]n', 'Madalya'),
    (r'kampt[ıi]|haz[ıi]rl[ıi]k\s*kamp', 'MilliKamp')
]

# 4. Önemli İsimler & Liderler
ONEMLI_ISIMLER = [
    (r'eray\s*[sş]amdan', 'ErayŞamdan'),
    (r'erc[uü]ment\s*ta[sş]demir', 'ErcümentTaşdemir'),
    (r'ali\s*ar[ıi]k', 'AliArık'),
    (r'zilan\s*ertem', 'ZilanErtem'),
    (r'sinem\s*oru[cç]', 'SinemOruç'),
    (r'muhammet\s*kemal\s*g[uü]l[sş]en|g[uü]l[sş]en\s*ailesi', 'GülşenAilesi')
]


def generate_smart_tags(haber):
    """
    Bir haber nesnesinden veya sözlüğünden akıllı taglar üretir.
    En az 3, en fazla 7 benzersiz hashtag döndürür.
    """
    if not haber:
        return ["#Spor24", "#Haber"]

    baslik = getattr(haber, 'baslik', '') or (haber.get('title') if isinstance(haber, dict) else '') or ''
    icerik = getattr(haber, 'icerik', '') or (haber.get('content') if isinstance(haber, dict) else '') or ''
    kat_ad = ''
    if hasattr(haber, 'kategori') and haber.kategori:
        kat_ad = haber.kategori.ad
    elif isinstance(haber, dict):
        kat_ad = haber.get('category_name') or haber.get('category') or ''

    fed_ad = ''
    if hasattr(haber, 'federasyon_website') and haber.federasyon_website:
        fed_ad = haber.federasyon_website.ad

    full_text = f"{baslik} {kat_ad} {fed_ad} {icerik[:500]}".lower()

    tags = []

    # 1. Kategori / Branş Tagı
    if kat_ad:
        clean_kat = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]', '', kat_ad)
        if clean_kat:
            tags.append(f"#{clean_kat}")

    # Branş sözlüğünden tara
    for keyword, tag_name in SPOR_BRANSLARI.items():
        if keyword in full_text:
            tag = f"#{tag_name}"
            if tag not in tags:
                tags.append(tag)
            if len(tags) >= 2:
                break

    # 2. Organizasyon ve Kategori Terimleri
    for pattern, tag_name in ORGANIZASYONLAR:
        if re.search(pattern, full_text, re.IGNORECASE):
            tag = f"#{tag_name}"
            if tag not in tags:
                tags.append(tag)

    # 3. Şehirler / Lokasyonlar
    for city_key, city_name in SEHIRLER.items():
        if re.search(r'\b' + city_key + r'\b', full_text, re.IGNORECASE):
            tag = f"#{city_name}"
            if tag not in tags:
                tags.append(tag)

    # 4. Kişiler / Sporcular
    for pattern, person_name in ONEMLI_ISIMLER:
        if re.search(pattern, full_text, re.IGNORECASE):
            tag = f"#{person_name}"
            if tag not in tags:
                tags.append(tag)

    # 5. Kurumsal Fallback
    if '#Spor24' not in tags:
        tags.append('#Spor24')

    # Maksimum 6 en iyi tag
    return tags[:6]


def get_airtag_id(haber):
    """
    Haber için kriptografik AirTag ID üretir.
    Format: SP24-{id}-{SHA256(6 hane)}
    Örnek: SP24-1433-692C2D
    """
    if not haber:
        return "SP24-0000-NONE"
    
    hid = getattr(haber, 'id', None) or (haber.get('id') if isinstance(haber, dict) else 0)
    baslik = getattr(haber, 'baslik', '') or (haber.get('title') if isinstance(haber, dict) else '')
    tarih = getattr(haber, 'olusturma_tarihi', None)
    tarih_str = tarih.strftime('%Y%m%d') if tarih else '2026'
    
    raw = f"{hid}_{tarih_str}_{baslik[:20]}"
    sig = hashlib.sha256(raw.encode('utf-8', errors='ignore')).hexdigest()[:6].upper()
    return f"SP24-{hid}-{sig}"


def get_airtag_shortlink(haber, channel='wa_share'):
    """
    AirTag takip parametreli kısa link üretir.
    Örnek: https://spor24.net/c/1433?tag=wa_share
    """
    hid = getattr(haber, 'id', None) or (haber.get('id') if isinstance(haber, dict) else 0)
    base = f"https://spor24.net/c/{hid}"
    if channel:
        return f"{base}?tag={channel}"
    return base
