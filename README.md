# SPOR24.NET — Dijital Spor Medyası & Mobil Mimari Altyapısı

> Türkiye'nin 44 resmi spor federasyonunu, bağımsız branşlarını ve canlı spor gündemini tek bir çatı altında toplayan otonom medya platformu.

---

## 📱 Google Stitch & Mobil Uygulama Entegrasyonu

Bu depo, Google Stitch ve mobil uygulama geliştiricileri için Spor24'ün tüm veri modellerini, canlı API entegrasyonlarını ve arayüz sözleşmelerini eksiksiz sunar.

### 🎨 Tasarım Dili & Tema
- **Tema:** Dark Mode / Ultra Koyu Modern Spor Medyası
- **Arka Plan:** \#0B0E14\ (Koyu grafit), Kart Yüzeyleri: \#111827\ ve \#1F2937\
- **Vurgu Renkleri:**
  - Canlı Kırmızı (Brand Red): \#E11D48\
  - Altın / Amber: \#F59E0B\ (Okunma sayısı ve başarı rozetleri)
  - Zümrüt Yeşili: \#10B981\ (Canlı veri akışı ve başarı göstergeleri)
  - Kobalt Mavi: \#3B82F6\ (Federasyon bağlantıları)

### 📲 Mobil Navigasyon Mimarisi (Bottom Navigation)
1. **Anasayfa:** Son dakika bandı, dokunmatik dev manşet slider'ı, grid haber kartları akışı.
2. **Federasyonlar & Branşlar:** 44 resmi federasyon (Boks, Güreş, Karate, Bisiklet, vb.) akış havuzu, anlık filtreleme çipleri.
3. **Spor24 Web TV:** 1080p kesintisiz video oynatıcı kartı ve günlük yayın akışı listesi.
4. **Köşe Yazarları:** Yazar avatarları, köşe yazıları ve derinlemesine spor analizleri.
5. **İstatistik & Profil:** Editoryal zeka, anlık okunma nabzı ve kullanıcı ayarları.

---

## ⚡ Canlı REST API Referansı

Mobil uygulamanın canlıda haber çekebileceği üretim uçları:

| Uç Nokta (Endpoint) | Metot | Açıklama |
| :--- | :--- | :--- |
| \https://spor24.net/api/news/\ | GET | Sayfalanmış canlı haber akışı (\esults\, \
ext\, \previous\) |
| \https://spor24.net/api/news/?category={ad}\ | GET | Belirli bir branşa / federasyona göre filtrelenmiş haberler |
| \https://spor24.net/api/news/?search={kelime}\ | GET | Anlık haber içi metin araması |
| \https://spor24.net/api/categories/\ | GET | 44 Federasyon ve 48 spor branşının haber sayılarıyla listesi |
| \https://spor24.net/api/columnists/\ | GET | Aktif köşe yazarları ve son yayınlanan makaleleri |
| \https://spor24.net/post.html?id={id}\ | GET | Haber detay sayfası ve görsel galerisi |
| \https://spor24.net/video/\ | GET | Spor24 TV canlı yayın akışı |

---

## 🗄️ Temel Veri Modelleri (haberler/models.py)

- **\Haber\**: Başlık, özet, detaylı HTML içerik, 16:9 kapak görseli, kategori ilişkisi, görüntülenme sayısı (\goruntulenme_sayisi\), yayın tarihi, SHA-256 dijital tescil mührü (\Content ID\).
- **\Kategori\**: Spor dalları (Futbol, Basketbol, Voleybol, Muay Thai, Hentbol, Boks, Bisiklet, vb.).
- **\FederasyonWebsite\**: 44 resmi federasyonun portal adresleri, otomatik veri çekme durumları ve havuz istatistikleri.
- **\Yazar\ & \KoseYazisi\**: Köşe yazarları, profil fotoğrafları, biyografileri ve makaleleri.
- **\ZiyaretLog\**: KVKK uyumlu, salted SHA-256 IP hash'li çift motorlu hibrit analitik kayıtları.

---

## 🚀 Yerel Kurulum (Geliştirici Ortamı)

\\\ash
# 1. Depoyu klonlayın
git clone https://github.com/Antknight06/spor24-platform.git
cd spor24-platform

# 2. Sanal ortamı kurun ve paketleri yükleyin
python -m venv venv
source venv/bin/activate  # Windows için: venv\\Scripts\\activate
pip install -r requirements.txt

# 3. Veritabanını oluşturun ve sunucuyu başlatın
python manage.py migrate
python manage.py runserver
\\\

---
© 2026 SPOR24.NET — Tüm Hakları Saklıdır.
