# haberler/urls.py
from django.urls import path
from . import views
from . import views_auth
from . import views_engagement
from . import views_whatsapp

app_name = 'haberler'

urlpatterns = [
    path('kose-yazilari/', views.kose_yazilari_listesi, name='kose-yazilari-listesi'),
    # Authentication URLs
    path('login/', views_auth.custom_login, name='custom_login'),
    path('logout/', views_auth.custom_logout, name='custom_logout'),
    path('register/', views_auth.register, name='register'),
    # === YENİ EKLENECEK SATIR ===
    path('v3/', views.anasayfa_v3, name='anasayfa_v3'),
    path('reklam-proxy/', views.reklam_proxy, name='reklam_proxy'),
    path('verify-email/<str:user_email>/', views_auth.verify_email, name='verify_email'),
    # ============================
    path('validate-email/', views_auth.validate_email_ajax, name='validate_email_ajax'),
    
    # Dashboard URLs
    path('admin-dashboard/', views_auth.admin_dashboard, name='admin_dashboard'),
    path('yetkili-dashboard/', views_auth.yetkili_dashboard, name='yetkili_dashboard'),
    path('abone-dashboard/', views_auth.abone_dashboard, name='abone_dashboard'),
    
    # Subscriber function URLs
    path('favori-haberler/', views_auth.favori_haberler, name='favori_haberler'),
    path('yorumlarim/', views_auth.yorumlarim, name='yorumlarim'),
    path('profil-ayarlari/', views_auth.profil_ayarlari, name='profil_ayarlari'),
    path('haber-ekle-favori/<int:haber_id>/', views_auth.haber_ekle_favori, name='haber_ekle_favori'),
    path('haber-kaldir-favori/<int:favori_id>/', views_auth.haber_kaldir_favori, name='haber_kaldir_favori'),
    path('haber-kaldir-favori-by-haber/<int:haber_id>/', views_auth.haber_kaldir_favori_by_haber, name='haber_kaldir_favori_by_haber'),
    
    # Comment URLs
    path('yorum-ekle/<int:haber_id>/', views_auth.yorum_ekle, name='yorum_ekle'),
    path('yorum-yanitla/<int:yorum_id>/', views_auth.yorum_yanitla, name='yorum_yanitla'),
    
    # Author function URLs
    path('haber-favori-goruntule/<int:haber_id>/', views_auth.haber_favori_goruntule, name='haber_favori_goruntule'),
    
    # Opinion article URLs for authorized users
    path('yeni-kose-yazisi/', views_auth.yeni_kose_yazisi, name='yeni_kose_yazisi'),
    path('kose-yazisi-duzenle/<int:haber_id>/', views_auth.kose_yazisi_duzenle, name='kose_yazisi_duzenle'),
    path('kose-yazilarim/', views_auth.kose_yazilarim, name='kose_yazilarim'),
    
    # News article URLs for authorized users
    path('yeni-haber/', views_auth.yeni_haber, name='yeni_haber'),
    path('haber-duzenle/<int:haber_id>/', views_auth.haber_duzenle, name='haber_duzenle'),
    path('haberlerim/', views_auth.haberlerim, name='haberlerim'),
    
    # Pending yetkili news URLs
    path('bekleyen-yetkili-haberlerim/', views_auth.bekleyen_yetkili_haberlerim, name='bekleyen_yetkili_haberlerim'),
    path('bekleyen-yetkili-haber/<int:haber_id>/', views_auth.bekleyen_yetkili_haber_detay, name='bekleyen_yetkili_haber_detay'),
    
    # Other dashboard actions (placeholders)
    path('yorum-yonetimi/', views_auth.yorum_yonetimi, name='yorum_yonetimi'),
    path('istatistikler/', views_auth.istatistikler, name='istatistikler'),
    path('galeri/', views_auth.galeri, name='galeri'),
    
    # Search URL
    path('arama/', views.haber_arama, name='haber_arama'),
    
    # === Statik Sayfa URL'leri ===  <--- BURAYA TAŞIDIK
    path('hakkimizda/', views.hakkimizda, name='hakkimizda'),
    path('kunye/', views.kunye, name='kunye'),
    path('iletisim/', views.iletisim, name='iletisim'),
    path('gizlilik-politikasi/', views.gizlilik_politikasi, name='gizlilik_politikasi'),
    path('kullanim-sartlari/', views.kullanim_sartlari, name='kullanim_sartlari'),
    path('videolar/', views.video_sayfasi, name='video_sayfasi'), # <--- BU SATIRI EKLEYİN
    # ==========================
    # Karate Bölümü URL'leri
    path('karate/antrenorler/', views.karate_antrenorler, name='karate_antrenorler'),
    path('karate/kulupler/', views.karate_kulupler, name='karate_kulupler'),
    path('karate-formlari/', views.karate_formlari, name='karate_formlari'),

    # Kategori URL'i (Statiklerden sonra, genelden önce iyi bir yer)
    path('kategori/<str:slug>/', views.kategori_haberler, name='kategori_haberler'),

    # Etkileşim (Engagement) URL'leri
    path('anket/<int:poll_id>/oy/', views_engagement.vote_poll, name='poll_vote'),
    path('anket-oyla/<int:poll_id>/', views_engagement.vote_poll, name='vote_poll'),
    path('yarismalar/', views_engagement.quiz_list, name='quiz_list'),
    path('yarisma/<int:quiz_id>/', views_engagement.quiz_detail, name='quiz_detail'),
    path('yarisma-kaydet/<int:quiz_id>/', views_engagement.submit_quiz, name='submit_quiz'),

    # API endpoints for Raspberry Pi 4 Scraper Worker
    path('api/v1/federasyonlar/', views.api_federasyonlar, name='api_federasyonlar'),
    path('api/v1/bekleyen-haber-ekle/', views.api_bekleyen_haber_ekle, name='api_bekleyen_haber_ekle'),
    path('api/v1/bekleyen-sosyal-medya-ekle/', views.api_bekleyen_sosyal_medya_ekle, name='api_bekleyen_sosyal_medya_ekle'),
    path('api/telegram/webhook/', views.telegram_webhook, name='api_telegram_webhook'),
    path('api/whatsapp/channel-share/<int:news_id>/', views_whatsapp.api_whatsapp_channel_share, name='api_whatsapp_channel_share'),

    # Authors & Newsletter URLs
    path('yazarlar/', views.yazarlar_listesi, name='yazarlar_listesi'),
    path('yazar/<str:username>/', views.yazar_detay, name='yazar_detay'),
    path('bulten-abone-ekle/', views.bulten_olustur, name='bulten_olustur'),

    # Generic patterns EN SONDA olmalı
    path('', views.haber_listesi, name='haber_listesi'), # Ana sayfa (eğer varsa, yoksa haber listesi)
    path('<str:slug>/', views.haber_detay, name='haber_detay'), # Haber detayları en sonda denenmeli
]
