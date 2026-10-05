import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Haber, Kategori, UserProfile, Favori, Yorum, KarateAntrenor, KarateKulup, KarateSehir, Kunye
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from .smart_tags import generate_smart_tags, get_airtag_id, get_airtag_shortlink
import random
import requests
from django.core.cache import cache
import json
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt

def kose_yazilari_listesi(request):
    # Kalıcı olarak yazarlar sayfasına yönlendir
    return redirect('/yazarlar/', permanent=True)

def get_editorial_feed():
    """
    SPOR24 Smart Editorial Council News Flow:
    1. Slider: Pinned news first (manset_sabitlendi=True), then manset_haberi=True within the last 48 hours,
       ordered by -olusturma_tarihi (latest push-down).
       If fewer than 15, backfills from latest 48h news so slider is always vibrant.
    2. Side Featured (3 cards): Top viewed in last 7 days, strictly excluding slider news (zero duplication).
    3. Grid Feed (Page 1): Pure 4-column feed, strictly excluding hero & side items (zero duplication).
    """
    cutoff_48h = timezone.now() - timedelta(hours=48)

    # 1. Slider news (max 15)
    slider_qs = Haber.objects.filter(
        yayinlandi=True,
        kose_yazisi=False,
        olusturma_tarihi__gte=cutoff_48h,
        manset_haberi=True
    ).select_related('kategori', 'federasyon_website').order_by('-manset_sabitlendi', '-olusturma_tarihi')[:15]
    slider_news = list(slider_qs)

    if len(slider_news) < 15:
        existing_ids = [h.id for h in slider_news]
        backfill = Haber.objects.filter(
            yayinlandi=True,
            kose_yazisi=False,
            olusturma_tarihi__gte=cutoff_48h
        ).exclude(id__in=existing_ids).select_related('kategori', 'federasyon_website').order_by('-olusturma_tarihi')[:(15 - len(slider_news))]
        slider_news.extend(list(backfill))

    if len(slider_news) < 15:
        existing_ids = [h.id for h in slider_news]
        backfill2 = Haber.objects.filter(
            yayinlandi=True,
            kose_yazisi=False
        ).exclude(id__in=existing_ids).select_related('kategori', 'federasyon_website').order_by('-olusturma_tarihi')[:(15 - len(slider_news))]
        slider_news.extend(list(backfill2))

    slider_ids = [h.id for h in slider_news]

    # 2. Side Featured (3 cards)
    side_qs = Haber.objects.filter(
        yayinlandi=True,
        kose_yazisi=False,
        olusturma_tarihi__gte=timezone.now() - timedelta(days=7)
    ).exclude(id__in=slider_ids).select_related('kategori', 'federasyon_website').order_by('-goruntulenme_sayisi', '-olusturma_tarihi')[:3]
    featured_news = list(side_qs)

    if len(featured_news) < 3:
        existing_hero = slider_ids + [h.id for h in featured_news]
        more_side = Haber.objects.filter(
            yayinlandi=True,
            kose_yazisi=False
        ).exclude(id__in=existing_hero).select_related('kategori', 'federasyon_website').order_by('-olusturma_tarihi')[:(3 - len(featured_news))]
        featured_news.extend(list(more_side))

    featured_ids = [h.id for h in featured_news]
    excluded_hero_ids = slider_ids + featured_ids

    # 3. Grid news (30 cards)
    grid_news = list(Haber.objects.filter(
        yayinlandi=True,
        kose_yazisi=False
    ).exclude(id__in=excluded_hero_ids).select_related('kategori', 'federasyon_website').order_by('-olusturma_tarihi')[:30])

    return slider_news, featured_news, grid_news

def anasayfa(request):
    """
    Renders the modern SPOR24.NET Frontend (v3/index.html) with Server-Side Rendering (SSR)
    for optimal SEO, Google News indexing, and social previews, while preserving full client-side interactivity.
    """
    try:
        slider_news, featured_news, initial_news = get_editorial_feed()

        category_colors = {
            'KARATE': 'color-cinnabar',
            'BOKS': 'color-cinnabar',
            'KİCK BOKS': 'color-cinnabar',
            'TAEKWONDO': 'color-blue-dark',
            'GÜREŞ': 'color-blue-dark',
            'JUDO': 'color-screamin-green',
            'WUSHU KUNGFU': 'color-sun-yellow',
        }

        for n in initial_news:
            n.resim_url = resolve_news_image(n)
            cat_name = (n.kategori.ad if n.kategori else 'GÜNCEL').upper()
            n.cat_name = cat_name
            n.color_class = category_colors.get(cat_name, 'color-cinnabar')

        for n in slider_news:
            n.resim_url = resolve_news_image(n)
            cat_name = (n.kategori.ad if n.kategori else 'GÜNCEL').upper()
            n.cat_name = cat_name
            n.color_class = category_colors.get(cat_name, 'color-cinnabar')

        for n in featured_news:
            n.resim_url = resolve_news_image(n)
            cat_name = (n.kategori.ad if n.kategori else 'GÜNCEL').upper()
            n.cat_name = cat_name
            n.color_class = category_colors.get(cat_name, 'color-cinnabar')

        context = {
            'slider_news': slider_news,
            'featured_news': featured_news,
            'initial_news': initial_news,
        }
        resp = render(request, 'v3/index.html', context)
        resp['Cache-Control'] = 'public, max-age=30, s-maxage=60'
        return resp
    except Exception as e:
        logger.error(f"Error in anasayfa view: {e}")
        return render(request, 'v3/index.html', {})


import re

