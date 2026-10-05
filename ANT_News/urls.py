"""
URL configuration for ANT_News project.
"""
from django.contrib import admin
from haberler.sitemaps import StaticViewSitemap, HaberSitemap, KategoriSitemap, YazarSitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from haberler import views
from . import views as main_views
from haberler import admin_views
from haberler import views_seo
from django.http import HttpResponse

sitemaps = {
    'haberler': HaberSitemap,
    'kategoriler': KategoriSitemap,
    'yazarlar': YazarSitemap,
    'static': StaticViewSitemap,
}

from haberler import views_engagement
from haberler import views_analytics
from haberler import views_linkcheck
from haberler import views_whatsapp
from haberler import views_airtag

urlpatterns = [
    # AirTag & Shortlink Tracking System
    path('c/<int:news_id>/', views_airtag.airtag_redirect, name='airtag_redirect_short'),
    path('c/<str:content_id>/', views_airtag.airtag_redirect, name='airtag_redirect_code'),
    path('api/tags/<str:tag_name>/', views_airtag.api_tag_news, name='api_tag_news'),

    path('ads.txt', lambda r: HttpResponse("google.com, pub-4099153035746180, DIRECT, f08c47fec0942fa0", content_type="text/plain")),
    path('OneSignalSDKWorker.js', lambda r: HttpResponse('importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");', content_type='application/javascript')),
    path('robots.txt', views_seo.custom_robots_txt, name='robots_txt'),
    path('sitemap.xml', views_seo.clean_sitemap_view, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap-news.xml', views_seo.google_news_sitemap, name='google_news_sitemap'),
    path('google-news.xml', views_seo.google_news_sitemap, name='google_news_sitemap_alt'),
    path('rss.xml', views_seo.news_rss_feed, name='news_rss_feed'),
    path('feed/', views_seo.news_rss_feed, name='news_feed'),
    path('admin/check-new-news/', main_views.check_new_news, name='check_new_news'),
    path('boxing-test/', main_views.boxing_test, name='boxing_test'),
    path('admin/permission-matrix/', admin_views.permission_matrix, name='permission_matrix'),
    path('admin/scraper-control/', admin_views.scraper_control, name='scraper_control'),
    path('api/news/', views.api_news, name='api_news'),
    path('api/news/<int:news_id>/', views.api_news_detail, name='api_news_detail'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/columnists/', views.api_columnists, name='api_columnists'),
    path('api/whatsapp/channel-share/<int:news_id>/', views_whatsapp.api_whatsapp_channel_share, name='api_whatsapp_channel_share_root'),
    path('api/analytics/track/', views_analytics.api_analytics_track, name='api_analytics_track'),
    path('api/analytics/stats/', views_analytics.api_analytics_stats, name='api_analytics_stats'),
    path('api/news/log_activity/', views_analytics.api_analytics_track, name='api_log_activity'),
    path('anket/<int:poll_id>/oy/', views_engagement.vote_poll, name='vote_poll_root'),
    path('istatistik.html', views_analytics.istatistik_view, name='istatistik_html'),
    path('istatistik/', views_analytics.istatistik_view, name='istatistik_page'),
    path('istatistik/index.html', views_analytics.istatistik_view),
    path('post.html', views.v3_post, name='post_html'),
    path('v3/post.html', views.v3_post, name='v3_post_html'),
    path('admin/post.html', views.v3_post, name='admin_post_html'),
    path('admin/haberler/post.html', views.v3_post, name='admin_haberler_post_html'),
    path('api/telegram/webhook/', views.telegram_webhook, name='telegram_webhook_root'),
    path('admin/linkcheck/custom-action/', views_linkcheck.linkcheck_action, name='linkcheck_custom_action'),
    path('admin/linkcheck/', include('linkcheck.urls')),
    path('admin/', admin.site.urls),
    path('yazar/<str:username>/', views.yazar_detay, name='yazar_detay_root'),
    path('yetkili-giris/', views.yetkili_giris, name='yetkili_giris_root'),
    path('cikis/', views.custom_logout, name='custom_logout_root'),
    path('yazarlar/', views.yazarlar_listesi, name='yazarlar_listesi_root'),
    path('kategori/<str:slug>/', views.kategori_haberler, name='kategori_haberler_root'),
    path('arama/', views.haber_arama, name='haber_arama_root'),
    path('hakkimizda/', views.hakkimizda, name='hakkimizda_root'),
    path('kunye/', views.kunye, name='kunye_root'),
    path('iletisim/', views.iletisim, name='iletisim_root'),
    path('gizlilik-politikasi/', views.gizlilik_politikasi, name='gizlilik_politikasi_root'),
    path('kullanim-sartlari/', views.kullanim_sartlari, name='kullanim_sartlari_root'),
        path('haber/<str:slug>/', views.haber_detay, name='haber_detay_singular'),
    path('haberler/', include('haberler.urls')),
    path('', views.anasayfa, name='anasayfa'),
    path('v2/', views.anasayfa_v2, name='anasayfa_v2'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
