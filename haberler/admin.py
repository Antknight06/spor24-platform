from django.utils.safestring import mark_safe
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib import messages
from django.db import models
from django.shortcuts import render, redirect
from django.utils.html import format_html
from .models import Kategori, Haber, FederasyonWebsite, BekleyenHaber, BekleyenYetkiliHaberi, TaramaLog, Ad, Reklam, Kunye
from django.views.decorators.csrf import csrf_exempt


def make_image_preview(obj, width="100%", max_height="320px"):
    from urllib.parse import urljoin
    img_url = None
    if getattr(obj, 'resim', None):
        try:
            if obj.resim and obj.resim.url:
                img_url = obj.resim.url
        except Exception:
            pass
    if not img_url and getattr(obj, 'kaynak_resim_url', None):
        raw_img = obj.kaynak_resim_url.strip()
        if raw_img and not raw_img.startswith(('http://', 'https://', '/media/')):
            kaynak_url = getattr(obj, 'kaynak_url', '')
            if kaynak_url:
                raw_img = urljoin(kaynak_url, raw_img)
        img_url = raw_img

    if not img_url:
        return format_html(
            '<div style="padding: 12px 16px; border-radius: 8px; background: rgba(255,255,255,0.05); color: #94a3b8; font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; gap: 8px;">'
            '<span>📷</span><span>Görsel henüz yüklenmemiş veya URL belirtilmemiş.</span>'
            '</div>'
        )

    return format_html(
        '<div style="margin: 8px 0 16px 0; max-width: 520px; border-radius: 12px; overflow: hidden; border: 2px solid #3b82f6; box-shadow: 0 8px 24px rgba(0,0,0,0.3); background: #0f172a;">'
        '<img src="{}" style="width: {}; max-height: {}; object-fit: cover; display: block;" onerror="this.onerror=null;this.src=\'/static/img/logo_5.png\';" />'
        '<div style="background: #1e293b; color: #cbd5e1; font-size: 11px; padding: 8px 14px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.1);">'
        '<span style="font-weight: 700; color: #38bdf8; display: inline-flex; align-items: center; gap: 4px;">📸 Canlı Görsel Önizleme</span>'
        '<a href="{}" target="_blank" style="color: #60a5fa; text-decoration: underline; font-weight: bold;">Tam Boyutta Aç ↗</a>'
        '</div>'
        '</div>',
        img_url, width, max_height, img_url
    )


def make_live_card_preview(obj):
    if not obj or not getattr(obj, 'id', None):
        return format_html(
            '<div style="padding: 16px; border-radius: 12px; background: #1e293b; color: #94a3b8; font-size: 13px;">'
            'ℹ️ Haber kaydedildikten sonra burada canlı ana sayfa kart simülasyonu görüntülenecektir.'
            '</div>'
        )

    # 1. Resolve Image
    img_url = ''
    if getattr(obj, 'resim', None):
        try:
            if obj.resim and obj.resim.url:
                img_url = obj.resim.url
        except Exception:
            pass
    if not img_url and getattr(obj, 'kaynak_resim_url', None):
        raw_img = obj.kaynak_resim_url.strip()
        if raw_img and not raw_img.startswith(('http://', 'https://', '/media/')):
            kaynak_url = getattr(obj, 'kaynak_url', '')
            if kaynak_url:
                raw_img = urljoin(kaynak_url, raw_img)
        img_url = raw_img
    if not img_url and getattr(obj, 'federasyon_website', None) and getattr(obj.federasyon_website, 'logo', None):
        try:
            img_url = obj.federasyon_website.logo.url
        except Exception:
            pass
    if not img_url:
        img_url = '/static/img/logo_5.png'

    # 2. Resolve Category & Badge Color
    kategori_ad = 'GÜNCEL'
    if getattr(obj, 'kategori', None) and obj.kategori:
        kategori_ad = obj.kategori.ad.upper()
    elif getattr(obj, 'federasyon_website', None) and obj.federasyon_website:
        kategori_ad = obj.federasyon_website.ad.upper()

    color_map = {
        'KARATE': '#ef4444',
        'BOKS': '#dc2626',
        'KİCK BOKS': '#b91c1c',
        'TAEKWONDO': '#2563eb',
        'GÜREŞ': '#1d4ed8',
        'JUDO': '#16a34a',
        'WUSHU KUNGFU': '#d97706',
        'VOLEYBOL': '#ea580c',
        'OKÇULUK': '#0284c7',
        'BİLARDO': '#7c3aed',
        'CİMNASTİK': '#db2777',
        'INSTAGRAM': '#e1306c',
        'TWITTER': '#1da1f2',
        'X': '#0f172a',
        'FACEBOOK': '#1877f2',
        'YOUTUBE': '#ff0000',
    }
    badge_bg = '#ef4444'
    for k, c in color_map.items():
        if k in kategori_ad:
            badge_bg = c
            break

    # 3. Format Date
    dt = getattr(obj, 'haber_tarihi', None) or getattr(obj, 'olusturma_tarihi', None) or getattr(obj, 'paylasim_tarihi', None)
    date_str = dt.strftime('%d.%m.%Y %H:%M') if dt else 'Tarih Belirtilmedi'

    baslik = getattr(obj, 'baslik', '') or 'Başlık Yok'
    ozet = getattr(obj, 'ozet', '') or ''
    if not ozet and getattr(obj, 'icerik', None):
        ozet = obj.icerik[:140] + '...'

    # 4. Live Link if published
    live_link_btn = ''
    if getattr(obj, 'yayinlandi', False):
        live_link_btn = f'''
        <a href="https://spor24.net/post.html?id={obj.id}" target="_blank" 
           style="display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; padding: 7px 16px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 700; margin-top: 10px; width: fit-content;">
           <span>🌐 Canlı Sitede Gör</span> <span style="font-size: 14px;">↗</span>
        </a>
        '''

    return format_html(
        '''
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 16px; padding: 20px; margin-bottom: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">📱</span>
                    <strong style="font-size: 15px; color: #60a5fa; letter-spacing: 0.5px;">SPOR24 ANA SAYFA KART SİMÜLATÖRÜ</strong>
                </div>
                <span style="font-size: 11px; background: rgba(59, 130, 246, 0.2); color: #93c5fd; padding: 4px 10px; border-radius: 20px; font-weight: 600; border: 1px solid rgba(59, 130, 246, 0.3);">
                    Canlı Önizleme
                </span>
            </div>

            <div style="display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start;">
                <!-- KART ÖNİZLEMESİ (Ana sayfadaki 4 sütunlu kart ile %100 aynı) -->
                <div style="width: 310px; max-width: 100%; border-radius: 12px; overflow: hidden; background: #ffffff; box-shadow: 0 8px 20px rgba(0,0,0,0.3); border: 1px solid #e2e8f0; flex-shrink: 0;">
                    <div style="position: relative; width: 100%; height: 185px; background: #0f172a; overflow: hidden;">
                        <span style="position: absolute; top: 10px; left: 10px; z-index: 2; background: {badge_bg}; color: #ffffff; font-size: 10px; font-weight: 800; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 2px 6px rgba(0,0,0,0.4);">
                            {kategori_ad}
                        </span>
                        <img src="{img_url}" alt="Önizleme" style="width: 100%; height: 100%; object-fit: cover; display: block;" onerror="this.onerror=null;this.src='/static/img/logo_5.png';" />
                    </div>
                    <div style="padding: 14px 16px; background: #ffffff;">
                        <div style="font-size: 11px; color: #64748b; margin-bottom: 8px; font-weight: 500; display: flex; align-items: center; gap: 5px;">
                            <span>🕒</span> <span>{date_str}</span>
                        </div>
                        <h4 style="font-size: 13px; font-weight: 800; color: #0f172a; line-height: 1.35; margin: 0 0 8px 0; max-height: 54px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">
                            {baslik}
                        </h4>
                        <p style="font-size: 11px; color: #475569; line-height: 1.45; margin: 0; max-height: 48px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">
                            {ozet}
                        </p>
                    </div>
                </div>

                <!-- BİLGİ & METRİK PANELİ -->
                <div style="flex: 1; min-width: 250px; display: flex; flex-direction: column; gap: 12px; background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);">
                    <div style="font-size: 13px; font-weight: 700; color: #e2e8f0; margin-bottom: 4px;">
                        📌 Kart Yayın Durumu & Analiz:
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; line-height: 1.8;">
                        <div>• <strong>Görsel Kaynağı:</strong> <span style="color: #38bdf8;">{img_source}</span></div>
                        <div>• <strong>Başlık Uzunluğu:</strong> <span style="color: #fbbf24;">{title_len} karakter</span> ({title_status})</div>
                        <div>• <strong>Özet / Spot:</strong> <span style="color: #a78bfa;">{summary_len} karakter</span></div>
                        <div>• <strong>Yayın Tarihi:</strong> <span style="color: #34d399;">{date_str}</span></div>
                    </div>
                    {live_link_btn}
                </div>
            </div>
        </div>
        ''',
        badge_bg=badge_bg,
        kategori_ad=kategori_ad,
        img_url=img_url,
        date_str=date_str,
        baslik=baslik,
        ozet=ozet,
        img_source=('Yerel Dosya' if getattr(obj, 'resim', None) else ('Kaynak Web URL' if getattr(obj, 'kaynak_resim_url', None) else 'Varsayılan Logo')),
        title_len=len(baslik),
        title_status=('İdeal Uzunluk' if 30 <= len(baslik) <= 90 else ('Çok Uzun' if len(baslik) > 90 else 'Kısa')),
        summary_len=len(ozet),
        live_link_btn=mark_safe(live_link_btn)
    )