def resolve_news_image(n):
    """
    Strictly resolves REAL database images for a news item:
    1. Direct file upload / DB resim field (VERIFIED to exist on disk)
    2. Check gorsel_url field
    3. Extract real image tag from HTML content
    4. Official Federation Logo (VERIFIED to exist on disk)
    5. Fallback to Brand Logo (/static/img/logo_5.png)
    """
    def is_valid_image(url_or_path):
        if not url_or_path:
            return False
        u = str(url_or_path).strip()
        if u.startswith('http://') or u.startswith('https://'):
            return True
        clean = u.lstrip('/')
        if clean.startswith('media/'):
            clean = clean[6:]
        disk_path = os.path.join(settings.MEDIA_ROOT, clean)
        return os.path.exists(disk_path)

    img_url = ''
    # 1. DB resim field (verified to exist on disk)
    if n.resim:
        try:
            if n.resim.name:
                clean_name = str(n.resim.name).lstrip('/')
                if clean_name.startswith('media/'):
                    clean_name = clean_name[6:]
                disk_path = os.path.join(settings.MEDIA_ROOT, clean_name)
                if os.path.exists(disk_path):
                    img_url = n.resim.url
        except Exception:
            pass

    # 2. gorsel_url field
    if not img_url and hasattr(n, 'gorsel_url') and n.gorsel_url:
        try:
            cand = str(n.gorsel_url).strip()
            if is_valid_image(cand):
                img_url = cand
        except Exception:
            pass

    # 3. HTML icerik img tag
    if not img_url and n.icerik:
        try:
            img_match = re.search(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', n.icerik, re.IGNORECASE)
            if img_match:
                cand = img_match.group(1).strip()
                if is_valid_image(cand):
                    img_url = cand
        except Exception:
            pass

    # 4. Federation logo
    if not img_url and hasattr(n, 'federasyon_website') and n.federasyon_website and n.federasyon_website.logo:
        try:
            if n.federasyon_website.logo.name:
                fed_name = str(n.federasyon_website.logo.name).lstrip('/')
                if fed_name.startswith('media/'):
                    fed_name = fed_name[6:]
                disk_path = os.path.join(settings.MEDIA_ROOT, fed_name)
                if os.path.exists(disk_path):
                    img_url = n.federasyon_website.logo.url
        except Exception:
            pass

    # 5. Fallback to Brand Logo
    if not img_url:
        img_url = '/static/img/logo_5.png'

    if img_url.startswith('/media/media/'):
        img_url = img_url.replace('/media/media/', '/media/')
    elif img_url.startswith('media/'):
        img_url = '/' + img_url

    # Cache buster for local media so any updated/regenerated image updates immediately
    if img_url.startswith('/media/'):
        clean_path = img_url[7:].split('?')[0]
        full_disk = os.path.join(settings.MEDIA_ROOT, clean_path)
        if os.path.exists(full_disk):
            try:
                mtime = int(os.path.getmtime(full_disk))
                img_url = f"{img_url.split('?')[0]}?v={mtime}"
            except Exception:
                pass

    return img_url


def resolve_author_name(n):
    name = ''
    if n.yazar:
        fn = n.yazar.get_full_name().strip()
        name = fn if fn else n.yazar.username
    else:
        name = 'Kenan ANT'

    name_lower = name.lower()
    if 'gulsen' in name_lower or 'gülşen' in name_lower:
        return 'Muhammet Kemal GÜLŞEN'
    elif 'admin' in name_lower or 'newsbot' in name_lower or 'bot' in name_lower or 'kenan' in name_lower:
        return 'Kenan ANT'
    elif 'sinan' in name_lower:
        return 'Sinan AĞLAR'
    elif 'cengiz' in name_lower or 'tuncel' in name_lower:
        return 'Cengiz TUNCEL'
    elif 'vasfi' in name_lower or 'aşçı' in name_lower or 'asci' in name_lower:
        return 'Vasfi AŞÇI'
    elif 'hasan' in name_lower or 'yetiş' in name_lower or 'yetis' in name_lower:
        return 'Hasan Hüseyin YETİŞ'
    elif 'mehmet' in name_lower or 'bozdağ' in name_lower or 'bozdag' in name_lower:
        return 'Mehmet BOZDAĞ'
    
    return name


def resolve_author_image(n):
    if n.yazar and hasattr(n.yazar, 'userprofile') and getattr(n.yazar.userprofile, 'profil_resmi', None):
        try:
            return n.yazar.userprofile.profil_resmi.url
        except Exception:
            pass

    author_name = resolve_author_name(n).lower()
    if 'sinan' in author_name:
        return '/media/profil_resimleri/yazar_sinanaglar_cropped.jpeg'
    elif 'cengiz' in author_name or 'tuncel' in author_name:
        return '/media/profil_resimleri/tuncel_GHHehan.png'
    elif 'muhammet' in author_name or 'gülşen' in author_name or 'gulsen' in author_name:
        return '/media/profil_resimleri/muhammet_kemal_gulsen.jpg'
    elif 'vasfi' in author_name or 'aşçı' in author_name or 'asci' in author_name:
        return '/media/profil_resimleri/yazar_vasfiascihotmail.com_cropped.jpeg'
    elif 'hasan' in author_name or 'yetiş' in author_name or 'yetis' in author_name:
        return '/media/profil_resimleri/yazar_Hasan_Hüseyin_Yetiş_cropped.jpeg'
    elif 'mehmet' in author_name or 'bozdağ' in author_name or 'bozdag' in author_name:
        return '/media/profil_resimleri/yazar_Kalemsor_cropped.jpeg'
    elif 'kenan' in author_name:
        return '/media/profil_resimleri/kenan_ant_avatar.jpg'

    return '/static/v3/img/author-default.jpg'


def format_news_item_dict(n):
    img_url = resolve_news_image(n)
    author_name = resolve_author_name(n)
    author_img = resolve_author_image(n)
    author_username = n.yazar.username if n.yazar else ''

    cat_display = 'GÜNCEL'
    if n.federasyon_website and n.federasyon_website.ad:
        fed_name = n.federasyon_website.ad
        clean_fed = fed_name.replace("Türkiye ", "").replace(" Federasyonu", "").replace(" (GOSBF)", "").strip()
        cat_display = clean_fed if clean_fed else fed_name
    elif n.kategori and n.kategori.ad:
        cat_display = n.kategori.ad

    return {
        'id': n.id,
        'title': n.baslik,
        'content': n.icerik,
        'image': img_url,
        'resim': img_url,
        'category_name': cat_display,
        'created_at': n.olusturma_tarihi.isoformat(),
        'is_columnist': n.kose_yazisi,
        'author_name': author_name,
        'author_username': author_username,
        'author_image': author_img,
        'is_manset': n.manset_haberi,
        'is_pinned': getattr(n, 'manset_sabitlendi', False),
        'score': getattr(n, 'haber_degeri_skoru', 0),
        'views': n.goruntulenme_sayisi or 1,
        'goruntulenme_sayisi': n.goruntulenme_sayisi or 1,
    }


def api_news(request):
    """
    Returns news JSON matching SPOR24.NET v3 structure for news-loader.js
    Enriched with 63+ Federations, Admin Ads, Polls, and Breaking News.
    Supports smart hero/slider push-down, 48h decay, and zero duplication.
    Supports real pagination for "DAHA FAZLA HABER YÜKLE".
    """
    try:
        cat_id = request.GET.get('category')
        search_q = request.GET.get('search')
        is_col_req = request.GET.get('is_columnist') == '1' or request.GET.get('columnists') == '1'

        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        try:
            page_size = int(request.GET.get('page_size', 30))
        except ValueError:
            page_size = 30

        offset = request.GET.get('offset')
        is_default_req = (not is_col_req) and (not cat_id) and (not search_q) and (page == 1) and (offset is None)

        # In-Memory Cache Strategy for Default Requests (Page 1, No Filters, No Offset)
        cache_key = f"api_news_default_ps{page_size}_v5"
        if is_default_req:
            from django.core.cache import cache
            cached_data = cache.get(cache_key)
            if cached_data:
                resp = JsonResponse(cached_data)
                resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                resp['Pragma'] = 'no-cache'
                resp['Expires'] = '0'
                return resp

        slider_items = []
        side_items = []

        if is_col_req:
            news_qs = Haber.objects.filter(yayinlandi=True, kose_yazisi=True).select_related('kategori', 'federasyon_website', 'yazar', 'yazar__userprofile').order_by('-olusturma_tarihi')
            if cat_id:
                news_qs = news_qs.filter(kategori_id=cat_id)
            if search_q:
                news_qs = news_qs.filter(Q(baslik__icontains=search_q) | Q(icerik__icontains=search_q))
                
            seen_authors = set()
            news_list = []
            for item in news_qs:
                aname = resolve_author_name(item)
                if aname not in seen_authors:
                    seen_authors.add(aname)
                    news_list.append(item)
            results = [format_news_item_dict(n) for n in news_list[:12]]
            next_url = None
        elif is_default_req:
            # Default Page 1 Homepage: Separated hero (slider + side) and grid!
            slider_news, featured_news, grid_news = get_editorial_feed()
            slider_items = [format_news_item_dict(n) for n in slider_news]
            side_items = [format_news_item_dict(n) for n in featured_news]
            results = [format_news_item_dict(n) for n in grid_news]

            excluded_hero_ids = [h.id for h in slider_news] + [h.id for h in featured_news]
            total_grid_count = Haber.objects.filter(yayinlandi=True, kose_yazisi=False).exclude(id__in=excluded_hero_ids).count()
            next_url = f"/api/news/?offset=30&page_size=30" if total_grid_count > 30 else None
        else:
            # Offset pagination or category / search filter
            if not cat_id and not search_q and offset is not None:
                cutoff_48h = timezone.now() - timedelta(hours=48)
                slider_ids = list(Haber.objects.filter(yayinlandi=True, kose_yazisi=False, olusturma_tarihi__gte=cutoff_48h, manset_haberi=True).values_list('id', flat=True)[:15])
                side_ids = list(Haber.objects.filter(yayinlandi=True, kose_yazisi=False, olusturma_tarihi__gte=timezone.now() - timedelta(days=7)).exclude(id__in=slider_ids).order_by('-goruntulenme_sayisi').values_list('id', flat=True)[:3])
                excluded_hero_ids = slider_ids + side_ids

                grid_qs = Haber.objects.filter(yayinlandi=True, kose_yazisi=False).exclude(id__in=excluded_hero_ids).select_related('kategori', 'federasyon_website', 'yazar', 'yazar__userprofile').order_by('-olusturma_tarihi')
                start_idx = int(offset)
                end_idx = start_idx + page_size
                total_count = grid_qs.count()
                news_list = list(grid_qs[start_idx:end_idx])
                results = [format_news_item_dict(n) for n in news_list]
                next_url = f"/api/news/?offset={end_idx}&page_size=30" if end_idx < total_count else None
            else:
                news_qs = Haber.objects.filter(yayinlandi=True).select_related('kategori', 'federasyon_website', 'yazar', 'yazar__userprofile').order_by('-olusturma_tarihi')
                if cat_id:
                    news_qs = news_qs.filter(kategori_id=cat_id)
                if search_q:
                    news_qs = news_qs.filter(Q(baslik__icontains=search_q) | Q(icerik__icontains=search_q))

                total_count = news_qs.count()
                start_idx = (page - 1) * page_size if offset is None else int(offset)
                end_idx = start_idx + page_size
                news_list = list(news_qs[start_idx:end_idx])
                results = [format_news_item_dict(n) for n in news_list]

                params = [f"offset={end_idx}", f"page_size={page_size}"]
                if cat_id:
                    params.append(f"category={cat_id}")
                if search_q:
                    params.append(f"search={search_q}")
                next_url = f"/api/news/?{'&'.join(params)}" if end_idx < total_count else None

        # 1. Breaking News Ticker (Latest 6 bot-scraped / published items)
        breaking_items = Haber.objects.filter(yayinlandi=True).order_by('-olusturma_tarihi')[:6]
        breaking_news = [b.baslik for b in breaking_items]

        # 2. Admin Active Ads (Both Ad and Reklam models)
        from .models import Reklam, Ad
        ads_data = {}
        for ad in Reklam.objects.filter(aktif=True):
            ads_data[ad.konum] = {
                'baslik': ad.baslik,
                'reklam_tipi': getattr(ad, 'reklam_tipi', 'gorsel'),
                'image': ad.resim.url if ad.resim else '',
                'video': ad.video.url if hasattr(ad, 'video') and ad.video else '',
                'hedef_url': ad.hedef_url or '#',
                'kod': getattr(ad, 'kod', ''),
                'iframe_url': getattr(ad, 'iframe_url', ''),
                'iframe_goster': False,
            }
        for ad in Ad.objects.filter(aktif=True):
            ads_data[ad.konum] = {
                'baslik': ad.baslik,
                'reklam_tipi': 'iframe' if ad.iframe_goster else 'gorsel',
                'image': ad.resim.url if ad.resim else '',
                'hedef_url': ad.hedef_url or '#',
                'iframe_goster': ad.iframe_goster,
            }

        # 3. Active Polls by Position
        from .models_engagement import Poll
        polls_data = {}
        for p in Poll.objects.filter(is_active=True).prefetch_related('choices'):
            polls_data[p.position] = {
                'id': p.id,
                'question': p.question,
                'position': p.position,
                'choices': [{'id': c.id, 'text': c.choice_text, 'votes': c.votes_count} for c in p.choices.all()]
            }

        response_data = {
            'results': results,
            'slider_items': slider_items,
            'side_items': side_items,
            'breaking_news': breaking_news,
            'ads': ads_data,
            'polls': polls_data,
            'poll': polls_data.get('grid_3') or polls_data.get('sidebar'),
            'next': next_url
        }

        if is_default_req:
            from django.core.cache import cache
            cache.set(cache_key, response_data, 30)

        resp = JsonResponse(response_data)
        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'
        return resp
    except Exception as e:
        import traceback
        return JsonResponse({'results': [], 'slider_items': [], 'side_items': [], 'error': str(e), 'trace': traceback.format_exc()})


def api_news_detail(request, news_id):
    """
    Returns single news item JSON matching SPOR24.NET structure for post.html
    """
    try:
        n = get_object_or_404(Haber, id=news_id, yayinlandi=True)
        img_url = resolve_news_image(n)

        author_img = '/static/v3/img/author-default.jpg'
        if n.yazar and hasattr(n.yazar, 'userprofile') and getattr(n.yazar.userprofile, 'profil_resmi', None):
            try:
                author_img = n.yazar.userprofile.profil_resmi.url
            except Exception:
                pass

        data = {
            'id': n.id,
            'slug': n.slug,
            'title': n.baslik,
            'content': n.icerik,
            'image': img_url,
            'resim': img_url,
            'category_name': n.kategori.ad if n.kategori else 'GÜNCEL',
            'source_name': getattr(n, 'kaynak_name', None) or (n.federasyon_website.ad if n.federasyon_website else 'Spor24'),
            'created_at': n.olusturma_tarihi.isoformat(),
            'is_columnist': n.kose_yazisi,
            'author_name': n.yazar.get_full_name() if (n.yazar and n.yazar.get_full_name()) else (n.yazar_adi or 'Spor24 Editör'),
            'author_image': author_img,
            'smart_tags': generate_smart_tags(n),
            'airtag_id': get_airtag_id(n),
            'airtag_shortlink': get_airtag_shortlink(n, 'direct'),
            'airtag_wa_share': get_airtag_shortlink(n, 'wa_share'),
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


def v3_post(request):
    news_id = request.GET.get('id')
    haber = None
    if news_id:
        try:
            haber = Haber.objects.select_related('kategori', 'yazar', 'federasyon_website').get(id=news_id, yayinlandi=True)
            haber.resim_url = resolve_news_image(haber)
            from django.utils.html import strip_tags
            text_source = haber.ozet or haber.icerik or haber.baslik
            haber.clean_ozet = ' '.join(strip_tags(text_source).split())[:200]
            haber.smart_tags = generate_smart_tags(haber)
            haber.airtag_id = get_airtag_id(haber)
            haber.airtag_shortlink = get_airtag_shortlink(haber, 'direct')
            haber.airtag_wa_share = get_airtag_shortlink(haber, 'wa_share')
        except Exception:
            pass
    return render(request, 'v3/post.html', {'haber': haber})


def api_categories(request):
    """
    Returns active federations count & categories for dynamic navbar populating
    """
    try:
        from .models import FederasyonWebsite
        aktif_fed_sayisi = FederasyonWebsite.objects.filter(aktif=True).count()
        toplam_fed_sayisi = FederasyonWebsite.objects.count()

        cats = Kategori.objects.all().order_by('ad')
        results = [{'id': c.id, 'name': c.ad, 'slug': c.slug} for c in cats]
        return JsonResponse({
            'results': results,
            'active_count': aktif_fed_sayisi,
            'total_count': toplam_fed_sayisi
        })
    except Exception as e:
        return JsonResponse({'results': [], 'active_count': 0, 'total_count': 0, 'error': str(e)})


@csrf_exempt
def api_log_activity(request):
    return JsonResponse({'status': 'ok'})




def _get_homepage_context(weather_data):
    from haberler.models import Reklam, Haber, Kategori
    from .models_engagement import Poll, Quiz
    
    active_poll = Poll.objects.filter(is_active=True).first()
    latest_quiz = Quiz.objects.filter(is_active=True).first()
    
    manset_haber = Haber.objects.filter(manset_haberi=True, yayinlandi=True).first()
    son_haberler = Haber.objects.filter(yayinlandi=True, kose_yazisi=False).order_by('-olusturma_tarihi')[:30]
    anasayfa_haberleri = Haber.objects.filter(yayinlandi=True).order_by('-goruntulenme_sayisi')[:5]
    son_kose_yazilari = Haber.objects.filter(yayinlandi=True, kose_yazisi=True)[:4]
    
    one_week_ago = timezone.now() - timedelta(days=7)
    weekly_news = Haber.objects.filter(
        yayinlandi=True,
        olusturma_tarihi__gte=one_week_ago
    ).exclude(resim='').order_by('-olusturma_tarihi')
    
    if weekly_news.count() < 10:
        all_recent_news = Haber.objects.filter(
            yayinlandi=True
        ).exclude(resim='').order_by('-olusturma_tarihi')[:20]
        news_list = list(all_recent_news)
        random.shuffle(news_list)
        one_cikan_haberler = news_list[:10]
    else:
        weekly_list = list(weekly_news[:20]) 
        random.shuffle(weekly_list) 
        one_cikan_haberler = weekly_list[:10] 
        
    kategoriler = Kategori.objects.filter(menude_goster=True)
    
    # Ads logic
    active_ads = Reklam.objects.filter(aktif=True)
    ads_by_position = {ad.konum: ad for ad in active_ads}
    
    # 1. Slider / Carousel (carousel_items)
    carousel_items = []
    for i, haber in enumerate(one_cikan_haberler):
        pos_num = i + 1
        if pos_num == 4 and 'manset_4' in ads_by_position:
            carousel_items.append({'type': 'ad', 'reklam': ads_by_position['manset_4']})
        elif pos_num == 8 and 'manset_8' in ads_by_position:
            carousel_items.append({'type': 'ad', 'reklam': ads_by_position['manset_8']})
        carousel_items.append({'type': 'news', 'haber': haber})
        
    # If carousel_items is empty, add fallback news
    if not carousel_items and son_haberler.exists():
        for haber in son_haberler[:5]:
            carousel_items.append({'type': 'news', 'haber': haber})
            
    # 2. Grid (grid_items)
    grid_items = []
    for i, haber in enumerate(son_haberler[:12]):
        pos_num = i + 1
        grid_pos_name = f'grid_{pos_num}'
        if grid_pos_name in ads_by_position:
            grid_items.append({'type': 'ad', 'reklam': ads_by_position[grid_pos_name]})
        grid_items.append({'type': 'news', 'haber': haber})
        
    # If grid_items is empty, add fallback news
    if not grid_items and son_haberler.exists():
        for haber in son_haberler[:6]:
            grid_items.append({'type': 'news', 'haber': haber})
            
    reklam_header = ads_by_position.get('header_ad') or ads_by_position.get('global_head')
    
    return {
        'manset_haber': manset_haber,
        'son_haberler': son_haberler,
        'anasayfa_haberleri': anasayfa_haberleri,
        'son_kose_yazilari': son_kose_yazilari,
        'one_cikan_haberler': one_cikan_haberler,
        'kategoriler': kategoriler,
        'hava_durumu': weather_data,
        'carousel_items': carousel_items,
        'grid_items': grid_items,
        'reklam_header': reklam_header,
        'active_poll': active_poll,
        'latest_quiz': latest_quiz,
    }


def haber_listesi(request):
    haberler = Haber.objects.filter(yayinlandi=True)

    paginator = Paginator(haberler, 10)
    sayfa_numarasi = request.GET.get('page')
    page_obj = paginator.get_page(sayfa_numarasi)

    weather_data = cache.get('weather_data')
    context = _get_homepage_context(weather_data)
    context['page_obj'] = page_obj

    return render(request, 'ana_sayfa.html', context)


def haber_detay(request, slug):
    # Tüm haberler (otomatik eklenenler dahil)
    haber = get_object_or_404(Haber, slug=slug, yayinlandi=True)
    
    # Görüntülenme sayısını artır
    haber.goruntulenme_sayisi += 1
    haber.save(update_fields=['goruntulenme_sayisi'])
    
    # Get favorite count for this news article
    favori_sayisi = Favori.objects.filter(haber=haber).count()
    
    # Check if current user is the author of this article
    kullanici_favori_mi = False
    if request.user.is_authenticated:
        kullanici_favori_mi = Favori.objects.filter(haber=haber, kullanici=request.user).exists()
    
    # Tüm ilgili haberler (otomatik eklenenler dahil)
    ilgili_haberler = Haber.objects.filter(
        kategori=haber.kategori, 
        yayinlandi=True
    ).exclude(id=haber.id)[:4]
    
    # Count only top-level comments (not replies)
    yorum_sayisi = Yorum.objects.filter(haber=haber, ust_yorum=None).count()
    from django.utils.html import strip_tags
    text_source = haber.ozet or haber.icerik or haber.baslik
    haber.clean_ozet = ' '.join(strip_tags(text_source).split())[:200]
    
    # 🏷️ Akıllı Takip Tagları & 📡 AirTag Entegrasyonu
    haber.smart_tags = generate_smart_tags(haber)
    haber.airtag_id = get_airtag_id(haber)
    haber.airtag_shortlink = get_airtag_shortlink(haber, 'direct')
    haber.airtag_wa_share = get_airtag_shortlink(haber, 'wa_share')
    
    context = {
        'haber': haber,
        'ilgili_haberler': ilgili_haberler,
        'kategoriler': Kategori.objects.filter(menude_goster=True),
        'favori_sayisi': favori_sayisi,
        'kullanici_favori_mi': kullanici_favori_mi,
        'yorum_sayisi': yorum_sayisi,
    }
    
    return render(request, 'v3/post.html', context)

def kategori_haberler(request, slug):
    kategori = get_object_or_404(Kategori, slug=slug)
    # Tüm haberler (otomatik eklenenler dahil)
    haberler = Haber.objects.filter(kategori=kategori, yayinlandi=True, kose_yazisi=False)
    kose_yazilari = Haber.objects.filter(kategori=kategori, yayinlandi=True, kose_yazisi=True)[:5]
    
    paginator = Paginator(haberler, 12)
    sayfa_numarasi = request.GET.get('page')
    page_obj = paginator.get_page(sayfa_numarasi)
    
    context = {
        'kategori': kategori,
        'page_obj': page_obj,
        'kose_yazilari': kose_yazilari,
        'kategoriler': Kategori.objects.filter(menude_goster=True),
    }
    
    return render(request, 'haberler/kategori_haberler.html', context)

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Use Django's authenticate function which will use our custom backend
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect based on user type
            try:
                user_profile = user.userprofile
                if user_profile.user_type == 'admin':
                    return redirect('haberler:admin_dashboard')
                elif user_profile.user_type == 'yetkili':
                    return redirect('haberler:yetkili_dashboard')
                else:  # abone
                    return redirect('haberler:abone_dashboard')
            except UserProfile.DoesNotExist:
                # If no profile exists, create one with default abone type
                UserProfile.objects.create(user=user, user_type='abone')
                return redirect('haberler:abone_dashboard')
        else:
            messages.error(request, 'Geçersiz e-posta adresi veya şifre.' if '@' in username else 'Geçersiz kullanıcı adı veya şifre.')
    
    return render(request, 'auth/login.html')

def custom_logout(request):
    logout(request)
    next_url = request.GET.get('next', '/yetkili-giris/')
    return redirect(next_url)

def register(request):
    if request.method == 'POST':
        # Debug: Print all POST data
        print("POST data:", request.POST)
        
        user_type = request.POST.get('user_type', 'abone')
        print("User type:", user_type)
        
        # Get fields based on user type
        if user_type == 'yetkili':
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('yetkili_email', '')
            password1 = request.POST.get('yetkili_password1', '')
            password2 = request.POST.get('yetkili_password2', '')
            # For yetkililer, username will be first name + last name
            username = f"{first_name} {last_name}".strip()
        elif user_type == 'admin':
            # For administrators, use the standard username field
            username = request.POST.get('abone_username', '')
            email = request.POST.get('abone_email', '')
            password1 = request.POST.get('abone_password1', '')
            password2 = request.POST.get('abone_password2', '')
            first_name = ''
            last_name = ''
        else:  # abone or any other type
            username = request.POST.get('abone_username', '')
            email = request.POST.get('abone_email', '')
            password1 = request.POST.get('abone_password1', '')
            password2 = request.POST.get('abone_password2', '')
            first_name = ''
            last_name = ''
        
        print(f"Username: {username}, Email: {email}, Password1: {password1}, Password2: {password2}")
        print(f"First name: {first_name}, Last name: {last_name}")
        
        if password1 != password2:
            messages.error(request, 'Şifreler eşleşmiyor.')
            return render(request, 'auth/register.html')
        
        if not username:
            messages.error(request, 'Kullanıcı adı gereklidir.')
            return render(request, 'auth/register.html')
            
        if not email:
            messages.error(request, 'Email adresi gereklidir.')
            return render(request, 'auth/register.html')
            
        if not password1:
            messages.error(request, 'Şifre gereklidir.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu kullanıcı adı zaten alınmış.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Bu email zaten kullanımda.')
            return render(request, 'auth/register.html')
        
        # Create user
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            print("User created successfully:", user)
        except Exception as e:
            messages.error(request, f'Kullanıcı oluşturulurken bir hata oluştu: {str(e)}')
            return render(request, 'auth/register.html')
        
        # Set first and last name for yetkili users
        if user_type == 'yetkili' and first_name and last_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            print("First and last name set for yetkili user")
        
        # Create or update user profile
        try:
            user_profile, created = UserProfile.objects.get_or_create(user=user, defaults={'user_type': user_type})
            if not created:
                # If profile already existed, update the user_type
                user_profile.user_type = user_type
                user_profile.save()
        except Exception as e:
            messages.error(request, f'Kullanıcı profili oluşturulurken bir hata oluştu: {str(e)}')
            return render(request, 'auth/register.html')
        
        user_profile.save()
        print("User profile saved:", user_profile)
        
        # Redirect to login page with user_type parameter
        if user_type == 'yetkili':
            response = redirect('haberler:custom_login' + '?user_type=yetkili')
        elif user_type == 'abone':
            response = redirect('haberler:custom_login' + '?user_type=abone')
        else:
            response = redirect('haberler:custom_login')
        
        # Add success message after redirect to avoid conflicts
        messages.success(request, 'Hesabınız oluşturuldu. Şimdi giriş yapabilirsiniz.')
        return response
    
    return render(request, 'auth/register.html')

@login_required
def admin_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'admin':
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    
    # Get dashboard statistics (including all news)
    total_haberler = Haber.objects.count()
    total_kategoriler = Kategori.objects.count()
    total_kullanicilar = User.objects.count()
    total_aboneler = UserProfile.objects.filter(user_type='abone').count()
    total_yetkililer = UserProfile.objects.filter(user_type='yetkili').count()
    
    context = {
        'user_type': 'Yönetici',
        'dashboard_title': 'Yönetici Paneli',
        'permissions': ['Tüm haberleri düzenleme', 'Kullanıcı yönetimi', 'Kategori yönetimi', 'Sistem ayarları'],
        'total_haberler': total_haberler,
        'total_kategoriler': total_kategoriler,
        'total_kullanicilar': total_kullanicilar,
        'total_aboneler': total_aboneler,
        'total_yetkililer': total_yetkililer,
    }
    return render(request, 'auth/dashboard_admin.html', context)

@login_required
def yetkili_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'yetkili':
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    
    # Get user's news and opinion articles
    user_haberler = Haber.objects.filter(yazar=request.user, kose_yazisi=False).count()
    user_kose_yazilari = Haber.objects.filter(yazar=request.user, kose_yazisi=True).count()
    
    context = {
        'user_type': 'Yetkili',
        'dashboard_title': 'Yetkili Paneli',
        'permissions': ['Haber ekleme', 'Kendi haberlerini düzenleme', 'Köşe yazısı ekleme', 'Kendi köşe yazılarını düzenleme', 'Yorum yönetimi'],
        'user_haberler': user_haberler,
        'user_kose_yazilari': user_kose_yazilari
    }
    return render(request, 'auth/dashboard_yetkili.html', context)

@login_required
def abone_dashboard(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'abone':
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    
    # Get user's reading stats
    okunan_haber_sayisi = 42  # This would need to be implemented based on actual reading history
    yorum_sayisi = Yorum.objects.filter(yazar=request.user).count()
    favori_sayisi = Favori.objects.filter(kullanici=request.user).count()
    kategori_sayisi = 5  # This could be dynamic based on user preferences
    
    context = {
        'user_type': 'Abone',
        'dashboard_title': 'Abone Paneli',
        'permissions': ['Haber okuma', 'Yorum yapma', 'Profil yönetimi'],
        'okunan_haber_sayisi': okunan_haber_sayisi,
        'yorum_sayisi': yorum_sayisi,
        'favori_sayisi': favori_sayisi,
        'kategori_sayisi': kategori_sayisi,
    }
    return render(request, 'auth/dashboard_abone.html', context)

def haber_arama(request):
    query = request.GET.get('q', '')
    haberler = []
    kategoriler = Kategori.objects.filter(menude_goster=True)
    
    if query:
        # Search in news titles, content, and summaries
        haberler = Haber.objects.filter(
            yayinlandi=True
        ).filter(
            Q(baslik__icontains=query) | 
            Q(ozet__icontains=query) | 
            Q(icerik__icontains=query)
        )
    
    context = {
        'query': query,
        'haberler': haberler,
        'kategoriler': kategoriler,
    }
    
    return render(request, 'haberler/arama_sonuclari.html', context)

# --- Statik Sayfa Fonksiyonları ---

def hakkimizda(request):
    return render(request, 'pages/hakkimizda.html')

def iletisim(request):
    return render(request, 'pages/iletisim.html')

def gizlilik_politikasi(request):
    return render(request, 'pages/gizlilik.html')

def kullanim_sartlari(request):
    return render(request, 'pages/kullanim.html')
def video_sayfasi(request):
    return redirect('/#spor24-live-tv-section', permanent=True)
def kunye(request):
    import re
    kunye_bilgisi = Kunye.objects.first()
    staff = []
    if kunye_bilgisi and kunye_bilgisi.editorler:
        for line in kunye_bilgisi.editorler.splitlines():
            line = line.strip()
            if not line or 'Adı Soyadı' in line or 'Görev' in line:
                continue
            parts = [p.strip() for p in re.split(r'\s{2,}|\t+', line) if p.strip()]
            if len(parts) >= 2:
                staff.append({'name': parts[0], 'role': parts[1]})
            elif len(parts) == 1:
                staff.append({'name': parts[0], 'role': 'Editör'})
    return render(request, 'pages/kunye.html', {'kunye': kunye_bilgisi, 'staff': staff})

# Karate Bölümü İçin Fonksiyonlar
def karate_antrenorler(request):
    from django.db.models import Count
    # 1. HARİTA VERİSİ (Şehirlere göre sayıları al)
    sehir_verileri = KarateAntrenor.objects.values('sehir__ad').annotate(toplam=Count('id')).order_by('sehir__ad')

    # Harita boyama için JSON verisi hazırla
    harita_dict = {}
    for veri in sehir_verileri:
        if veri['sehir__ad']:
            sehir_adi = veri['sehir__ad'].strip().upper()
            harita_dict[sehir_adi] = veri['toplam']
    
    harita_json = json.dumps(harita_dict, ensure_ascii=False)

    # 2. FİLTRELEME MANTIĞI
    # Varsayılan sıralama: Şehir ve İsim
    antrenor_listesi = KarateAntrenor.objects.select_related('sehir').all().order_by('sehir__ad', 'ad_soyad')

    # A) İsim Arama (HTML'deki name='q')
    arama_kelimesi = request.GET.get('q')
    if arama_kelimesi:
        antrenor_listesi = antrenor_listesi.filter(ad_soyad__icontains=arama_kelimesi)

    # B) Şehir Filtresi (HTML'deki name='sehir')
    secilen_sehir = request.GET.get('sehir')
    if secilen_sehir and secilen_sehir != "Tüm Şehirler":
        antrenor_listesi = antrenor_listesi.filter(sehir__ad=secilen_sehir)

    # C) Kademe Filtresi (HTML'deki name='kademe')
    secilen_kademe = request.GET.get('kademe')
    if secilen_kademe and secilen_kademe != "Tüm Kademeler":
        antrenor_listesi = antrenor_listesi.filter(kademe=secilen_kademe)

    # 3. DROPDOWN MENÜLERİNİ DOLDUR
    sehirler_listesi = list(KarateSehir.objects.values_list('ad', flat=True).order_by('ad'))
    if not sehirler_listesi:
        sehirler_listesi = list(KarateAntrenor.objects.exclude(sehir__isnull=True).values_list('sehir__ad', flat=True).distinct())

    def tr_sirala(text):
        if not text: return ""
        ceviri = str.maketrans("ÇĞİÖŞÜ", "CGIOSU")
        return text.translate(ceviri)

    tum_sehirler = sorted([s for s in sehirler_listesi if s], key=tr_sirala)
    tum_kademeler = KarateAntrenor.objects.exclude(kademe__isnull=True).exclude(kademe='').values_list('kademe', flat=True).distinct().order_by('kademe')

    # 4. SAYFALAMA (Her sayfada 50 kişi)
    paginator = Paginator(antrenor_listesi, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'tum_sehirler': tum_sehirler,
        'tum_kademeler': tum_kademeler,
        'harita_json': harita_json,
    }

    return render(request, 'haberler/karate_antrenorler.html', context)

def karate_kulupler(request):
    # Kulüpleri listele
    secilen_sehir = request.GET.get('sehir')
    q = request.GET.get('q')
    
    kulup_listesi = KarateKulup.objects.select_related('sehir').all()
    if secilen_sehir and secilen_sehir != "Tüm Şehirler":
        kulup_listesi = kulup_listesi.filter(sehir__ad__iexact=secilen_sehir)
    if q:
        kulup_listesi = kulup_listesi.filter(ad__icontains=q)
        
    kulup_listesi = kulup_listesi.order_by('sehir__ad', 'ad')
    
    paginator = Paginator(kulup_listesi, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    tum_sehirler = list(KarateSehir.objects.values_list('ad', flat=True).order_by('ad'))
    
    return render(request, 'haberler/karate_kulupler.html', {
        'page_obj': page_obj,
        'tum_sehirler': tum_sehirler,
        'secilen_sehir': secilen_sehir
    })
def karate_formlari(request):
    return render(request, 'karate_formlari.html')

def anasayfa_v2(request):
    # Modern tasarım için test view'ı
    weather_data = cache.get('weather_data')
    if not weather_data:
        API_KEY = "0eee6a155bbb6dbed48dd8f58805f850"
        city = "Ankara"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=tr"
        try:
            current_weather_data = None
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            weather_data = {
                'city': city,
                'temperature': round(data['main']['temp']),
                'description': data['weather'][0]['description'].capitalize(),
                'icon': data['weather'][0]['icon']
            }
            cache.set('weather_data', weather_data, 3600)  # 1 saat cache
        except Exception as e:
            print(f"Hava durumu hatası: {e}")
            weather_data = None

    # Veri Çekme Bölümü
    # 1. Ana Manşet Slider (manset_haberi=True olanlar)
    manset_haberler = Haber.objects.filter(manset_haberi=True, yayinlandi=True).order_by('-olusturma_tarihi')[:15]
    
    # 2. Yan Manşet / Sağ Slider (manset olmayan, son haberler)
    # Manşettekileri hariç tutmak için exclude kullanabiliriz.
    yan_manset_haberler = Haber.objects.filter(yayinlandi=True).exclude(id__in=manset_haberler.values_list('id', flat=True)).order_by('-olusturma_tarihi')[:5]
    
    # 3. Alt Grid Haberler (yan manşet ve manşet dışındakiler)
    excluded_ids = list(manset_haberler.values_list('id', flat=True)) + list(yan_manset_haberler.values_list('id', flat=True))
    grid_haberler = Haber.objects.filter(yayinlandi=True).exclude(id__in=excluded_ids).order_by('-olusturma_tarihi')[:12]

    # 4. Köşe Yazıları
    son_kose_yazilari = Haber.objects.filter(yayinlandi=True, kose_yazisi=True)[:4]

    # 5. Kategoriler
    kategoriler = Kategori.objects.filter(menude_goster=True)

    context = {
        'manset_haberler': manset_haberler,
        'yan_manset_haberler': yan_manset_haberler,
        'grid_haberler': grid_haberler,
        'son_kose_yazilari': son_kose_yazilari,
        'kategoriler': kategoriler,
        'hava_durumu': weather_data,
    }
    return render(request, 'home_modern.html', context)


def anasayfa_v3(request):
    """
    Eski NewsBit v3 tasarımı kalıcı olarak ana sayfaya yönlendirildi (SEO 301).
    """
    return redirect('/', permanent=True)


def reklam_proxy(request):
    """
    Proxies external ad URLs to bypass X-Frame-Options/CSP restrictions.
    Allows framing websites that set X-Frame-Options: DENY.
    """
    import urllib.request
    import urllib.parse
    import ssl
    from django.http import HttpResponse, Http404
    
    url = request.GET.get('url')
    if not url:
        raise Http404("URL parametresi eksik.")
        
    # Güvenlik Kontrolü: Yalnızca aktif reklamlarımızda kayıtlı olan URL'lere izin ver
    from .models import Reklam
    allowed = Reklam.objects.filter(iframe_url=url, aktif=True).exists()
    if not allowed:
        # fallback control: also check if it is set as target_url
        allowed = Reklam.objects.filter(hedef_url=url, aktif=True).exists()
        
    if not allowed:
        raise Http404("Yetkisiz proxy isteği.")
        
    try:
        # SSL doğrulamasını devre dışı bırakarak en esnek şekilde bağlanalım
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            content_type = response.headers.get('Content-Type', 'text/html')
            content = response.read()
            
            if 'text/html' in content_type:
                # İframe içindeki görece (relative) yolların hedef siteden çekilebilmesi için <base> etiketi enjekte edelim
                html = content.decode('utf-8', errors='ignore')
                
                parsed = urllib.parse.urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                
                # Base etiketini head taginin hemen sonrasına ekliyoruz
                base_tag = f'\n<base href="{base_url}/">\n'
                if '<head>' in html:
                    html = html.replace('<head>', f'<head>{base_tag}', 1)
                elif '<HEAD>' in html:
                    html = html.replace('<HEAD>', f'<HEAD>{base_tag}', 1)
                else:
                    html = f'{base_tag}{html}'
                
                content = html.encode('utf-8')
                
            django_response = HttpResponse(content, content_type=content_type)
            
            # X-Frame-Options engellerini kaldırıp tarayıcıya serbestçe yükleme yetkisi verelim
            django_response['X-Frame-Options'] = 'ALLOWALL'
            if 'Content-Security-Policy' in django_response:
                del django_response['Content-Security-Policy']
                
            return django_response
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Reklam proxy hatası ({url}): {e}")
        return HttpResponse(f"Dış sayfa yüklenemedi: {e}", status=502)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from difflib import SequenceMatcher
from .models import FederasyonWebsite, Kategori, BekleyenHaber, Haber

def validate_api_key(request):
    """Checks if X-API-Key header matches configured API_SECRET_KEY"""
    secret_key = getattr(settings, 'API_SECRET_KEY', None)
    if not secret_key:
        return False
    request_key = request.headers.get('X-API-Key') or request.META.get('HTTP_X_API_KEY')
    return request_key == secret_key

def api_federasyonlar(request):
    """GET endpoint: returns active federations with their scraping configurations"""
    if not validate_api_key(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    federations = FederasyonWebsite.objects.filter(aktif=True)
    data = []
    for fed in federations:
        try:
            sosyal = fed.sosyal_medya
            instagram = sosyal.instagram_kullanici_adi or ""
            facebook = sosyal.facebook_sayfasi or ""
            twitter = sosyal.x_sayfasi or ""
        except Exception:
            instagram = ""
            facebook = ""
            twitter = ""
            
        data.append({
            'id': fed.id,
            'ad': fed.ad,
            'ana_url': fed.ana_url,
            'haberler_url': fed.haberler_url,
            'haber_listesi_selector': fed.haber_listesi_selector,
            'haber_baslik_selector': fed.haber_baslik_selector,
            'haber_link_selector': fed.haber_link_selector,
            'haber_tarih_selector': fed.haber_tarih_selector,
            'haber_ozet_selector': fed.haber_ozet_selector,
            'instagram_kullanici_adi': instagram,
            'facebook_sayfasi': facebook,
            'x_sayfasi': twitter,
        })
    return JsonResponse(data, safe=False)

@csrf_exempt

def is_valid_news_candidate(title, url, content_text=None):
    """
    Gatekeeper validation: Protects Spor24 against junk news, static menus,
    board member emails, and outdated archives (e.g. 2022).
    """
    if not url or not url.lower().startswith(('http://', 'https://')):
        return False, "invalid_url_protocol"

    t = (title or '').strip()
    if len(t) < 10 or len(t.split()) < 2:
        return False, "title_too_short_or_single_word"

    t_lower = t.lower()
    url_lower = url.lower()

    # 1. Banned navigation menu titles
    banned_keywords = [
        'haberler', 'duyurular', 'faaliyetler', 'faaliyet programı', 'faaliyet takvimi',
        'yönetim kurulu', 'denetim kurulu', 'disiplin kurulu', 'kurullar', 'başkanlarımız',
        'tarihçe', 'misyon & vizyon', 'misyon ve vizyon', 'iletişim', 'foto galeri',
        'video galeri', 'şampiyonalar', 'türkiye şampiyonaları', 'kulüplerimiz',
        'hakemlerimiz', 'antrenörlerimiz', 'mevzuat', 'talimatlar', 'ana sayfa',
        'anasayfa', 'uluslararası kendo federasyonu', 'avrupa kendo federasyonu',
        'twf bilgi sistemi', 'vize seminerleri', 'gizlilik politikası', 'kvkk'
    ]
    for bk in banned_keywords:
        if t_lower == bk or t_lower.startswith(f"{bk} ") or t_lower.endswith(f" {bk}"):
            return False, f"banned_menu_keyword_{bk}"

    # 2. Reject past year archives (Current year is 2026)
    past_years = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']
    for py in past_years:
        if f"{py} faaliyet" in t_lower or f"{py} arşivi" in t_lower:
            return False, f"past_year_archive_{py}"
        if f"/{py}-faaliyet" in url_lower or f"/{py}-arsiv" in url_lower:
            return False, f"past_year_url_{py}"

    # 3. Reject pure directory / listing URLs
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    clean_path = parsed.path.strip('/')
    if clean_path in ['', 'haberler', 'duyurular', 'news', 'announcements', 'category/genel']:
        return False, "category_listing_url"

    return True, "valid"

def api_bekleyen_haber_ekle(request):
    """POST endpoint: receives news item, runs de-duplication, inserts it, triggers Telegram notification"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    if not validate_api_key(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
        
    fed_id = body.get('federation_id')
    title = body.get('title')
    summary = body.get('summary', '')
    content = body.get('content', '')
    url = body.get('url')
    image_url = body.get('image_url')
    
    # New category fields for better flexibility (e.g. for GOSBF subcategories like Sambo, Savate)
    category_id = body.get('category_id')
    category_slug = body.get('category_slug')
    
    if not all([fed_id, title, url]):
        return JsonResponse({'error': 'Missing required fields (federation_id, title, url)'}, status=400)
        
    try:
        federation = FederasyonWebsite.objects.get(id=fed_id)
    except FederasyonWebsite.DoesNotExist:
        return JsonResponse({'error': 'Federation website does not exist'}, status=400)
        
    # Check if duplicate in published news
    if Haber.objects.filter(kaynak_url=url).exists():
        return JsonResponse({'status': 'skipped', 'reason': 'already_published'})
        
    # Gatekeeper check: validate title, url, and relevance
    is_valid, reject_reason = is_valid_news_candidate(title, url, content)
    if not is_valid:
        return JsonResponse({'status': 'rejected', 'reason': reject_reason, 'message': f'Rejected by Gatekeeper: {reject_reason}'}, status=400)

    # Check if duplicate in pending news
    if BekleyenHaber.objects.filter(kaynak_url=url).exists():
        return JsonResponse({'status': 'skipped', 'reason': 'already_pending'})
        
    # Resolve the correct category
    category = None
    if category_id:
        category = Kategori.objects.filter(id=category_id).first()
    elif category_slug:
        category = Kategori.objects.filter(slug=category_slug).first()
        
    # Fallback to the first category associated with the federation
    if not category:
        category = Kategori.objects.filter(federasyon_website=federation).first()
        
    # Check title similarity (85%) within this category
    if category:
        recent_published = list(Haber.objects.filter(kategori=category).order_by('-olusturma_tarihi')[:30].values_list('baslik', flat=True))
        recent_pending = list(BekleyenHaber.objects.filter(federasyon_website=federation, kategori=category).order_by('-olusturma_tarihi')[:30].values_list('baslik', flat=True))
        
        for existing_title in recent_published + recent_pending:
            ratio = SequenceMatcher(None, title.lower(), existing_title.lower()).ratio()
            if ratio >= 0.85:
                return JsonResponse({'status': 'skipped', 'reason': 'duplicate_title_similarity', 'similarity_ratio': ratio})
                
    # Sanitize & Clean content using trafilatura if navigation junk detected or content too short
    if url and url.startswith('http'):
        has_nav_junk = any(k in (content or '') for k in ['Ana Sayfa', 'E-Turnuva', 'Bakanımız', 'Yönetim Kurulu', 'Skip to content', 'Misyon & Vizyon'])
        if has_nav_junk or len((content or '').strip()) < 80:
            try:
                import trafilatura
                downloaded = trafilatura.fetch_url(url)
                if not downloaded:
                    import requests
                    downloaded = requests.get(url, verify=False, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}).text
                if downloaded:
                    clean_extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
                    if clean_extracted and len(clean_extracted.strip()) > 60:
                        content = clean_extracted.strip()
                        summary = content[:200] + ('...' if len(content) > 200 else '')
            except Exception:
                pass

    video_url = body.get('video_url')
    is_video = body.get('is_video', False)
    scraper_name = body.get('scraper_name')

    # Create the pending news item with resolved category
    pending = BekleyenHaber.objects.create(
        baslik=title,
        ozet=summary or title,
        icerik=content or summary or title,
        kaynak_url=url,
        kaynak_resim_url=image_url,
        video_url=video_url,
        is_video=is_video,
        federasyon_website=federation,
        kategori=category
    )
    
    # Trigger Telegram notifications asynchronously so scraper pushes never block web workers!
    try:
        import threading
        def _bg_send_news_notif(news_payload):
            try:
                from .services.notification_service import NotificationService
                NotificationService().send_new_news_notifications([news_payload])
            except Exception as ex:
                logger.error(f"Async news notification error: {ex}")

        threading.Thread(target=_bg_send_news_notif, args=({
            'id': pending.id,
            'federation': federation.ad,
            'title': title,
            'url': url,
            'image_url': image_url,
            'video_url': video_url,
            'is_video': is_video,
            'scraper_name': scraper_name
        },), daemon=True).start()
        telegram_sent = True
    except Exception as e:
        telegram_sent = False
        print(f"Error dispatching background Telegram notification: {e}")
        
    return JsonResponse({
        'status': 'created',
        'pending_id': pending.id,
        'telegram_notification': telegram_sent
    }, status=201)

@csrf_exempt
def api_bekleyen_sosyal_medya_ekle(request):
    """POST endpoint: receives social media post, runs de-duplication, inserts it, triggers Telegram notification"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    if not validate_api_key(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
        
    platform = body.get('platform')
    fed_id = body.get('federation_id')
    post_id = body.get('post_id')
    title = body.get('title')
    content = body.get('content', '')
    url = body.get('url')
    image_url = body.get('image_url')
    gonderi_tipi = body.get('gonderi_tipi', 'post')
    
    if not all([platform, fed_id, post_id, title, url]):
        return JsonResponse({'error': 'Missing required fields (platform, federation_id, post_id, title, url)'}, status=400)
        
    if platform not in ['instagram', 'twitter', 'facebook']:
        return JsonResponse({'error': 'Invalid platform. Must be instagram, twitter, or facebook'}, status=400)
        
    try:
        federation = FederasyonWebsite.objects.get(id=fed_id)
    except FederasyonWebsite.DoesNotExist:
        return JsonResponse({'error': 'Federation website does not exist'}, status=400)
        
    # Check if duplicate in pending social media posts
    from .models import BekleyenSosyalMedyaHaberi
    if BekleyenSosyalMedyaHaberi.objects.filter(paylasim_id=post_id).exists():
        return JsonResponse({'status': 'skipped', 'reason': 'already_pending_social'})
        
    # Check if duplicate in published news (using kaynak_url)
    if Haber.objects.filter(kaynak_url=url).exists():
        return JsonResponse({'status': 'skipped', 'reason': 'already_published_news'})
        
    # Create the pending social media post
    pending = BekleyenSosyalMedyaHaberi.objects.create(
        platform=platform,
        federasyon_website=federation,
        paylasim_id=post_id,
        baslik=title,
        icerik=content or title,
        kaynak_url=url,
        kaynak_resim_url=image_url,
        gonderi_tipi=gonderi_tipi
    )
    
    # Trigger Telegram notifications asynchronously so scraper pushes never block web workers!
    try:
        import threading
        def _bg_send_social_notif(social_payload):
            try:
                from .services.notification_service import NotificationService
                NotificationService().send_social_media_notifications([social_payload])
            except Exception as ex:
                logger.error(f"Async social notification error: {ex}")

        threading.Thread(target=_bg_send_social_notif, args=({
            'id': pending.id,
            'platform': platform,
            'federation': federation.ad,
            'title': title,
            'content': content,
            'url': url,
            'image_url': image_url,
            'gonderi_tipi': gonderi_tipi
        },), daemon=True).start()
        telegram_sent = True
    except Exception as e:
        telegram_sent = False
        print(f"Error dispatching background social Telegram notification: {e}")
        
    return JsonResponse({
        'status': 'created',
        'pending_id': pending.id,
        'telegram_notification': telegram_sent
    }, status=201)

from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.contrib.auth.models import User
from .models import BultenAbone

def yazarlar_listesi(request):
    """View to list all active columnists/editors in modern v3 design"""
    excluded_usernames = [
        'newsbot', 'socialbot', 'karatebot', 'kose_yazari', 'federation_importer', 
        'karate_importer', 'karate_full_importer', 'multi_federation_importer', 
        'boks_importer', 'wushu_duyuru_importer', 'wushu_importer', 'boxing_importer', 
        'mma_scraper', 'gures_scraper', 'mmafederasyonu', 'yetkili', 'Yetkili User', 
        'abone', 'Antknight', 'Kenan ANT', 'Kenan ANT 1', 'kenan_ant_main', 'vasfiasci41'
    ]
    
    raw_yazarlar = list(User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(userprofile__user_type='yetkili') | Q(haber__isnull=False)
    ).exclude(username__in=excluded_usernames).distinct().annotate(
        haber_sayisi=Count('haber', filter=Q(haber__kose_yazisi=False)),
        yazi_sayisi=Count('haber', filter=Q(haber__kose_yazisi=True))
    ).order_by('-yazi_sayisi', '-haber_sayisi'))
    
    filtered_yazarlar = []
    seen_names = set()
    for yazar in raw_yazarlar:
        full_n = yazar.get_full_name().strip()
        if not full_n or full_n in ['Test User', 'Pasif User']:
            continue
        if (yazar.yazi_sayisi > 0 or yazar.haber_sayisi > 0 or yazar.is_staff) and full_n not in seen_names:
            seen_names.add(full_n)
            filtered_yazarlar.append(yazar)
            
    for yazar in filtered_yazarlar:
        img = ''
        if hasattr(yazar, 'userprofile') and yazar.userprofile:
            if hasattr(yazar.userprofile, 'profil_resmi') and yazar.userprofile.profil_resmi:
                try:
                    img = yazar.userprofile.profil_resmi.url
                except Exception:
                    img = str(yazar.userprofile.profil_resmi)
            elif hasattr(yazar.userprofile, 'avatar') and yazar.userprofile.avatar:
                try:
                    img = yazar.userprofile.avatar.url
                except Exception:
                    img = str(yazar.userprofile.avatar)
        
        if not img:
            latest_h = Haber.objects.filter(yazar=yazar).exclude(resim='').exclude(resim__isnull=True).order_by('-olusturma_tarihi').first()
            if latest_h and latest_h.resim:
                try:
                    img = latest_h.resim.url
                except Exception:
                    img = str(latest_h.resim)
                    
        yazar.resolved_image = img if img else '/static/v3/img/author-default.jpg'
    
    context = {
        'yazarlar': filtered_yazarlar
    }
    return render(request, 'v3/yazarlar_listesi.html', context)

def yazar_detay(request, username):
    """View to display detailed author profile with fast 20-item pagination and perfect image resolution"""
    yazar = get_object_or_404(User, username=username)
    
    # Combined queryset of author's articles & column posts, ordered by date
    icerik_qs = Haber.objects.filter(yazar=yazar, yayinlandi=True).select_related('kategori').order_by('-olusturma_tarihi')
    toplam_icerik = icerik_qs.count()
    kose_yazisi_sayisi = Haber.objects.filter(yazar=yazar, kose_yazisi=True, yayinlandi=True).count()
    haber_sayisi = toplam_icerik - kose_yazisi_sayisi

    page_number = request.GET.get('page', 1)
    paginator = Paginator(icerik_qs, 20)  # 20 items per page
    page_obj = paginator.get_page(page_number)

    # Attach resolved image URL to each item in current page
    for item in page_obj:
        item.resim_url = resolve_news_image(item)

    # If AJAX request or format=json, return JSON for "Load More" button
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        items = []
        for item in page_obj:
            items.append({
                'id': item.id,
                'baslik': item.baslik,
                'resim_url': item.resim_url,
                'kategori_ad': item.kategori.ad if item.kategori else ('KÖŞE YAZISI' if item.kose_yazisi else 'GÜNCEL'),
                'is_kose_yazisi': item.kose_yazisi,
                'tarih': item.olusturma_tarihi.strftime('%d.%m.%Y') if item.olusturma_tarihi else '',
                'goruntulenme': item.goruntulenme_sayisi
            })
        return JsonResponse({
            'items': items,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None
        })

    context = {
        'yazar_user': yazar,
        'page_obj': page_obj,
        'toplam_icerik': toplam_icerik,
        'kose_yazisi_sayisi': kose_yazisi_sayisi,
        'haber_sayisi': haber_sayisi,
    }
    return render(request, 'v3/author.html', context)

def bulten_olustur(request):
    """AJAX view to subscribe email to newsletter"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Gecersiz istek metodu.'}, status=405)
        
    eposta = request.POST.get('eposta', '').strip()
    telefon = request.POST.get('telefon', '').strip()
    isim = request.POST.get('isim', '').strip()
    soyisim = request.POST.get('soyisim', '').strip()
    kullanici_adi = request.POST.get('kullanici_adi', '').strip()
    
    if not eposta:
        return JsonResponse({'status': 'error', 'message': 'E-posta adresi gereklidir.'}, status=400)
        
    if BultenAbone.objects.filter(eposta=eposta).exists():
        return JsonResponse({'status': 'exists', 'message': 'Bu e-posta adresi zaten bultenimize kayitli.'})
        
    try:
        BultenAbone.objects.create(
            eposta=eposta,
            telefon=telefon,
            isim=isim,
            soyisim=soyisim,
            kullanici_adi=kullanici_adi
        )
        return JsonResponse({'status': 'success', 'message': 'Bultene basariyla kayit oldunuz!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Kayit sirasinda hata olustu: {str(e)}'}, status=500)


@csrf_exempt
def telegram_webhook(request):
    """
    Telegram Webhook Endpoint for @gazi_gucu_sporcu_bot and general Telegram Webhooks.
    Responds with HTTP 200 OK to Telegram server.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'ok', 'message': 'Telegram Webhook Listener Active (POST expected)'})
        
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        # 1. Handle Callback Query
        callback_query = data.get('callback_query')
        if callback_query:
            cq_id = callback_query.get('id')
            cq_data = callback_query.get('data', '')
            BOT_TOKEN = os.getenv("GAZI_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", ""))
            import requests
            try:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                    json={"callback_query_id": cq_id, "text": "✅ İşlem alındı!"},
                    timeout=5
                )
            except Exception:
                pass
            return JsonResponse({'status': 'ok', 'type': 'callback_query'})

        # 2. Handle Message
        message = data.get('message')
        if message:
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            if chat_id and text:
                BOT_TOKEN = os.getenv("GAZI_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", ""))
                import requests
                reply_text = (
                    "🥋 <b>Gazi Gücü Spor Kulübü Otomasyon Botu</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "Hoş geldiniz! Sporcu lisans doğrulama ve kulüp sistemi aktif.\n\n"
                    "💡 Sporcu T.C. Kimlik No veya Ad-Soyad yazarak arama yapabilirsiniz."
                )
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text, "parse_mode": "HTML"},
                        timeout=5
                    )
                except Exception:
                    pass
                return JsonResponse({'status': 'ok', 'type': 'message'})

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'ok', 'note': str(e)})


