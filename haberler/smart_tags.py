"""
SPOR24 Akıllı TAG & AirTag Üretim Motoru (Smart Tags & Digital AirTag Engine)
Haber başlığı, kategorisi ve içeriğinden dinamik, semantik hashtag ve AirTag kodları üretir.
"""

import re
import hashlib
from urllib.parse import quote

def turkish_lower(text):
    """Türkçe İ / I harflerini bozmadan küçük harfe dönüştürür."""
    if not text:
        return ""
    return text.replace('İ', 'i').replace('I', 'ı').lower()

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

# 2. Önemli Şehirler, Ülkeler & Lokasyonlar
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
    'letonya': 'Letonya',
    'riga': 'Riga',
    'polonya': 'Polonya',
    'macaristan': 'Macaristan',
    'hirvatistan': 'Hırvatistan',
    'hırvatistan': 'Hırvatistan',
    'gurcistan': 'Gürcistan',
    'gürcistan': 'Gürcistan',
    'azerbaycan': 'Azerbaycan',
    'italya': 'İtalya',
    'ispanya': 'İspanya',
    'almanya': 'Almanya',
    'fransa': 'Fransa',
    'ingiltere': 'İngiltere',
    'japonya': 'Japonya',
    'ozbekistan': 'Özbekistan',
    'özbekistan': 'Özbekistan',
    'kazakistan': 'Kazakistan',
    'rusya': 'Rusya',
    'madrid': 'Madrid',
    'salzburg': 'Salzburg',
    'misir': 'Mısır',
    'mısır': 'Mısır',
    'sirbistan': 'Sırbistan',
    'sırbistan': 'Sırbistan',
    'belgrad': 'Belgrad',
    'paris': 'Paris',
    'tokyo': 'Tokyo',
    'baku': 'Bakü',
    'bakü': 'Bakü',
    'atina': 'Atina',
    'roma': 'Roma'
}

# 3. Kategori / Etkinlik Terimleri
ORGANIZASYONLAR = [
    (r'\bu14\b', 'U14'),
    (r'\bu16\b', 'U16'),
    (r'\bu18\b', 'U18'),
    (r'\bu21\b', 'U21'),
    (r'milli\s*takım|millî\s*takım|milli\s*sporcu|millî\s*sporcu|milli\s*karateci|millî\s*karateci', 'MilliTakım'),
    (r'avrupa\s*[sş]ampiyon', 'AvrupaŞampiyonası'),
    (r'd[uü]nya\s*[sş]ampiyon', 'DünyaŞampiyonası'),
    (r'madalya|bronz|g[uü]m[uü][sş]|alt[ıi]n|k[uü]rs[uü]', 'Madalya'),
    (r't[uü]rkiye\s*[sş]ampiyon', 'TürkiyeŞampiyonası'),
    (r'balkan\s*[sş]ampiyon', 'BalkanŞampiyonası'),
    (r'series\s*a', 'SeriesA'),
    (r'grand\s*prix', 'GrandPrix'),
    (r'k[ıi][sş]\s*oyunlar', 'KışOyunları'),
    (r'fisu', 'FISU'),
    (r'olimpiyat', 'Olimpiyat'),
    (r'dan\s*e[gğ]itim|dan\s*s[ıi]nav', 'DanSınavı'),
    (r'antren[oö]rl[uü]k|antren[oö]r\s*kurs', 'Antrenörlük'),
    (r'hakemlik|hakem\s*kurs', 'Hakemlik'),
    (r'geli[sş]im\s*seminer', 'GelişimSemineri'),
    (r'alt\s*yap[ıi]|altyap[ıi]', 'Altyapı'),
    (r'kampt[ıi]|haz[ıi]rl[ıi]k\s*kamp', 'MilliKamp')
]

# 4. Önemli İsimler & Liderler
ONEMLI_ISIMLER = [
    (r'eray\s*[sş]amdan', 'ErayŞamdan'),
    (r'erc[uü]ment\s*ta[sş]demir', 'ErcümentTaşdemir'),
    (r'ali\s*ar[ıi]k', 'AliArık'),
    (r'zilan\s*ertem', 'ZilanErtem'),
    (r'sinem\s*oru[cç]', 'SinemOruç'),
    (r'muhammet\s*kemal\s*g[uü]l[sş]en|g[uü]l[sş]en\s*ailesi', 'GülşenAilesi'),
    (r'kadir\s*efe\s*g[uü]l[sş]en', 'KadirEfeGülşen'),
    (r'ismail\s*efe\s*polat', 'İsmailEfePolat'),
    (r'z[uü]beyir\s*karahan', 'ZübeyirKarahan'),
    (r'iklim\s*[sş]evval\s*duman', 'İklimŞevvalDuman')
]