@admin.register(FederasyonWebsite)
class FederasyonWebsiteAdmin(ModelAdmin):
    list_display = ['ad', 'ana_url', 'aktif', 'son_tarama', 'instagram_url', 'facebook_url', 'x_url', 'youtube_url']
    list_filter = ['aktif', 'son_tarama']
    search_fields = ['ad', 'ana_url']
    list_editable = ['aktif']
    readonly_fields = ['son_tarama', 'son_yeni_haber_zamani']
    actions = ['scrape_selected_social', 'scrape_selected_web']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        active_cnt = FederasyonWebsite.objects.filter(aktif=True).count()
        total_cnt = FederasyonWebsite.objects.count()
        messages.info(
            request,
            format_html(
                '<strong style="font-size: 15px; color: #111;">📊 BRANŞ & FEDERASYON SEÇİM DURUMU:</strong> '
                '<span style="background:#28a745; color:#fff; padding: 4px 12px; border-radius: 20px; font-weight: bold; margin-left: 8px;">🟢 Haber Çekilen Seçili (Aktif): {} / {}</span> '
                '<span style="background:#6c757d; color:#fff; padding: 4px 12px; border-radius: 20px; font-weight: bold; margin-left: 5px;">⚪ Pasif (Devre Dışı): {}</span>',
                active_cnt, total_cnt, total_cnt - active_cnt
            )
        )
        return super().changelist_view(request, extra_context=extra_context)
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('ad', 'ana_url', 'haberler_url', 'aktif')
        }),
        ('Sosyal Medya Hesapları', {
            'fields': ('instagram_url', 'facebook_url', 'x_url', 'youtube_url')
        }),
        ('CSS Selectorlar', {
            'fields': (
                'haber_listesi_selector',
                'haber_baslik_selector', 
                'haber_link_selector',
                'haber_tarih_selector',
                'haber_ozet_selector'
            ),
            'description': 'Haber cekmek icin kullanilacak CSS selectorlari belirtin'
        }),
        ('Durum', {
            'fields': ('son_tarama', 'son_yeni_haber_zamani')
        }),
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('toggle-aktif/', self.admin_site.admin_view(self.toggle_aktif), name='haberler_federasyonwebsite_toggle_aktif'),
            path('toggle-all-aktif/', self.admin_site.admin_view(self.toggle_all_aktif), name='haberler_federasyonwebsite_toggle_all_aktif'),
        ]
        return custom_urls + urls

    def toggle_aktif(self, request):
        from django.http import JsonResponse
        import json
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                website_id = data.get('website_id')
                aktif_state = data.get('aktif', True)
                if website_id:
                    FederasyonWebsite.objects.filter(id=website_id).update(aktif=aktif_state)
                    return JsonResponse({'status': 'success', 'website_id': website_id, 'aktif': aktif_state})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'invalid method'}, status=405)

    def toggle_all_aktif(self, request):
        from django.http import JsonResponse
        import json
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                aktif_state = data.get('aktif', True)
                website_ids = data.get('website_ids', [])
                
                if website_ids:
                    updated = FederasyonWebsite.objects.filter(id__in=website_ids).update(aktif=aktif_state)
                else:
                    updated = FederasyonWebsite.objects.all().update(aktif=aktif_state)
                    
                return JsonResponse({'status': 'success', 'updated_count': updated, 'aktif': aktif_state})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'invalid method'}, status=405)


    def scrape_selected_social(self, request, queryset):
        from django.core.management import call_command
        import threading
        
        ids_str = ",".join([str(x.id) for x in queryset])
        
        def run_scrape():
            try:
                call_command('tarama_sosyal_medya', federation_ids=ids_str)
            except Exception as e:
                print(f"Admin trigger social scrape error: {e}")
                
        threading.Thread(target=run_scrape).start()
        self.message_user(
            request, 
            f"Seçilen {queryset.count()} federasyon için sosyal medya taraması arka planda başlatıldı.", 
            level='info'
        )
    scrape_selected_social.short_description = "Seçilen federasyonların Sosyal Medyasını tara"

    def scrape_selected_web(self, request, queryset):
        from django.core.management import call_command
        import threading
        
        ids_str = ",".join([str(x.id) for x in queryset])
        
        def run_scrape():
            try:
                call_command('diger_federasyon_haberleri_cek', federation_ids=ids_str, limit=5)
            except Exception as e:
                print(f"Admin trigger web scrape error: {e}")
                
        threading.Thread(target=run_scrape).start()
        self.message_user(
            request, 
            f"Seçilen {queryset.count()} federasyon için web haber taraması arka planda başlatıldı.", 
            level='info'
        )
    scrape_selected_web.short_description = "Seçilen federasyonların Resmi Web Sitelerini tara"


@admin.register(Kategori)
class KategoriAdmin(ModelAdmin):
    list_display = ['ad', 'federasyon_website', 'olusturma_tarihi']
    list_filter = ['federasyon_website', 'olusturma_tarihi']
    prepopulated_fields = {'slug': ('ad',)}
    search_fields = ['ad']