def yetkili_giris(request):
    """View to provide a dedicated, branded Yetkili / Yazar Login and Status page"""
    error_message = None
    
    if request.method == 'POST':
        username_val = request.POST.get('username', '').strip()
        password_val = request.POST.get('password', '').strip()
        
        if username_val and password_val:
            user = authenticate(request, username=username_val, password=password_val)
            if user is not None:
                if user.is_active and (user.is_staff or user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.user_type in ['admin', 'yetkili'])):
                    login(request, user)
                    return redirect('haberler:yetkili_dashboard')
                else:
                    error_message = "Hesabınız yetkili panel erişimine uygun değil veya pasif."
            else:
                error_message = "Kullanıcı adı veya şifre hatalı!"
        else:
            error_message = "Lütfen kullanıcı adı ve şifrenizi girin."
            
    context = {
        'is_logged_in': request.user.is_authenticated,
        'current_user': request.user if request.user.is_authenticated else None,
        'error_message': error_message
    }
    return render(request, 'v3/yetkili_giris.html', context)


def api_columnists(request):
    """
    API endpoint serving real columnists and column articles for the mobile app (ColumnistsScreen.tsx)
    and web frontends.
    """
    from django.db.models import Count, Q
    from django.utils import timezone
    import datetime

    excluded_usernames = [
        'newsbot', 'socialbot', 'karatebot', 'kose_yazari', 'federation_importer', 
        'karate_importer', 'karate_full_importer', 'multi_federation_importer', 
        'boks_importer', 'wushu_duyuru_importer', 'wushu_importer', 'boxing_importer', 
        'mma_scraper', 'gures_scraper', 'mmafederasyonu', 'yetkili', 'Yetkili User', 
        'abone'
    ]

    base_domain = "https://spor24.net"

    # 1. Fetch real columnists
    authors_qs = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(userprofile__user_type='yetkili') | Q(haber__kose_yazisi=True)
    ).exclude(username__in=excluded_usernames).distinct().annotate(
        yazi_sayisi=Count('haber', filter=Q(haber__kose_yazisi=True, haber__yayinlandi=True)),
        haber_sayisi=Count('haber', filter=Q(haber__kose_yazisi=False, haber__yayinlandi=True))
    ).order_by('-yazi_sayisi', '-haber_sayisi')

    authors_data = []
    seen_names = set()
    cutoff_7d = timezone.now() - datetime.timedelta(days=7)

    for u in authors_qs:
        name = u.get_full_name().strip()
        if not name:
            if '@' in u.username:
                name = u.username.split('@')[0].capitalize()
            else:
                name = u.username

        if name in seen_names or name.lower() in ['test user', 'pasif user']:
            continue
        seen_names.add(name)

        # Avatar resolution
        avatar_url = ""
        if hasattr(u, 'userprofile') and u.userprofile:
            prof = u.userprofile
            if hasattr(prof, 'profil_resmi') and prof.profil_resmi:
                try:
                    avatar_url = prof.profil_resmi.url
                except Exception:
                    avatar_url = str(prof.profil_resmi)
            elif hasattr(prof, 'avatar') and prof.avatar:
                try:
                    avatar_url = prof.avatar.url
                except Exception:
                    avatar_url = str(prof.avatar)

        if not avatar_url:
            latest_h = Haber.objects.filter(yazar=u).exclude(resim='').exclude(resim__isnull=True).order_by('-olusturma_tarihi').first()
            if latest_h and latest_h.resim:
                try:
                    avatar_url = latest_h.resim.url
                except Exception:
                    avatar_url = str(latest_h.resim)

        if avatar_url and not avatar_url.startswith('http'):
            avatar_url = base_domain + ('' if avatar_url.startswith('/') else '/') + avatar_url
        if not avatar_url:
            avatar_url = base_domain + '/static/v3/img/author-default.jpg'

        role = "Kıdemli Spor Yazarı & Analist"
        if hasattr(u, 'userprofile') and getattr(u.userprofile, 'unvan', None):
            role = u.userprofile.unvan

        has_new = Haber.objects.filter(yazar=u, yayinlandi=True, olusturma_tarihi__gte=cutoff_7d).exists()

        authors_data.append({
            'id': str(u.id),
            'name': name,
            'role': role,
            'avatar_url': avatar_url,
            'has_new_article': has_new,
            'total_articles': u.yazi_sayisi + u.haber_sayisi,
            'is_following': False
        })

    # 2. Fetch real column articles
    articles_qs = Haber.objects.filter(
        kose_yazisi=True,
        yayinlandi=True
    ).select_related('kategori', 'yazar').order_by('-olusturma_tarihi')[:30]

    # If few dedicated column articles, fallback to editorial articles
    if articles_qs.count() < 4:
        articles_qs = Haber.objects.filter(
            yayinlandi=True
        ).exclude(yazar__username__in=['newsbot', 'socialbot', 'karatebot']).select_related('kategori', 'yazar').order_by('-olusturma_tarihi')[:30]

    articles_data = []
    now = timezone.now()

    for idx, art in enumerate(articles_qs):
        art_author_name = art.yazar.get_full_name().strip() if art.yazar else 'SPOR24 Editörü'
        if not art_author_name or art_author_name == 'admin':
            art_author_name = 'Kenan Demirel' if 'kenan' in (art.yazar.username if art.yazar else '').lower() else (art.yazar.username if art.yazar else 'SPOR24 Editörü')

        # Match with authors_data if available
        matched_author = next((a for a in authors_data if a['name'] == art_author_name or a['id'] == str(art.yazar_id)), None)
        if not matched_author:
            matched_author = {
                'id': str(art.yazar_id or idx + 1),
                'name': art_author_name,
                'role': 'SPOR24 Analisti',
                'avatar_url': base_domain + '/static/v3/img/author-default.jpg',
                'has_new_article': True,
                'total_articles': 1,
                'is_following': False
            }

        # Date formatting
        diff = now - art.olusturma_tarihi
        if diff.days == 0:
            pub_str = "Bugün"
        elif diff.days == 1:
            pub_str = "Dün"
        elif diff.days < 7:
            pub_str = f"{diff.days} gün önce"
        else:
            pub_str = art.olusturma_tarihi.strftime('%d.%m.%Y')

        word_count = len((art.icerik or '').split())
        read_min = max(2, word_count // 140)

        articles_data.append({
            'id': str(art.id),
            'title': art.baslik,
            'summary': art.ozet or (art.baslik[:180] + '...'),
            'author': matched_author,
            'category': (art.kategori.ad if art.kategori else 'SPOR ANALİZ').upper(),
            'read_time': f"{read_min} dk",
            'view_count': art.goruntulenme_sayisi or 0,
            'published_at': pub_str,
            'is_featured': (idx == 0),
            'is_sealed': True,
            'seal_node': 'SPOR24-NODE-01'
        })

    featured_data = articles_data[0] if articles_data else None

    resp = JsonResponse({
        'authors': authors_data,
        'featured': featured_data,
        'articles': articles_data
    })
    resp['Cache-Control'] = 'public, max-age=60, s-maxage=120'
    return resp