def generate_smart_tags(haber):
    """
    Bir haber nesnesinden veya sözlüğünden akıllı taglar üretir.
    Başlık ve spot öncelikli, semantik eşleme yapar.
    En az 3, en fazla 7 benzersiz hashtag döndürür.
    """
    if not haber:
        return ["#Spor24", "#Haber"]

    baslik = (
        getattr(haber, 'ozgun_baslik', None) or 
        getattr(haber, 'baslik', '') or 
        (haber.get('title') if isinstance(haber, dict) else '') or ''
    )
    raw_baslik = getattr(haber, 'baslik', '') if hasattr(haber, 'baslik') else ''
    
    ozet = (
        getattr(haber, 'ozgun_ozet', None) or
        getattr(haber, 'ozet', '') or
        (haber.get('summary') if isinstance(haber, dict) else '') or ''
    )
    
    icerik = (
        getattr(haber, 'ozgun_icerik', None) or 
        getattr(haber, 'icerik', '') or 
        (haber.get('content') if isinstance(haber, dict) else '') or ''
    )
    
    kat_ad = ''
    if hasattr(haber, 'kategori') and haber.kategori:
        kat_ad = haber.kategori.ad
    elif isinstance(haber, dict):
        kat_ad = haber.get('category_name') or haber.get('category') or ''

    fed_ad = ''
    if hasattr(haber, 'federasyon_website') and haber.federasyon_website:
        fed_ad = haber.federasyon_website.ad

    # 1. Başlık ve spot metni (Yüksek öncelik)
    headline_text = turkish_lower(f"{baslik} {raw_baslik} {ozet}")
    
    # 2. Gövde ve federasyon dahil tam metin
    full_text = turkish_lower(f"{baslik} {raw_baslik} {kat_ad} {fed_ad} {ozet} {icerik[:2000]}")

    priority_tags = []
    normal_tags = []

    # 1. Kategori / Branş Tagı (Öncelikli)
    if kat_ad:
        clean_kat = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]', '', kat_ad)
        if clean_kat:
            priority_tags.append(f"#{clean_kat}")

    # 2. Branş Sözlüğü (Başlıkta geçiyorsa öncelikli)
    for keyword, tag_name in SPOR_BRANSLARI.items():
        tag = f"#{tag_name}"
        if keyword in headline_text:
            if tag not in priority_tags:
                priority_tags.append(tag)
        elif keyword in full_text:
            if tag not in normal_tags and tag not in priority_tags:
                normal_tags.append(tag)

    # 3. Lokasyonlar (Şehirler / Ülkeler)
    for city_key, city_name in SEHIRLER.items():
        tag = f"#{city_name}"
        if re.search(r'\b' + city_key + r'\b', headline_text, re.IGNORECASE):
            if tag not in priority_tags:
                priority_tags.append(tag)
        elif re.search(r'\b' + city_key + r'\b', full_text, re.IGNORECASE):
            if tag not in normal_tags and tag not in priority_tags:
                normal_tags.append(tag)

    # 4. Turnuva, Madalya ve Organizasyon Terimleri
    for pattern, tag_name in ORGANIZASYONLAR:
        tag = f"#{tag_name}"
        if re.search(pattern, headline_text, re.IGNORECASE):
            if tag not in priority_tags:
                priority_tags.append(tag)
        elif re.search(pattern, full_text, re.IGNORECASE):
            if tag not in normal_tags and tag not in priority_tags:
                normal_tags.append(tag)

    # 5. Kişiler & Sporcular
    for pattern, person_name in ONEMLI_ISIMLER:
        tag = f"#{person_name}"
        if re.search(pattern, headline_text, re.IGNORECASE):
            if tag not in priority_tags:
                priority_tags.append(tag)
        elif re.search(pattern, full_text, re.IGNORECASE):
            if tag not in normal_tags and tag not in priority_tags:
                normal_tags.append(tag)

    # Listeleri birleştir: Başlık/kategori etiketleri önde
    all_tags = []
    for t in priority_tags + normal_tags:
        if t not in all_tags:
            all_tags.append(t)

    # Kurumsal Marka Tagı
    if '#Spor24' not in all_tags:
        all_tags.append('#Spor24')

    return all_tags[:7]


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