@admin.register(Haber)
class HaberAdmin(ModelAdmin):
    list_display = ['baslik', 'kategori', 'yazar', 'haber_tarihi', 'goruntulenme_sayisi', 'haber_degeri_skoru', 'yayinlandi', 'manset_haberi', 'manset_sabitlendi']
    list_filter = ['kategori', 'federasyon_website', 'otomatik_eklendi', 'yayinlandi', 'manset_haberi', 'anasayfa_haberi', 'kose_yazisi', 'olusturma_tarihi', 'haber_tarihi']
    search_fields = ['baslik', 'icerik', 'kaynak_url']
    prepopulated_fields = {'slug': ('baslik',)}
    list_editable = ['haber_tarihi', 'yayinlandi', 'manset_haberi', 'manset_sabitlendi']
    date_hierarchy = 'haber_tarihi'
    readonly_fields = ['canli_kart_onizleme', 'kaynak_url', 'otomatik_eklendi', 'goruntulenme_sayisi', 'gorsel_onizleme']
    actions = ['fix_news_dates', 'update_photos_and_dates', 'delete_selected_items']
    ordering = ['-haber_tarihi', '-olusturma_tarihi'] 
    
    def canli_kart_onizleme(self, obj):
        return make_live_card_preview(obj)
    canli_kart_onizleme.short_description = "Haber Kartı Canlı Simülasyonu"

    def gorsel_onizleme(self, obj):
        return make_image_preview(obj)
    gorsel_onizleme.short_description = "Haber Görseli Önizleme"

    def delete_selected_items(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"🗑️ Seçilen {count} adet haber kalıcı olarak silindi.", level='success')
    delete_selected_items.short_description = "🗑️ Seçili haberleri tamamen sil"

    fieldsets = (
        ('📱 Canlı Kart Görsel Önizleme', {
            'fields': ('canli_kart_onizleme',),
            'description': 'Haberin SPOR24.NET ana sayfasında ziyaretçilere nasıl görüneceğinin canlı simülasyonu.'
        }),
        ('Temel Bilgiler', {
            'fields': ('baslik', 'slug', 'kategori', 'yazar', 'haber_tarihi')
        }),
        ('Icerik & Görsel', {
            'fields': ('resim', 'ozet', 'icerik')
        }),
        ('Kaynak Bilgileri', {
            'fields': ('kaynak_url', 'federasyon_website', 'otomatik_eklendi'),
            'classes': ('collapse',)
        }),
        ('Yayin Ayarlari', {
            'fields': ('yayinlandi', 'manset_haberi', 'anasayfa_haberi', 'kose_yazisi', 'goruntulenme_sayisi')
        }),
    )
    
    def fix_news_dates(self, request, queryset):
        """Seçili haberlerin tarihlerini kaynak URL'den otomatik düzelt"""
        import requests
        from bs4 import BeautifulSoup
        import re
        from datetime import datetime
        from django.utils import timezone
        
        fixed_count = 0
        error_count = 0
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for haber in queryset:
            if not haber.kaynak_url:
                continue
                
            try:
                # URL'den tarih çıkart
                url_tarih_pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
                match = re.search(url_tarih_pattern, haber.kaynak_url)
                
                if match:
                    yil, ay, gun = match.groups()
                    try:
                        yeni_tarih = datetime(int(yil), int(ay), int(gun))
                        yeni_tarih = timezone.make_aware(yeni_tarih)
                        
                        # Mevcut tarihle karşılaştır
                        if haber.haber_tarihi != yeni_tarih:
                            eski_tarih = haber.haber_tarihi
                            haber.haber_tarihi = yeni_tarih
                            haber.save()
                            fixed_count += 1
                            
                            self.message_user(
                                request, 
                                f"✅ '{haber.baslik[:50]}...' tarihi güncellendi: {eski_tarih} → {yeni_tarih}",
                                level='success'
                            )
                    except ValueError:
                        error_count += 1
                        continue
                else:
                    # URL'de tarih yoksa, sayfadan çekmeye çalış
                    try:
                        response = requests.get(haber.kaynak_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Meta tag'lerden tarih
                            date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
                            if date_meta:
                                tarih_str = date_meta.get('content', '')
                                yeni_tarih = datetime.fromisoformat(tarih_str.replace('Z', '+00:00'))
                                
                                if haber.haber_tarihi != yeni_tarih:
                                    eski_tarih = haber.haber_tarihi
                                    haber.haber_tarihi = yeni_tarih
                                    haber.save()
                                    fixed_count += 1
                                    
                                    self.message_user(
                                        request, 
                                        f"✅ '{haber.baslik[:50]}...' tarihi meta tag'den güncellendi: {eski_tarih} → {yeni_tarih}",
                                        level='success'
                                    )
                    except Exception:
                        error_count += 1
                        continue
                        
            except Exception as e:
                error_count += 1
                self.message_user(
                    request, 
                    f"❌ '{haber.baslik[:50]}...' tarih düzeltme hatası: {e}",
                    level='error'
                )
        
        # Özet mesaj
        if fixed_count > 0:
            self.message_user(
                request, 
                f"🎉 Toplam {fixed_count} haberin tarihi başarıyla düzeltildi!",
                level='success'
            )
        
        if error_count > 0:
            self.message_user(
                request, 
                f"⚠️ {error_count} haberde tarih düzeltme hatası oluştu.",
                level='warning'
            )
            
        if fixed_count == 0 and error_count == 0:
            self.message_user(
                request, 
                "ℹ️ Düzeltilecek tarih bulunamadı. Tüm haberler güncel görünüyor.",
                level='info'
            )
    
    fix_news_dates.short_description = "📅 Seçili haberlerin tarihlerini otomatik düzelt"
    
    def update_photos_and_dates(self, request, queryset):
        """Seçili haberlerin fotoğraf ve tarihlerini güncelle"""
        import requests
        from bs4 import BeautifulSoup
        from PIL import Image
        import io
        import hashlib
        from django.core.files.base import ContentFile
        from urllib.parse import urljoin
        import re
        from datetime import datetime
        from django.utils import timezone
        
        updated_count = 0
        error_count = 0
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for haber in queryset:
            if not haber.kaynak_url:
                continue
                
            try:
                response = requests.get(haber.kaynak_url, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Tarih güncelleme
                tarih_guncellendi = False
                
                # URL'den tarih çıkart
                url_tarih_pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
                match = re.search(url_tarih_pattern, haber.kaynak_url)
                
                if match:
                    yil, ay, gun = match.groups()
                    try:
                        yeni_tarih = datetime(int(yil), int(ay), int(gun))
                        yeni_tarih = timezone.make_aware(yeni_tarih)
                        
                        if haber.haber_tarihi != yeni_tarih:
                            haber.haber_tarihi = yeni_tarih
                            tarih_guncellendi = True
                    except ValueError:
                        pass
                
                # Fotoğraf güncelleme
                foto_guncellendi = False
                
                # Fotoğraf URL'lerini bul
                foto_urls = []
                
                # WordPress post thumbnail
                post_thumbnail = soup.select_one('.post-thumbnail img')
                if post_thumbnail and post_thumbnail.get('src'):
                    foto_urls.append(post_thumbnail.get('src'))
                
                # Entry content içindeki ilk fotoğraf
                entry_img = soup.select_one('.entry-content img')
                if entry_img and entry_img.get('src'):
                    foto_urls.append(entry_img.get('src'))
                
                # Article içindeki fotoğraflar
                article_imgs = soup.select('article img')
                for img in article_imgs[:2]:
                    if img.get('src'):
                        foto_urls.append(img.get('src'))
                
                # Duplicate'ları temizle
                foto_urls = list(dict.fromkeys(foto_urls))
                
                for foto_url in foto_urls:
                    # Tam URL yap
                    if foto_url.startswith('/'):
                        base_url = '/'.join(haber.kaynak_url.split('/')[:3])
                        foto_url = urljoin(base_url, foto_url)
                    elif not foto_url.startswith('http'):
                        continue
                    
                    # Küçük fotoğrafları ve ikonları hariç tut
                    if any(skip in foto_url.lower() for skip in ['icon', 'logo', 'avatar', 'thumb-', 'banner', 'header']):
                        continue
                    
                    try:
                        foto_response = requests.get(foto_url, headers=headers, timeout=10)
                        if foto_response.status_code != 200 or len(foto_response.content) < 5000:
                            continue
                        
                        # PIL ile fotoğrafı kontrol et
                        image = Image.open(io.BytesIO(foto_response.content))
                        width, height = image.size
                        
                        if width < 200 or height < 150:
                            continue
                        
                        # RGB'ye çevir (gerekirse)
                        if image.mode in ('RGBA', 'LA', 'P'):
                            image = image.convert('RGB')
                        
                        # Fotoğrafı optimize et
                        max_width, max_height = 1200, 800
                        if image.width > max_width or image.height > max_height:
                            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                        
                        # Optimize edilmiş fotoğrafı kaydet
                        output = io.BytesIO()
                        image.save(output, format='JPEG', quality=90, optimize=True)
                        output.seek(0)
                        
                        # Dosya adı oluştur
                        slug_hash = hashlib.md5(haber.slug.encode()).hexdigest()[:8]
                        filename = f"{haber.kategori.slug}_{haber.slug[:25]}_{slug_hash}_updated.jpg"
                        
                        # Eski fotoğrafı sil (varsa)
                        if haber.resim:
                            try:
                                haber.resim.delete(save=False)
                            except:
                                pass
                        
                        # Yeni fotoğrafı kaydet
                        haber.resim.save(
                            filename,
                            ContentFile(output.getvalue()),
                            save=False
                        )
                        
                        foto_guncellendi = True
                        break  # İlk başarılı fotoğrafı kullan
                        
                    except Exception:
                        continue
                
                # Değişiklikleri kaydet
                if tarih_guncellendi or foto_guncellendi:
                    haber.save()
                    updated_count += 1
                    
                    updates = []
                    if tarih_guncellendi:
                        updates.append("📅 Tarih")
                    if foto_guncellendi:
                        updates.append("📷 Fotoğraf")
                    
                    self.message_user(
                        request, 
                        f"✅ '{haber.baslik[:40]}...' güncellendi: {', '.join(updates)}",
                        level='success'
                    )
                        
            except Exception as e:
                error_count += 1
                self.message_user(
                    request, 
                    f"❌ '{haber.baslik[:40]}...' güncelleme hatası: {e}",
                    level='error'
                )
        
        # Özet mesaj
        if updated_count > 0:
            self.message_user(
                request, 
                f"🎉 Toplam {updated_count} haber başarıyla güncellendi!",
                level='success'
            )
        
        if error_count > 0:
            self.message_user(
                request, 
                f"⚠️ {error_count} haberde güncelleme hatası oluştu.",
                level='warning'
            )
            
        if updated_count == 0 and error_count == 0:
            self.message_user(
                request, 
                "ℹ️ Güncellenecek içerik bulunamadı.",
                level='info'
            )
    
    update_photos_and_dates.short_description = "🔄 Seçili haberlerin fotoğraf ve tarihlerini güncelle"

@admin.register(BekleyenYetkiliHaberi)
class BekleyenYetkiliHaberiAdmin(ModelAdmin):
    list_display = ['baslik', 'yazar', 'kategori', 'kose_yazisi', 'olusturma_tarihi', 'onaylandi', 'reddedildi', 'onay_durumu']
    list_filter = ['kategori', 'kose_yazisi', 'onaylandi', 'reddedildi', 'olusturma_tarihi', 'onay_tarihi']
    search_fields = ['baslik', 'icerik', 'yazar__username', 'yazar__first_name', 'yazar__last_name']
    readonly_fields = ['olusturma_tarihi', 'onay_tarihi', 'red_tarihi', 'onaylayan', 'gorsel_onizleme']
    actions = ['approve_selected', 'reject_selected', 'delete_selected_items']
    date_hierarchy = 'olusturma_tarihi'

    def gorsel_onizleme(self, obj):
        return make_image_preview(obj)
    gorsel_onizleme.short_description = "Görsel Önizlemesi"

    def delete_selected_items(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"🗑️ Seçilen {count} adet yetkili haberi başarıyla silindi.", level='success')
    delete_selected_items.short_description = "🗑️ Seçili yetkili haberlerini tamamen sil" 
    
    def onay_durumu(self, obj):
        if obj.onaylandi:
            return "✅ Onaylandı"
        elif obj.reddedildi:
            return "❌ Reddedildi"
        else:
            return "📝 Yetkili Onayı Bekliyor"
    onay_durumu.short_description = "Durum"
    
    def get_queryset(self, request):
        # Varsayılan olarak onay bekleyen yetkili haberlerini göster
        qs = super().get_queryset(request)
        if not request.GET.get('onaylandi__exact') and not request.GET.get('reddedildi__exact'):
            return qs.filter(onaylandi=False, reddedildi=False)
        return qs
    
    fieldsets = (
        ('Haber Bilgileri & Görsel', {
            'fields': ('baslik', 'gorsel_onizleme', 'resim', 'ozet', 'icerik', 'kategori')
        }),
        ('Yazar ve Tür', {
            'fields': ('yazar', 'kose_yazisi')
        }),
        ('Onay Durumu', {
            'fields': ('onaylandi', 'reddedildi', 'olusturma_tarihi', 'onay_tarihi', 'red_tarihi', 'onaylayan', 'red_nedeni')
        }),
    )
    
    def approve_selected(self, request, queryset):
        """Approve selected pending yetkili news items"""
        approved_count = 0
        for pending_news in queryset:
            if not pending_news.onaylandi and not pending_news.reddedildi:
                try:
                    haber = pending_news.approve(request.user)
                    approved_count += 1
                    self.message_user(request, f"✅ '{pending_news.baslik}' onaylandı ve yayınlandı.", level='success')
                except Exception as e:
                    self.message_user(request, f"❌ '{pending_news.baslik}' onaylanırken hata oluştu: {e}", level='error')
        
        if approved_count > 0:
            self.message_user(request, f"🎉 Toplam {approved_count} yetkili haberi onaylandı ve siteye eklendi.", level='success')
    
    approve_selected.short_description = "✅ Seçili yetkili haberlerini onayla"
    
    def reject_selected(self, request, queryset):
        """Reject selected pending yetkili news items"""
        rejected_count = 0
        for pending_news in queryset:
            if not pending_news.onaylandi and not pending_news.reddedildi:
                try:
                    pending_news.reject(request.user, "Admin tarafından reddedildi")
                    rejected_count += 1
                    self.message_user(request, f"❌ '{pending_news.baslik}' reddedildi.", level='warning')
                except Exception as e:
                    self.message_user(request, f"⚠️ '{pending_news.baslik}' reddedilirken hata oluştu: {e}", level='error')
        
        if rejected_count > 0:
            self.message_user(request, f"📝 Toplam {rejected_count} yetkili haberi reddedildi.", level='warning')
    
    reject_selected.short_description = "❌ Seçili yetkili haberlerini reddet"
    
    def save_model(self, request, obj, form, change):
        """Override save to ensure proper approval workflow when manually changed"""
        # Check if this is a change (not creation) and onaylandi field was manually set to True
        if change and obj.onaylandi and not obj.onay_tarihi:
            try:
                # Reset approval status first
                obj.onaylandi = False
                obj.reddedildi = False
                obj.onay_tarihi = None
                obj.onaylayan = None
                super().save_model(request, obj, form, change)
                
                # Now properly approve using the model method
                haber = obj.approve(request.user)
                
                self.message_user(
                    request, 
                    f"✅ '{obj.baslik}' properly approved and published as {haber.slug}", 
                    level='success'
                )
                return
                
            except Exception as e:
                self.message_user(
                    request, 
                    f"❌ Error during approval of '{obj.baslik}': {e}", 
                    level='error'
                )
                # Reset to pending state on error
                obj.onaylandi = False
                obj.reddedildi = False
                obj.onay_tarihi = None
                obj.onaylayan = None
        
        # Check if reddedildi was manually set to True
        elif change and obj.reddedildi and not obj.red_tarihi:
            try:
                obj.reject(request.user, "Admin tarafından reddedildi")
                self.message_user(
                    request, 
                    f"❌ '{obj.baslik}' properly rejected", 
                    level='warning'
                )
                return
            except Exception as e:
                self.message_user(
                    request, 
                    f"⚠️ Error during rejection of '{obj.baslik}': {e}", 
                    level='error'
                )
        
        # Default save behavior
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        """Prevent manual creation of pending yetkili news in admin"""
        return False

class HaberDurumuFilter(admin.SimpleListFilter):
    title = 'Yayın / Onay Durumu'
    parameter_name = 'durum'

    def lookups(self, request, model_admin):
        return [
            ('tumu', '📋 Tümü'),
            ('bekleyen', '⏳ Onay Bekleyenler'),
            ('onaylanan', '✅ Onaylananlar'),
            ('reddedilen', '❌ Reddedilenler'),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'bekleyen':
            return queryset.filter(onaylandi=False, reddedildi=False)
        elif val == 'onaylanan':
            return queryset.filter(onaylandi=True)
        elif val == 'reddedilen':
            return queryset.filter(reddedildi=True)
        elif val == 'tumu':
            return queryset
        return queryset

class SkorAraligiFilter(admin.SimpleListFilter):
    title = 'Haber Değeri'
    parameter_name = 'skor_seviyesi'

    def lookups(self, request, model_admin):
        return [
            ('yildizli', '⭐ Branşında İlk 3 (Yıldızlı)'),
            ('cok_yuksek', '🔥 Çok Yüksek (80 - 100 Puan)'),
            ('yuksek', '⚡ Yüksek (65 - 79 Puan)'),
            ('orta', '💤 Orta (50 - 64 Puan)'),
            ('dusuk', '⏳ Düşük / Ham (< 50 Puan)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yildizli':
            starred_ids = model_admin.get_starred_ids()
            return queryset.filter(id__in=starred_ids)
        elif self.value() == 'cok_yuksek':
            return queryset.filter(haber_degeri_skoru__gte=80)
        elif self.value() == 'yuksek':
            return queryset.filter(haber_degeri_skoru__gte=65, haber_degeri_skoru__lt=80)
        elif self.value() == 'orta':
            return queryset.filter(haber_degeri_skoru__gte=50, haber_degeri_skoru__lt=65)
        elif self.value() == 'dusuk':
            return queryset.filter(models.Q(haber_degeri_skoru__lt=50) | models.Q(haber_degeri_skoru__isnull=True))
        return queryset

@admin.register(BekleyenHaber)
class BekleyenHaberAdmin(ModelAdmin):
    ordering = ['-haber_degeri_skoru', '-olusturma_tarihi']

    def get_starred_ids(self):
        """Her federasyon/branş için skoru en yüksek ilk 3 bekleyen haberin ID'lerini döndürür"""
        from .models import BekleyenHaber
        from django.db.models import Window, F
        from django.db.models.functions import RowNumber

        try:
            top_ids = BekleyenHaber.objects.filter(
                onaylandi=False,
                reddedildi=False,
                haber_degeri_skoru__gt=0
            ).annotate(
                row_num=Window(
                    expression=RowNumber(),
                    partition_by=[F('federasyon_website_id')],
                    order_by=[F('haber_degeri_skoru').desc(), F('id').desc()]
                )
            ).filter(row_num__lte=3).values_list('id', flat=True)
            return set(top_ids)
        except Exception:
            top_ids = set()
            fed_ids = BekleyenHaber.objects.filter(
                onaylandi=False, reddedildi=False, haber_degeri_skoru__gt=0
            ).values_list('federasyon_website_id', flat=True).distinct()
            for fid in fed_ids:
                ids = BekleyenHaber.objects.filter(
                    federasyon_website_id=fid, onaylandi=False, reddedildi=False, haber_degeri_skoru__gt=0
                ).order_by('-haber_degeri_skoru', '-id').values_list('id', flat=True)[:3]
                top_ids.update(ids)
            return top_ids

    def studyo_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:haberler_bekleyenhaber_studyo', args=[obj.id])
        return format_html(
            '<a href="{}" class="button" style="background:#0284c7; color:#ffffff !important; font-weight:700; padding:6px 12px; border-radius:6px; display:inline-flex; align-items:center; gap:5px; text-decoration:none; white-space:nowrap; box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
            '🎙️ Stüdyo'
            '</a>',
            url
        )
    studyo_link.short_description = "Haber Stüdyosu"

    def skor_badge(self, obj):
        score = obj.haber_degeri_skoru or 0
        starred_ids = getattr(self, '_cached_starred_ids', None)
        if starred_ids is None:
            starred_ids = self.get_starred_ids()
            self._cached_starred_ids = starred_ids
            
        is_starred = obj.id in starred_ids

        if is_starred:
            color = "#854d0e"
            bg = "#fef08a"
            border = "border:1px solid #eab308;"
            icon = "⭐"
        elif score >= 75:
            color = "#15803d"
            bg = "#dcfce7"
            border = "border:1px solid #86efac;"
            icon = "🔥"
        elif score >= 50:
            color = "#b45309"
            bg = "#fef3c7"
            border = "border:1px solid #fde68a;"
            icon = "⚡"
        elif score > 0:
            color = "#475569"
            bg = "#f1f5f9"
            border = "border:1px solid #cbd5e1;"
            icon = "💤"
        else:
            color = "#64748b"
            bg = "#e2e8f0"
            border = "border:1px solid #cbd5e1;"
            icon = "⏳"
            score = "Ham"

        star_tag = ' <span style="font-size:10px; background:#eab308; color:#fff; padding:1px 5px; border-radius:8px; font-weight:800; margin-left:2px;">TOP 3</span>' if is_starred else ''
        return format_html(
            '<span style="background:{}; color:{}; {}; padding:4px 10px; border-radius:14px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px; white-space:nowrap; box-shadow:0 1px 2px rgba(0,0,0,0.05);">'
            '{} {}{}'
            '</span>',
            bg, color, border, icon, score, mark_safe(star_tag)
        )
    skor_badge.short_description = "Haber Değeri"
    skor_badge.admin_order_field = 'haber_degeri_skoru'

    def baslik_temiz(self, obj):
        t = obj.ozgun_baslik if obj.ozgun_baslik else obj.baslik
        t = ' '.join(t.split())
        if len(t) > 75:
            t = t[:75] + '...'

        starred_ids = getattr(self, '_cached_starred_ids', None)
        if starred_ids is None:
            starred_ids = self.get_starred_ids()
            self._cached_starred_ids = starred_ids

        if obj.id in starred_ids:
            return format_html(
                '<span title="⭐ Branşın En Yüksek Skorlu İlk 3 Haberinden Biri" style="display:inline-flex; align-items:center; gap:4px;">'
                '<span style="color:#eab308; font-size:15px; text-shadow:0 0 4px rgba(234,179,8,0.5);">⭐</span> '
                '<span style="font-weight:600; color:#0f172a;">{}</span>'
                '</span>',
                t
            )
        return t
    baslik_temiz.short_description = "Başlık"

    def studyo_view(self, request, object_id):
        from django.shortcuts import get_object_or_404
        from .models import BekleyenHaber, Kategori
        from .ai_news_engine import ozgunlestir_haber
        from .smart_tags import generate_smart_tags, get_airtag_id, get_airtag_shortlink
        
        bekleyen = get_object_or_404(BekleyenHaber, id=object_id)
        
        # Otomatik AI: Eğer başlık özgünleşmemişse ve işlemde değilse otomatik hazırla
        if not bekleyen.ozgun_baslik and bekleyen.ai_durum != 'isleniyor':
            ozgunlestir_haber(bekleyen)
            bekleyen.refresh_from_db()
            
        kategoriler = Kategori.objects.all().order_by('ad')
        smart_tags = generate_smart_tags(bekleyen)
        airtag_id = get_airtag_id(bekleyen)
        airtag_shortlink = get_airtag_shortlink(bekleyen, 'wa_durum')

        context = dict(
            self.admin_site.each_context(request),
            title=f"Haber Stüdyosu - {bekleyen.id}",
            bekleyen=bekleyen,
            kategoriler=kategoriler,
            smart_tags=smart_tags,
            airtag_id=airtag_id,
            airtag_shortlink=airtag_shortlink,
        )
        return render(request, 'admin/haber_studyo.html', context)

    def studyo_kaydet(self, request, object_id):
        from django.shortcuts import get_object_or_404
        from .models import BekleyenHaber, Kategori
        
        bekleyen = get_object_or_404(BekleyenHaber, id=object_id)
        action = request.POST.get('action', 'save')

        if action == 'reject':
            try:
                if not bekleyen.reddedildi and not bekleyen.onaylandi:
                    bekleyen.reject(request.user)
                    self.message_user(request, f"❌ #{bekleyen.id} numaralı haber başarıyla reddedildi ve listeden çıkarıldı.", level=messages.WARNING)
                else:
                    self.message_user(request, f"ℹ️ Bu haber zaten işlenmiş durumda (Durum: {'Onaylandı' if bekleyen.onaylandi else 'Reddedildi'}).", level=messages.INFO)
                return redirect('admin:haberler_bekleyenhaber_changelist')
            except Exception as e:
                self.message_user(request, f"Reddetme hatası: {str(e)}", level=messages.ERROR)
                return redirect('admin:haberler_bekleyenhaber_studyo', object_id=bekleyen.id)

        elif action == 'reopen':
            try:
                bekleyen.reddedildi = False
                bekleyen.red_tarihi = None
                bekleyen.onaylandi = False
                bekleyen.onay_tarihi = None
                bekleyen.save()
                self.message_user(request, f"♻️ #{bekleyen.id} numaralı haber yeniden onay bekleyen havuzuna alındı.", level=messages.SUCCESS)
                return redirect('admin:haberler_bekleyenhaber_studyo', object_id=bekleyen.id)
            except Exception as e:
                self.message_user(request, f"Havuza alma hatası: {str(e)}", level=messages.ERROR)
                return redirect('admin:haberler_bekleyenhaber_studyo', object_id=bekleyen.id)

        bekleyen.ozgun_baslik = request.POST.get('ozgun_baslik', '').strip()
        bekleyen.ozgun_ozet = request.POST.get('ozgun_ozet', '').strip()
        bekleyen.ozgun_icerik = request.POST.get('ozgun_icerik', '').strip()
        
        kat_id = request.POST.get('kategori_id')
        if kat_id:
            try:
                bekleyen.kategori = Kategori.objects.get(id=kat_id)
            except Kategori.DoesNotExist:
                pass
                
        bekleyen.save()
        
        if action == 'publish':
            try:
                haber = bekleyen.approve(request.user)
                # Editorial overrides from studio form
                manset_override = request.POST.get('manset_haberi')
                pin_override = request.POST.get('manset_sabitlendi')
                if manset_override is not None:
                    haber.manset_haberi = (manset_override in ['1', 'on', 'true', 'True'])
                if pin_override is not None:
                    haber.manset_sabitlendi = (pin_override in ['1', 'on', 'true', 'True'])
                haber.save()

                live_url = f"/haber/{haber.slug}/"
                from django.utils.html import escape, format_html
                self.message_user(
                    request,
                    format_html(
                        "🎉 <strong>Tebrikler!</strong> Haber canlı yayına alındı: <a href='{}' target='_blank' style='color:#fff; text-decoration:underline; font-weight:bold;'>{} (Siteyi Gör ↗)</a>",
                        live_url,
                        haber.baslik
                    ),
                    level=messages.SUCCESS
                )
                return redirect('admin:haberler_bekleyenhaber_changelist')
            except Exception as e:
                self.message_user(request, f"Yayınlama hatası: {str(e)}", level=messages.ERROR)
                return redirect('admin:haberler_bekleyenhaber_studyo', object_id=bekleyen.id)
                
        self.message_user(request, "💾 Taslak başarıyla kaydedildi.", level=messages.SUCCESS)
        return redirect('admin:haberler_bekleyenhaber_studyo', object_id=bekleyen.id)

    def ai_calistir(self, request, object_id):
        from django.shortcuts import get_object_or_404
        from .models import BekleyenHaber
        from .ai_news_engine import ozgunlestir_haber
        
        bekleyen = get_object_or_404(BekleyenHaber, id=object_id)
        ton = request.GET.get('ton', 'standart')
        success, res = ozgunlestir_haber(bekleyen, ton=ton)
        if success:
            self.message_user(request, "⚡ Haber yapay zeka tarafından başarıyla yeniden özgünleştirildi.", level=messages.SUCCESS)
        else:
            self.message_user(request, f"Yapay zeka hatası: {res}", level=messages.ERROR)
            
        return redirect('admin:haberler_bekleyenhaber_studyo', object_id=bekleyen.id)

    def gorsel_durumu(self, obj):
        if obj.resim:
            try:
                url = obj.resim.url
                return format_html(
                    '<a href="{}" target="_blank" style="display:inline-block; position:relative;" title="Görseli Büyüt">'
                    '<img src="{}" style="width:48px; height:32px; object-fit:cover; border-radius:4px; border:1px solid #cbd5e1; box-shadow:0 1px 2px rgba(0,0,0,0.1);">'
                    '<span style="position:absolute; bottom:-2px; right:-2px; width:8px; height:8px; background:#10b981; border:1.5px solid #fff; border-radius:50%;"></span>'
                    '</a>',
                    url, url
                )
            except Exception:
                pass
        return format_html(
            '<span style="background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; padding:3px 7px; border-radius:6px; font-weight:700; font-size:11px; white-space:nowrap; display:inline-flex; align-items:center; gap:3px;">'
            '❌ Görsel Yok'
            '</span>'
        )
    gorsel_durumu.short_description = "Görsel"

    list_display = ['studyo_link', 'skor_badge', 'gorsel_durumu', 'baslik_temiz', 'federasyon_website', 'kategori', 'olusturma_tarihi', 'onay_durumu']
    list_filter = [HaberDurumuFilter, SkorAraligiFilter, 'federasyon_website', 'kategori', 'olusturma_tarihi']
    search_fields = ['baslik', 'icerik', 'kaynak_url']
    readonly_fields = ['canli_kart_onizleme', 'olusturma_tarihi', 'onay_tarihi', 'red_tarihi', 'onaylayan', 'gorsel_onizleme', 'kaynak_url']
    actions = ['approve_selected', 'reject_selected', 'delete_selected_items']

    def canli_kart_onizleme(self, obj):
        return make_live_card_preview(obj)
    canli_kart_onizleme.short_description = "Haber Kartı Canlı Simülasyonu"

    def gorsel_onizleme(self, obj):
        return make_image_preview(obj)
    gorsel_onizleme.short_description = "Görsel Önizlemesi"

    fieldsets = (
        ('📱 Canlı Kart Görsel Önizleme', {
            'fields': ('canli_kart_onizleme',),
            'description': 'Onaylandığı takdirde bu haberin SPOR24.NET ana sayfasında nasıl görüneceğinin canlı simülasyonu.'
        }),
        ('Haber Detayı', {
            'fields': ('baslik', 'federasyon_website', 'kategori', 'haber_tarihi', 'kaynak_url')
        }),
        ('Görsel & Metin', {
            'fields': ('gorsel_onizleme', 'kaynak_resim_url', 'resim', 'ozet', 'icerik')
        }),
        ('Onay Durumu', {
            'fields': ('onaylandi', 'reddedildi', 'olusturma_tarihi', 'onay_tarihi', 'red_tarihi', 'onaylayan', 'red_nedeni')
        }),
    )

    def delete_selected_items(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"🗑️ Seçilen {count} adet bekleyen haber başarıyla silindi.", level='success')
    delete_selected_items.short_description = "🗑️ Seçili haberleri tamamen sil" 

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/studyo/', self.admin_site.admin_view(self.studyo_view), name='haberler_bekleyenhaber_studyo'),
            path('<int:object_id>/studyo-kaydet/', self.admin_site.admin_view(self.studyo_kaydet), name='haberler_bekleyenhaber_studyo_kaydet'),
            path('<int:object_id>/ai-calistir/', self.admin_site.admin_view(self.ai_calistir), name='haberler_bekleyenhaber_ai_calistir'),
            path('toplu-ai-ozgunlestir/', self.admin_site.admin_view(self.toplu_ai_ozgunlestir_trigger), name='haberler_bekleyenhaber_toplu_ai'),
            path('trigger-scrape/', self.admin_site.admin_view(self.trigger_scrape), name='haberler_bekleyenhaber_trigger_scrape'),
            path('scraper-health/', self.admin_site.admin_view(self.scraper_health), name='scraper_health'),
            path('social-media-health/', self.admin_site.admin_view(self.social_media_health), name='social_media_health'),
        ]
        return custom_urls + urls

    
    def toplu_ai_ozgunlestir_trigger(self, request):
        from django.core.management import call_command
        import threading
        
        def run_batch():
            try:
                call_command('tum_bekleyenleri_ozgunlestir')
            except Exception as e:
                print(f"Async AI batch error: {e}")
                
        threading.Thread(target=run_batch).start()
        
        self.message_user(
            request, 
            "🤖 Tüm bekleyen haberleri yapay zeka ile özgünleştirme ve puanlama işlemi arka planda başlatıldı! Birkaç dakika sonra sayfayı yenilediğinizde tüm haberler hazır olacaktır.", 
            level=messages.SUCCESS
        )
        return redirect('admin:haberler_bekleyenhaber_changelist')

    def trigger_scrape(self, request):
        from django.core.management import call_command
        import threading
        
        def run_scrape():
            try:
                call_command('crawl_federasyonlar_ai', limit=3)
            except Exception as e:
                print(f"Async Crawl4AI error: {e}")
                
        threading.Thread(target=run_scrape).start()
        
        self.message_user(
            request, 
            "🔄 Federasyon sitelerini tarama işlemi akıllı tarayıcı (Crawl4AI) ile arka planda başlatıldı! Yeni haberler birkaç dakika içinde havuza eklenecektir.", 
            level=messages.INFO
        )
        return redirect('admin:haberler_bekleyenhaber_changelist')

    def scraper_health(self, request):
        from .models import FederasyonWebsite, Haber, BekleyenHaber
        
        federations_data = []
        for fed in FederasyonWebsite.objects.all():
            pub_count = Haber.objects.filter(federasyon_website=fed).count()
            pend_count = BekleyenHaber.objects.filter(federasyon_website=fed).count()
            
            federations_data.append({
                'obj': fed,
                'pub_count': pub_count,
                'pend_count': pend_count
            })
            
        context = dict(
            self.admin_site.each_context(request),
            title="Scraper Health Dashboard",
            federations=federations_data,
        )
        return render(request, 'admin/scraper_health.html', context)

    def social_media_health(self, request):
        from .models import FederasyonWebsite
        federations = FederasyonWebsite.objects.all()
        context = dict(
            self.admin_site.each_context(request),
            title="Sosyal Medya Sağlık Durumu",
            federations=federations,
        )
        return render(request, 'admin/social_media_health.html', context)



    def get_form(self, request, obj=None, **kwargs):
        request.current_obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "kategori":
            obj = getattr(request, 'current_obj', None)
            if obj and obj.federasyon_website:
                from django.db.models import Q
                from .models import Kategori
                fed_name = obj.federasyon_website.ad.lower()
                q = Q(federasyon_website=obj.federasyon_website)
                
                # Special cases for aggregated feeds
                if 'muay' in fed_name:
                    q |= Q(federasyon_website__ad__icontains='muay') | Q(federasyon_website__ad__icontains='jitsu') | Q(ad__icontains='muay') | Q(ad__icontains='jitsu')
                elif 'karate' in fed_name:
                    q |= Q(federasyon_website__ad__icontains='karate') | Q(federasyon_website__ad__icontains='kyokushin') | Q(ad__icontains='karate') | Q(ad__icontains='kyokushin')
                    
                kwargs["queryset"] = Kategori.objects.filter(q).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def onay_durumu(self, obj):
        if obj.onaylandi:
            return format_html(
                '<span style="background:#dcfce7; color:#15803d; border:1px solid #86efac; padding:4px 10px; border-radius:12px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px; white-space:nowrap; box-shadow:0 1px 2px rgba(0,0,0,0.05);">'
                '✅ Onaylandı'
                '</span>'
            )
        elif obj.reddedildi:
            return format_html(
                '<span style="background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; padding:4px 10px; border-radius:12px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px; white-space:nowrap;">'
                '❌ Reddedildi'
                '</span>'
            )
        else:
            return format_html(
                '<span style="background:#fef3c7; color:#b45309; border:1px solid #fde68a; padding:4px 10px; border-radius:12px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px; white-space:nowrap;">'
                '⏳ Onay Bekliyor'
                '</span>'
            )
    onay_durumu.short_description = "Durum"
    onay_durumu.admin_order_field = 'onaylandi'

    def changelist_view(self, request, extra_context=None):
        from django.http import HttpResponseRedirect
        if 'tab' in request.GET:
            qp = request.GET.copy()
            tab_val = qp.pop('tab')[0]
            qp['durum'] = tab_val
            return HttpResponseRedirect(request.path + '?' + qp.urlencode())

        extra_context = extra_context or {}
        from .models import BekleyenHaber
        total_bekleyen = BekleyenHaber.objects.filter(onaylandi=False, reddedildi=False).count()
        total_onaylanan = BekleyenHaber.objects.filter(onaylandi=True).count()
        total_reddedilen = BekleyenHaber.objects.filter(reddedildi=True).count()
        total_tumu = BekleyenHaber.objects.count()
        
        extra_context['tab_counts'] = {
            'bekleyen': total_bekleyen,
            'onaylanan': total_onaylanan,
            'reddedilen': total_reddedilen,
            'tumu': total_tumu
        }

        # Aktif sekme belirleme (Varsayılan: Onay Bekleyenler)
        current_durum = request.GET.get('durum', 'bekleyen')
        if current_durum not in ['tumu', 'bekleyen', 'onaylanan', 'reddedilen']:
            current_durum = 'bekleyen'
        extra_context['current_tab'] = current_durum

        # Diğer arama/filtre/sıralama parametrelerini koruyan dinamik sekme linkleri
        base_params = request.GET.copy()
        base_params.pop('p', None)
        base_params.pop('e', None)

        tab_urls = {}
        for t in ['bekleyen', 'onaylanan', 'reddedilen', 'tumu']:
            p = base_params.copy()
            p['durum'] = t
            tab_urls[t] = '?' + p.urlencode()

        extra_context['tab_urls'] = tab_urls
        
        # Yıldızlı ilk 3 haberleri cache'le
        self._cached_starred_ids = self.get_starred_ids()
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        durum = request.GET.get('durum')
        if durum == 'tumu':
            return qs
        elif durum == 'onaylanan':
            return qs.filter(onaylandi=True)
        elif durum == 'reddedilen':
            return qs.filter(reddedildi=True)
        else:
            # Varsayılan olarak sadece işlem bekleyenleri göster (yayındaki veya reddedilenler karışmaz)
            return qs.filter(onaylandi=False, reddedildi=False)
    
    fieldsets = (
        ('Haber Bilgileri & Görsel', {
            'fields': ('baslik', 'gorsel_onizleme', 'resim', 'kaynak_resim_url', 'ozet', 'icerik', 'kaynak_url', 'federasyon_website', 'kategori', 'haber_tarihi')
        }),
        ('Durum', {
            'fields': ('onaylandi', 'reddedildi', 'olusturma_tarihi', 'onay_tarihi', 'red_tarihi', 'onaylayan')
        }),
    )
    
    def approve_selected(self, request, queryset):
        """Approve selected pending news items"""
        approved_count = 0
        for pending_news in queryset:
            if not pending_news.onaylandi and not pending_news.reddedildi:
                try:
                    pending_news.approve(request.user)
                    approved_count += 1
                except Exception as e:
                    self.message_user(request, f"{pending_news.baslik} onaylanırken hata oluştu: {e}", level='error')
        
        self.message_user(request, f"{approved_count} haber onaylandı.")
    
    approve_selected.short_description = "Seçili haberleri onayla"
    
    def reject_selected(self, request, queryset):
        """Reject selected pending news items"""
        rejected_count = 0
        for pending_news in queryset:
            if not pending_news.onaylandi and not pending_news.reddedildi:
                try:
                    pending_news.reject(request.user)
                    rejected_count += 1
                except Exception as e:
                    self.message_user(request, f"{pending_news.baslik} reddedilirken hata oluştu: {e}", level='error')
        
        self.message_user(request, f"{rejected_count} haber reddedildi.")
    
    reject_selected.short_description = "Seçili haberleri reddet"
    
    def save_model(self, request, obj, form, change):
        """Override save to ensure proper approval workflow when manually changed"""
        # Check if this is a change (not creation) and onaylandi field was manually set to True
        if change and obj.onaylandi and not obj.onay_tarihi:
            try:
                # Reset approval status first
                obj.onaylandi = False
                obj.reddedildi = False
                obj.onay_tarihi = None
                obj.onaylayan = None
                super().save_model(request, obj, form, change)
                
                # Now properly approve using the model method
                haber = obj.approve(request.user)
                
                self.message_user(
                    request, 
                    f"✅ '{obj.baslik}' properly approved and published", 
                    level='success'
                )
                return
                
            except Exception as e:
                self.message_user(
                    request, 
                    f"❌ Error during approval of '{obj.baslik}': {e}", 
                    level='error'
                )
                # Reset to pending state on error
                obj.onaylandi = False
                obj.reddedildi = False
                obj.onay_tarihi = None
                obj.onaylayan = None
        
        # Check if reddedildi was manually set to True
        elif change and obj.reddedildi and not obj.red_tarihi:
            try:
                obj.reject(request.user)
                self.message_user(
                    request, 
                    f"❌ '{obj.baslik}' properly rejected", 
                    level='warning'
                )
                return
            except Exception as e:
                self.message_user(
                    request, 
                    f"⚠️ Error during rejection of '{obj.baslik}': {e}", 
                    level='error'
                )
        
        # Default save behavior
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        """Prevent manual creation of pending news"""
        return False

# --- Recovered Karate Admin Models ---
from .models import KarateSehir, KarateKulup, KarateAntrenor, Sporcu, KusakSinavBasvuru

@admin.register(KarateSehir)
class KarateSehirAdmin(ModelAdmin):
    list_display = ['ad']
    search_fields = ['ad']

@admin.register(KarateKulup)
class KarateKulupAdmin(ModelAdmin):
    list_display = ['ad', 'yetkili', 'sehir']
    list_filter = ['sehir']
    search_fields = ['ad', 'yetkili']

@admin.register(KarateAntrenor)
class KarateAntrenorAdmin(ModelAdmin):
    list_display = ['ad_soyad', 'kademe', 'kulup', 'sehir']
    list_filter = ['sehir', 'kademe']
    search_fields = ['ad_soyad', 'kulup']

@admin.register(Sporcu)
class SporcuAdmin(ModelAdmin):
    list_display = ['ad_soyad', 'tc', 'kemer', 'kulup', 'is_web_kayit', 'created_at']
    list_filter = ['kemer', 'cinsiyet', 'is_web_kayit', 'created_at']
    search_fields = ['ad_soyad', 'tc', 'kulup', 'lisans_no']
    list_editable = ['is_web_kayit']
    
@admin.register(KusakSinavBasvuru)
class KusakSinavBasvuruAdmin(ModelAdmin):
    list_display = ['get_sporcu_ad', 'mevcut_kemer', 'talep_edilen_kemer', 'durum', 'ucret_odendi', 'basvuru_tarihi']
    list_filter = ['durum', 'ucret_odendi', 'talep_edilen_kemer', 'basvuru_tarihi']
    search_fields = ['sporcu__ad_soyad', 'sporcu__tc']
    list_editable = ['durum', 'ucret_odendi']
    
    def get_sporcu_ad(self, obj):
        return obj.sporcu.ad_soyad
    get_sporcu_ad.short_description = 'Sporcu'

# --- Columnists Admin Section ---
from .models import KoseYazari, UserProfile
from django import forms
from django.contrib.auth.models import User

class KoseYazariForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False, label="Yeni Kullanıcı Adı", help_text="Sıfırdan yeni yazar oluşturmak için doldurun")
    password = forms.CharField(widget=forms.PasswordInput, required=False, label="Yeni Kullanıcı Şifresi", help_text="Sıfırdan yeni yazar oluşturmak için doldurun")
    yeni_sifre = forms.CharField(
        label="🔑 Yazar Şifresini Değiştir",
        widget=forms.TextInput(attrs={'placeholder': 'Yeni şifreyi buraya yazın (Değiştirmek istemiyorsanız boş bırakın)', 'style': 'width: 100%; max-width: 400px; padding: 6px; font-weight: bold; border: 2px solid #dc3545;'}),
        required=False,
        help_text="Bu yazarın şifresini değiştirmek için yeni şifreyi yazın ve Kaydet butonuna basın."
    )
    first_name = forms.CharField(max_length=150, required=False, label="Yazar Adı")
    last_name = forms.CharField(max_length=150, required=False, label="Yazar Soyadı")
    email = forms.EmailField(required=False, label="Yazar E-posta")

    class Meta:
        model = KoseYazari
        fields = ['user', 'bio', 'profil_resmi', 'location', 'birth_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'user' in self.fields:
            self.fields['user'].required = False
            self.fields['user'].label = "Mevcut Kullanıcıyı Seçin"
            self.fields['user'].help_text = "Sistemdeki mevcut bir kullanıcıyı köşe yazarı yapmak için seçin. VEYA yukarıdaki alanları doldurarak yeni bir yazar oluşturun."

    def clean(self):
        cleaned_data = super().clean()
        if self.instance and self.instance.pk:
            return cleaned_data
            
        user = cleaned_data.get('user')
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        email = cleaned_data.get('email')

        if not user:
            if not username or not password:
                raise forms.ValidationError("Lütfen ya mevcut bir kullanıcı seçin ya da yeni yazar için kullanıcı adı ve şifre girin.")
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("Bu kullanıcı adı zaten alınmış.")
            if email and User.objects.filter(email=email).exists():
                raise forms.ValidationError("Bu e-posta adresi zaten kullanımda.")
        return cleaned_data

@admin.register(KoseYazari)
class KoseYazariAdmin(ModelAdmin):
    form = KoseYazariForm
    list_display = ['goster_profil_resmi', 'goster_yazar_adi', 'user', 'yazi_sayisi_goster', 'user_type', 'anasayfa_yazari']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'location']
    readonly_fields = ['user_type', 'yazar_yazilari']
    list_editable = ['anasayfa_yazari']
    ordering = ['-anasayfa_yazari', 'user__first_name']

    def goster_profil_resmi(self, obj):
        from django.utils.html import format_html
        if obj.profil_resmi:
            return format_html('<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 50%; border: 1px solid #ddd;" />', obj.profil_resmi.url)
        return format_html('<span style="color: #999;">Resim Yok</span>')
    goster_profil_resmi.short_description = "Profil Resmi"

    def goster_yazar_adi(self, obj):
        return obj.user.get_full_name() or obj.user.username
    goster_yazar_adi.short_description = "Yazar Adı Soyadı"

    def yazi_sayisi_goster(self, obj):
        from .models import Haber
        return Haber.objects.filter(yazar=obj.user, kose_yazisi=True).count()
    yazi_sayisi_goster.short_description = "Köşe Yazısı Sayısı"

    def get_fields(self, request, obj=None):
        if obj:
            return ['user', 'user_type', 'yeni_sifre', 'bio', 'profil_resmi', 'location', 'birth_date', 'anasayfa_yazari', 'yazar_yazilari']
        else:
            return ['user', 'username', 'password', 'first_name', 'last_name', 'email', 'bio', 'profil_resmi', 'location', 'birth_date', 'anasayfa_yazari']

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing existing yazar
            return list(self.readonly_fields) + ['user']
        return self.readonly_fields
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='yetkili')
        
    def save_model(self, request, obj, form, change):
        yeni_sifre = form.cleaned_data.get('yeni_sifre')
        if change and getattr(obj, 'user', None) and yeni_sifre:
            obj.user.set_password(yeni_sifre)
            obj.user.save()
            messages.success(request, f"🔑 '{obj.user.username}' yazarının şifresi başarıyla '{yeni_sifre}' olarak güncellendi!")
        if not change:
            user = form.cleaned_data.get('user')
            if not user:
                # Create new User
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                email = form.cleaned_data.get('email')
                
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True
                )
                obj.user = user
            else:
                try:
                    profile = UserProfile.objects.get(user=user)
                    # Upgrade existing profile
                    profile.user_type = 'yetkili'
                    profile.bio = obj.bio
                    if obj.profil_resmi:
                        profile.profil_resmi = obj.profil_resmi
                    profile.location = obj.location
                    profile.birth_date = obj.birth_date
                    profile.save()
                    obj.pk = profile.pk
                    obj.id = profile.id
                    return
                except UserProfile.DoesNotExist:
                    pass
                
        obj.user_type = 'yetkili'
        super().save_model(request, obj, form, change)
        
    def yazar_yazilari(self, obj):
        from .models import Haber
        from django.utils.html import format_html
        if not obj or not getattr(obj, 'user', None):
            return "Yazara ait kayıt bulunamadı."
        yazilar = Haber.objects.filter(yazar=obj.user, kose_yazisi=True).order_by('-olusturma_tarihi')
        if not yazilar.exists():
            return "Yazara ait köşe yazısı bulunamadı."
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for yazi in yazilar:
            url = f"/admin/haberler/haber/{yazi.id}/change/"
            html += f'<li><a href="{url}">{yazi.baslik}</a> ({yazi.olusturma_tarihi.strftime("%d.%m.%Y")})</li>'
        html += "</ul>"
        return format_html(html)
    yazar_yazilari.short_description = "Köşe Yazısı Arşivi"

@admin.register(TaramaLog)
class TaramaLogAdmin(ModelAdmin):
    list_display = ['federasyon_website', 'tarama_zamani', 'durum', 'eklenen_sayi', 'mesaj']
    list_filter = ['durum', 'tarama_zamani', 'federasyon_website']
    search_fields = ['federasyon_website__ad', 'mesaj']
    readonly_fields = ['federasyon_website', 'tarama_zamani', 'durum', 'eklenen_sayi', 'mesaj']

@admin.register(Ad)
class AdAdmin(ModelAdmin):
    list_display = ['gorsel_onizleme', 'konum', 'baslik', 'hedef_url_link', 'aktif', 'iframe_goster', 'olusturma_tarihi']
    list_filter = ['aktif', 'konum', 'iframe_goster']
    search_fields = ['baslik', 'hedef_url']
    list_editable = ['aktif', 'iframe_goster']
    
    def gorsel_onizleme(self, obj):
        if obj.resim:
            return format_html('<img src="{}" style="height: 45px; max-width: 120px; object-fit: contain; border-radius: 4px; border: 1px solid #444;" />', obj.resim.url)
        elif obj.hedef_url and obj.iframe_goster:
            return mark_safe('<span style="background: #17a2b8; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">🌐 Canlı Iframe Site</span>')
        return mark_safe('<span style="color: #888; font-style: italic;">(Görsel Yok)</span>')
    gorsel_onizleme.short_description = "Reklam Görseli / Önizleme"

    def hedef_url_link(self, obj):
        if obj.hedef_url:
            short_url = obj.hedef_url.replace('https://', '').replace('http://', '').replace('www.', '')
            if len(short_url) > 30:
                short_url = short_url[:30] + '...'
            return format_html('<a href="{}" target="_blank" style="font-weight: bold; color: #20c997; text-decoration: underline;">🔗 {}</a>', obj.hedef_url, short_url)
        return mark_safe('<span style="color: #6c757d;">-</span>')
    hedef_url_link.short_description = "Hedef Web Sayfası"


@admin.register(Reklam)
class ReklamAdmin(ModelAdmin):
    list_display = ['baslik', 'reklam_tipi', 'konum', 'sira_no', 'resim_onizleme', 'hedef_link']
    list_filter = ['reklam_tipi', 'konum']
    search_fields = ['baslik', 'youtube_url', 'iframe_url']

    def resim_onizleme(self, obj):
        if obj.resim:
            return format_html('<img src="{}" style="height: 45px; max-width: 120px; object-fit: contain; border-radius: 4px;" />', obj.resim.url)
        elif obj.video:
            return mark_safe('<span style="background: #e83e8c; color: #fff; padding: 3px 6px; border-radius: 4px; font-size: 11px;">🎥 Video</span>')
        elif obj.youtube_url:
            return mark_safe('<span style="background: #dc3545; color: #fff; padding: 3px 6px; border-radius: 4px; font-size: 11px;">▶️ YouTube</span>')
        return mark_safe('<span style="color: #888;">-</span>')
    resim_onizleme.short_description = "Önizleme"

    def hedef_link(self, obj):
        if obj.iframe_url:
            return format_html('<a href="{}" target="_blank">🌐 {}</a>', obj.iframe_url, obj.iframe_url[:25])
        elif obj.youtube_url:
            return format_html('<a href="{}" target="_blank">▶️ {}</a>', obj.youtube_url, obj.youtube_url[:25])
        return "-"
    hedef_link.short_description = "Bağlantı"

@admin.register(Kunye)
class KunyeAdmin(ModelAdmin):
    list_display = ['imtiyaz_sahibi', 'sorumlu_yazi_isleri_muduru', 'telefon', 'eposta']
    
    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return True


from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import UserProfile, KoseYazari

class CustomUserChangeForm(UserChangeForm):
    yeni_sifre = forms.CharField(
        label="🔑 Yeni Şifre Belirle (Admin Tarafından)",
        widget=forms.TextInput(attrs={'placeholder': 'Yeni şifreyi yazın (Değiştirmek istemiyorsanız boş bırakın)', 'style': 'width: 100%; max-width: 400px; padding: 6px; font-weight: bold; border: 2px solid #dc3545;'}),
        required=False,
        help_text="Bu alana yeni bir şifre yazıp sayfanın altındaki 'Kaydet' butonuna basarak kullanıcının şifresini anında güncelleyebilirsiniz."
    )

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil Bilgileri / Rol ve Yetki Ayarları'
    fk_name = 'user'
    fieldsets = (
        (None, {
            'fields': ('user_type', 'bio', 'location', 'birth_date', 'profil_resmi', 'anasayfa_yazari')
        }),
        ('Yetkiler (Yalnızca Yetkili Tipi İçin Geçerli)', {
            'fields': ('can_add_news', 'can_edit_news', 'can_add_column', 'can_manage_comments'),
        }),
    )

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    inlines = (UserProfileInline,)
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        if obj:
            fieldsets[0][1]['fields'] = ('username', 'password', 'yeni_sifre', 'first_name', 'last_name', 'email')
        return fieldsets

    def save_model(self, request, obj, form, change):
        yeni_sifre = form.cleaned_data.get('yeni_sifre')
        if yeni_sifre:
            obj.set_password(yeni_sifre)
            messages.success(request, f"🔑 '{obj.username}' kullanıcısının şifresi başarıyla '{yeni_sifre}' olarak güncellendi!")
        super().save_model(request, obj, form, change)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)




# ============================================================
# ANKET (POLL) & YARIŞMA (QUIZ) YÖNETİMİ
# ============================================================
from .models_engagement import Poll, PollChoice, PollVote, Quiz, QuizQuestion, UserQuizScore

class PollChoiceInline(admin.TabularInline):
    model = PollChoice
    extra = 3
    fields = ['choice_text', 'votes_count']
    readonly_fields = ['votes_count']

@admin.register(Poll)
class PollAdmin(ModelAdmin):
    list_display = ['question', 'position', 'is_active', 'total_votes', 'oy_dagilimi_grafik', 'start_date', 'end_date', 'created_at']
    list_filter = ['is_active', 'position', 'created_at']
    search_fields = ['question']
    list_editable = ['is_active', 'position']
    inlines = [PollChoiceInline]
    readonly_fields = ['created_at', 'oy_dagilimi_grafik']
    
    fieldsets = (
        ('Anket Bilgileri & Pozisyon', {
            'fields': ('question', 'position', 'is_active', 'start_date', 'end_date')
        }),
        ('📊 Canlı Oy Sonuçları & Dağılım', {
            'fields': ('oy_dagilimi_grafik',)
        }),
        ('Sistem', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def total_votes(self, obj):
        return sum(c.votes_count for c in obj.choices.all())
    total_votes.short_description = 'Toplam Oy'

    def oy_dagilimi_grafik(self, obj):
        from django.utils.html import format_html
        if not obj or not obj.id:
            return "Anket henüz kaydedilmedi."
        choices = obj.choices.all()
        total = sum(c.votes_count for c in choices) or 0
        if total == 0:
            return format_html('<span style="color: #888;">Henüz oy kullanılmadı.</span>')
        html = '<div style="max-width: 450px; background: #1a1f2c; padding: 12px; border-radius: 8px; color: #fff;">'
        for c in choices:
            pct = round((c.votes_count / total) * 100, 1)
            html += f'''
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: bold; margin-bottom: 3px;">
                    <span>🔹 {c.choice_text}</span>
                    <span style="color: #fbbf24;">%{pct} ({c.votes_count} oy)</span>
                </div>
                <div style="background: #0f172a; border-radius: 6px; height: 14px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="background: linear-gradient(90deg, #dc3545, #ff6b6b); width: {pct}%; height: 100%;"></div>
                </div>
            </div>
            '''
        html += f'<div style="margin-top: 8px; font-size: 11px; text-align: right; color: #94a3b8; font-weight: bold;">Toplam: {total} Oy Kullanıldı</div></div>'
        return format_html(html)
    oy_dagilimi_grafik.short_description = "📊 Canlı Oy Dağılım Grafiği"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

@admin.register(PollVote)
class PollVoteAdmin(ModelAdmin):
    list_display = ['poll', 'choice', 'user', 'ip_address', 'created_at']
    list_filter = ['poll', 'created_at']
    search_fields = ['poll__question', 'user__username', 'ip_address']
    readonly_fields = ['poll', 'choice', 'user', 'ip_address', 'created_at']
    
    def has_add_permission(self, request):
        return False


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 2
    fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']

@admin.register(Quiz)
class QuizAdmin(ModelAdmin):
    list_display = ['title', 'is_active', 'question_count', 'participant_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    inlines = [QuizQuestionInline]
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Yarışma Bilgileri', {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Sistem', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Soru Sayısı'
    
    def participant_count(self, obj):
        return obj.userquizscore_set.count()
    participant_count.short_description = 'Katılımcı'

@admin.register(UserQuizScore)
class UserQuizScoreAdmin(ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'completed_at']
    list_filter = ['quiz', 'completed_at']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['user', 'quiz', 'score', 'completed_at']
    
    def has_add_permission(self, request):
        return False


from .models import BekleyenSosyalMedyaHaberi

@admin.register(BekleyenSosyalMedyaHaberi)
class BekleyenSosyalMedyaHaberiAdmin(ModelAdmin):
    list_display = ['title_preview', 'platform', 'federasyon_website', 'gonderi_tipi', 'paylasim_tarihi', 'onay_durumu']
    list_filter = ['platform', 'onaylandi', 'reddedildi', 'gonderi_tipi', 'paylasim_tarihi', 'federasyon_website']
    search_fields = ['baslik', 'icerik', 'paylasim_id']
    readonly_fields = ['canli_kart_onizleme', 'paylasim_id', 'paylasim_tarihi', 'onay_tarihi', 'onaylayan', 'gorsel_onizleme']
    actions = ['approve_selected_posts', 'reject_selected_posts', 'delete_selected_items']

    fieldsets = (
        ('📱 Canlı Kart Görsel Önizleme (Spor24 Ana Sayfa Görünümü)', {
            'fields': ('canli_kart_onizleme',),
            'description': 'Bu gönderi onaylanıp haber havuzuna alındığında ziyaretçilere ana sayfada bu şekilde görünecektir.'
        }),
        ('Gönderi ve Canlı Önizleme', {
            'fields': ('platform', 'federasyon_website', 'baslik', 'gorsel_onizleme', 'resim', 'kaynak_resim_url', 'icerik')
        }),
        ('Bağlantılar ve Kaynak', {
            'fields': ('kaynak_url', 'gonderi_tipi', 'paylasim_id', 'paylasim_tarihi')
        }),
        ('Onay Durumu', {
            'fields': ('onaylandi', 'reddedildi', 'onay_tarihi', 'onaylayan')
        }),
    )

    def canli_kart_onizleme(self, obj):
        return make_live_card_preview(obj)
    canli_kart_onizleme.short_description = "Canlı Kart Simülatörü"

    def gorsel_onizleme(self, obj):
        return make_image_preview(obj)
    gorsel_onizleme.short_description = "Görsel Önizlemesi"

    def delete_selected_items(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"🗑️ Seçilen {count} adet sosyal medya haberi kalıcı olarak silindi.", level='success')
    delete_selected_items.short_description = "🗑️ Seçili gönderileri tamamen sil" 

    def title_preview(self, obj):
        return obj.baslik[:60] + "..." if len(obj.baslik) > 60 else obj.baslik
    title_preview.short_description = 'Başlık'

    def onay_durumu(self, obj):
        from django.utils.html import format_html
        if obj.onaylandi:
            return format_html('<span style="color: green; font-weight: bold;">Onaylandı</span>')
        elif obj.reddedildi:
            return format_html('<span style="color: red; font-weight: bold;">Reddedildi</span>')
        return format_html('<span style="color: orange; font-weight: bold;">Bekliyor</span>')
    onay_durumu.short_description = 'Durum'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/approve-direct/', self.admin_site.admin_view(self.approve_direct), name='haberler_bekleyensosyalmedyahaberi_approve_direct'),
            path('<int:pk>/reject-direct/', self.admin_site.admin_view(self.reject_direct), name='haberler_bekleyensosyalmedyahaberi_reject_direct'),
            path('trigger-scrape-social/', self.admin_site.admin_view(self.trigger_scrape_social), name='haberler_bekleyensosyalmedya_trigger_scrape'),
        ]
        return custom_urls + urls

    def approve_direct(self, request, pk):
        obj = self.get_object(request, pk)
        if obj:
            try:
                obj.approve(request.user)
                self.message_user(request, f"'{obj.baslik[:40]}...' sosyal medya haberi başarıyla onaylandı ve Haber olarak eklendi.", level='success')
            except Exception as e:
                self.message_user(request, f"Hata: {e}", level='error')
        return redirect('admin:haberler_bekleyensosyalmedyahaberi_changelist')

    def reject_direct(self, request, pk):
        obj = self.get_object(request, pk)
        if obj:
            obj.reddedildi = True
            obj.save()
            self.message_user(request, f"'{obj.baslik[:40]}...' sosyal medya haberi reddedildi.", level='info')
        return redirect('admin:haberler_bekleyensosyalmedyahaberi_changelist')

    def trigger_scrape_social(self, request):
        from django.core.management import call_command
        import threading
        
        def run_scrape():
            try:
                call_command('tarama_sosyal_medya')
            except Exception as e:
                print(f"Social scrape error: {e}")
                
        threading.Thread(target=run_scrape).start()
        self.message_user(request, "Sosyal medya taraması arka planda başlatıldı. Yeni gönderiler birazdan eklenecektir.", level='info')
        return redirect('admin:haberler_bekleyensosyalmedyahaberi_changelist')

    def approve_selected_posts(self, request, queryset):
        success_count = 0
        error_count = 0
        for obj in queryset:
            if not obj.onaylandi and not obj.reddedildi:
                try:
                    obj.approve(request.user)
                    success_count += 1
                except Exception:
                    error_count += 1
        
        if success_count:
            self.message_user(request, f"{success_count} sosyal medya gönderisi onaylandı ve Haberlere eklendi.", level='success')
        if error_count:
            self.message_user(request, f"{error_count} gönderi onaylanırken hata oluştu.", level='error')
    approve_selected_posts.short_description = "Seçilen sosyal medya gönderilerini ONAYLA"

    def reject_selected_posts(self, request, queryset):
        updated = queryset.filter(onaylandi=False, reddedildi=False).update(reddedildi=True)
        self.message_user(request, f"{updated} sosyal medya gönderisi reddedildi.", level='info')
    reject_selected_posts.short_description = "Seçilen sosyal medya gönderilerini REDDET"

    def save_model(self, request, obj, form, change):
        """Override save to ensure proper approval workflow when manually changed via admin form"""
        if change and obj.onaylandi and not obj.onay_tarihi:
            try:
                obj.onaylandi = False
                obj.reddedildi = False
                obj.onay_tarihi = None
                obj.onaylayan = None
                super().save_model(request, obj, form, change)
                haber = obj.approve(request.user)
                self.message_user(
                    request,
                    f"✅ '{obj.baslik[:40]}...' sosyal medya haberi onaylandı ve Haber #{haber.id} olarak yayınlandı!",
                    level='success'
                )
                return
            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Onaylama sırasında hata: {e}",
                    level='error'
                )
        super().save_model(request, obj, form, change)

