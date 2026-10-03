from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, Permission, ContentType
from django.contrib import messages
from django.db.models import Q
from django.apps import apps
from django.http import JsonResponse
from django.core.cache import cache
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
import os
import threading
from .models import FederasyonWebsite, TaramaLog, Haber, BekleyenSosyalMedyaHaberi

def run_scraper_in_background(log_file_path):
    cache.set('scraper_running', True, timeout=1800)
    cache.set('scraper_status_message', 'Tarama işlemi başlatılıyor...')
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    try:
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] --- MANUEL TARAMA BAŞLATILDI ---\n")
            log_file.flush()
            
            # 1. Web Siteleri Taraması (Crawl4AI Akıllı Motor)
            cache.set('scraper_status_message', 'Web siteleri taranıyor (Crawl4AI Akıllı Motor)...')
            call_command('crawl_federasyonlar_ai', stdout=log_file, stderr=log_file)
            log_file.flush()
            
            # 2. Sosyal Medya Taraması
            cache.set('scraper_status_message', 'Sosyal medya taranıyor (tarama_sosyal_medya)...')
            call_command('tarama_sosyal_medya', stdout=log_file, stderr=log_file)
            log_file.flush()
            
            log_file.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] --- MANUEL TARAMA BAŞARIYLA TAMAMLANDI ---\n")
            cache.set('scraper_status_message', 'Tarama başarıyla tamamlandı.')
    except Exception as e:
        cache.set('scraper_status_message', f'Tarama hatası: {str(e)}')
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Hata oluştu: {str(e)}\n")
        except:
            pass
    finally:
        cache.delete('scraper_running')

def run_instagram_unsend_in_background(session_id, log_file_path):
    cache.set('instagram_unsend_running', True, timeout=3600)
    cache.set('instagram_unsend_status', 'Giriş yapılıyor...')
    
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    try:
        from instagrapi import Client
        import time
        cl = Client()
        
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Instagram DM temizleme işlemi başlatıldı.\n")
            log_file.flush()
            
            try:
                cl.login_by_sessionid(session_id)
                log_file.write(f"[SUCCESS] Giriş başarılı! Kullanıcı: {cl.username} (ID: {cl.user_id})\n")
                log_file.flush()
            except Exception as e:
                log_file.write(f"[ERROR] Oturum açma hatası: {str(e)}\n")
                log_file.flush()
                cache.set('instagram_unsend_status', f'Giriş hatası: {str(e)}')
                return
                
            cache.set('instagram_unsend_status', 'Sohbetler alınıyor...')
            threads = cl.direct_threads(amount=20)
            log_file.write(f"[INFO] {len(threads)} adet sohbet bulundu.\n")
            log_file.flush()
            
            total_unsent = 0
            for thread in threads:
                thread_users = ", ".join([u.username for u in thread.users])
                log_file.write(f"\nSohbet ID: {thread.id} ({thread_users}) taranıyor...\n")
                log_file.flush()
                
                try:
                    messages = cl.direct_messages(thread.id, amount=50)
                except Exception as e:
                    log_file.write(f"[ERROR] Mesajlar alınamadı: {str(e)}\n")
                    log_file.flush()
                    continue
                    
                for msg in messages:
                    if str(msg.user_id) == str(cl.user_id):
                        log_file.write(f" -> Gönderdiğiniz mesaj geri çekiliyor (Unsend): \"{msg.text}\"\n")
                        log_file.flush()
                        try:
                            cl.direct_message_unsend(thread.id, msg.id)
                            total_unsent += 1
                            log_file.write("    [OK] Mesaj başarıyla geri çekildi.\n")
                            log_file.flush()
                            time.sleep(4.0)
                        except Exception as e:
                            log_file.write(f"    [FAILED] Geri çekme hatası: {str(e)}\n")
                            log_file.flush()
                            if "rate" in str(e).lower() or "spam" in str(e).lower():
                                log_file.write("    [WARNING] Limit aşımı! 30 saniye bekleniyor...\n")
                                log_file.flush()
                                time.sleep(30)
                            else:
                                time.sleep(1)
                                
                log_file.write(" -> Sohbet kutunuzdan gizleniyor/siliniyor...\n")
                log_file.flush()
                try:
                    cl.direct_thread_hide(thread.id)
                    log_file.write("    [OK] Sohbet kutudan temizlendi.\n")
                    log_file.flush()
                    time.sleep(1.5)
                except Exception as e:
                    log_file.write(f"    [FAILED] Sohbet gizleme hatası: {str(e)}\n")
                    log_file.flush()
                    
            log_file.write(f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] İşlem tamamlandı. Toplam geri çekilen mesaj: {total_unsent}\n")
            cache.set('instagram_unsend_status', f'İşlem tamamlandı. Geri çekilen mesaj: {total_unsent}')
    except Exception as e:
        cache.set('instagram_unsend_status', f'Hata oluştu: {str(e)}')
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"[ERROR] Genel hata: {str(e)}\n")
        except:
            pass
    finally:
        cache.delete('instagram_unsend_running')

@user_passes_test(lambda u: u.is_superuser)
def scraper_control(request):
    log_file_path = os.path.join(settings.BASE_DIR, 'logs', 'otomatik_tarama.log')
    instagram_log_path = os.path.join(settings.BASE_DIR, 'logs', 'instagram_unsend.log')
    
    # Handle AJAX and POST requests
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_site':
            site_id = request.POST.get('site_id')
            try:
                site = FederasyonWebsite.objects.get(id=site_id)
                site.aktif = not site.aktif
                site.save()
                return JsonResponse({'status': 'success', 'aktif': site.aktif, 'site_name': site.ad})
            except FederasyonWebsite.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Site bulunamadı.'}, status=404)
                
        elif action == 'toggle_all_sites':
            aktif_val = request.POST.get('aktif') == 'true'
            FederasyonWebsite.objects.all().update(aktif=aktif_val)
            return JsonResponse({'status': 'success', 'aktif': aktif_val})
                
        elif action == 'start_scraper':
            if cache.get('scraper_running'):
                return JsonResponse({'status': 'error', 'message': 'Tarama zaten çalışıyor.'})
                
            session_id = request.POST.get('session_id', '').strip()
            if session_id:
                cache.set('instagram_last_session_id', session_id, timeout=None)
                # Immediately write cookies json
                cookies = [
                    {
                        "name": "sessionid",
                        "value": session_id,
                        "domain": ".instagram.com",
                        "path": "/",
                        "secure": True,
                        "httpOnly": True
                    }
                ]
                cookie_path = os.path.join(settings.BASE_DIR, 'instagram_cookies.json')
                try:
                    import json
                    with open(cookie_path, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f)
                except Exception as e:
                    # Log error silently
                    pass
                
            # Start background thread
            t = threading.Thread(target=run_scraper_in_background, args=(log_file_path,))
            t.daemon = True
            t.start()
            return JsonResponse({'status': 'success', 'message': 'Tarama arka planda başlatıldı.'})
            
        elif action == 'clear_logs':
            try:
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Log dosyası temizlendi.\n")
                return JsonResponse({'status': 'success', 'message': 'Loglar başarıyla temizlendi.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Hata: {str(e)}'})

        elif action == 'get_status':
            is_running = bool(cache.get('scraper_running'))
            status_message = cache.get('scraper_status_message', 'Beklemede')
            
            # Read last 120 lines of logs
            logs = ""
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        logs = "".join(lines[-120:])
                except Exception as e:
                    logs = f"Log okuma hatası: {str(e)}"
            else:
                logs = "Log dosyası henüz oluşmamış."
                
            return JsonResponse({
                'is_running': is_running,
                'status_message': status_message,
                'logs': logs
            })

        # New Instagram Actions
        elif action == 'start_instagram_unsend':
            if cache.get('instagram_unsend_running'):
                return JsonResponse({'status': 'error', 'message': 'Temizlik işlemi zaten çalışıyor.'})
                
            session_id = request.POST.get('session_id', '').strip()
            if not session_id:
                return JsonResponse({'status': 'error', 'message': 'Lütfen geçerli bir Session ID girin.'})
                
            cache.set('instagram_last_session_id', session_id, timeout=None) # Save session ID to cache permanently
            
            # Start background thread
            t = threading.Thread(target=run_instagram_unsend_in_background, args=(session_id, instagram_log_path))
            t.daemon = True
            t.start()
            return JsonResponse({'status': 'success', 'message': 'Instagram DM temizliği arka planda başlatıldı.'})

        elif action == 'get_instagram_status':
            is_running = bool(cache.get('instagram_unsend_running'))
            status_message = cache.get('instagram_unsend_status', 'Beklemede')
            
            # Read last 120 lines of instagram logs
            logs = ""
            if os.path.exists(instagram_log_path):
                try:
                    with open(instagram_log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        logs = "".join(lines[-120:])
                except Exception as e:
                    logs = f"Log okuma hatası: {str(e)}"
            else:
                logs = "Temizlik işlemi başlatıldığında günlük dosyası burada görünecektir."
                
            return JsonResponse({
                'is_running': is_running,
                'status_message': status_message,
                'logs': logs
            })

        elif action == 'clear_instagram_logs':
            try:
                os.makedirs(os.path.dirname(instagram_log_path), exist_ok=True)
                with open(instagram_log_path, 'w', encoding='utf-8') as f:
                    f.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Instagram günlükleri temizlendi.\n")
                return JsonResponse({'status': 'success', 'message': 'Günlükler başarıyla temizlendi.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Hata: {str(e)}'})

        elif action == 'save_instagram_session':
            session_id = request.POST.get('session_id', '').strip()
            if not session_id:
                return JsonResponse({'status': 'error', 'message': 'Lütfen geçerli bir Session ID girin.'})
            cache.set('instagram_last_session_id', session_id, timeout=None)
            
            # Immediately write the cookies JSON file
            cookies = [
                {
                    "name": "sessionid",
                    "value": session_id,
                    "domain": ".instagram.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True
                }
            ]
            cookie_path = os.path.join(settings.BASE_DIR, 'instagram_cookies.json')
            try:
                with open(cookie_path, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f)
                return JsonResponse({'status': 'success', 'message': 'Instagram Session ID başarıyla kaydedildi.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Hata: Çerez dosyası güncellenemedi: {str(e)}'})

        elif action == 'approve_website_news':
            news_id = request.POST.get('news_id')
            try:
                news = Haber.objects.get(id=news_id)
                news.yayinlandi = True
                news.save()
                return JsonResponse({'status': 'success', 'message': 'Haber başarıyla yayınlandı.'})
            except Haber.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Haber bulunamadı.'}, status=404)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Hata: {str(e)}'})
                
        elif action == 'delete_website_news':
            news_id = request.POST.get('news_id')
            try:
                Haber.objects.filter(id=news_id).delete()
                return JsonResponse({'status': 'success', 'message': 'Haber silindi.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Hata: {str(e)}'})
                
        elif action == 'approve_social_news':
            news_id = request.POST.get('news_id')
            try:
                social_news = BekleyenSosyalMedyaHaberi.objects.get(id=news_id)
                social_news.approve(request.user)
                return JsonResponse({'status': 'success', 'message': 'Sosyal medya haberi onaylandı.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Hata: {str(e)}'})
                
        elif action == 'reject_social_news':
            news_id = request.POST.get('news_id')
            try:
                social_news = BekleyenSosyalMedyaHaberi.objects.get(id=news_id)
                social_news.reddedildi = True
                social_news.save()
                return JsonResponse({'status': 'success', 'message': 'Sosyal medya haberi reddedildi.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Hata: {str(e)}'})
            
    # GET request: Render the control dashboard
    websites = FederasyonWebsite.objects.all().order_by('ad')
    recent_logs = TaramaLog.objects.all().select_related('federasyon_website').order_by('-tarama_zamani')[:15]
    
    # Read initial logs
    logs = ""
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logs = "".join(lines[-120:])
        except Exception as e:
            logs = f"Log okuma hatası: {str(e)}"
    else:
        logs = "Log dosyası henüz oluşmamış."
        
    is_running = bool(cache.get('scraper_running'))
    status_message = cache.get('scraper_status_message', 'Beklemede')

    # Read initial Instagram logs
    instagram_logs = ""
    if os.path.exists(instagram_log_path):
        try:
            with open(instagram_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                instagram_logs = "".join(lines[-120:])
        except Exception as e:
            instagram_logs = f"Log okuma hatası: {str(e)}"
    else:
        instagram_logs = "Temizlik işlemi başlatıldığında günlük dosyası burada görünecektir."

    instagram_running = bool(cache.get('instagram_unsend_running'))
    instagram_status = cache.get('instagram_unsend_status', 'Beklemede')
    
    all_sites_active = not FederasyonWebsite.objects.filter(aktif=False).exists()
    last_session_id = cache.get('instagram_last_session_id', '57376994679%3AkHiMd2dCAO52RP%3A1%3AAYjoYIF26oWmqi5bD2WGiJim2rIYMFsAsjtVA590Ng')
    
    # Check if last Instagram scan had a 403 error
    instagram_session_status = "active" # default
    last_insta_err = TaramaLog.objects.filter(mesaj__icontains="instagram", durum="hata").order_by("-tarama_zamani").first()
    if last_insta_err and ("403" in last_insta_err.mesaj or "Erişim hatası" in last_insta_err.mesaj or "cookie" in last_insta_err.mesaj.lower()):
        instagram_session_status = "expired"
    elif not cache.get('instagram_last_session_id'):
        instagram_session_status = "missing"

    # Fetch pending news
    pending_website_news = Haber.objects.filter(otomatik_eklendi=True, yayinlandi=False).order_by('-olusturma_tarihi')
    pending_social_news = BekleyenSosyalMedyaHaberi.objects.filter(onaylandi=False, reddedildi=False).order_by('-paylasim_tarihi')
    
    pending_website_count = pending_website_news.count()
    pending_social_count = pending_social_news.count()
    total_pending_count = pending_website_count + pending_social_count
    
    context = {
        'websites': websites,
        'recent_logs': recent_logs,
        'logs': logs,
        'is_running': is_running,
        'status_message': status_message,
        'instagram_logs': instagram_logs,
        'instagram_running': instagram_running,
        'instagram_status': instagram_status,
        'all_sites_active': all_sites_active,
        'last_session_id': last_session_id,
        'instagram_session_status': instagram_session_status,
        'pending_website_news': pending_website_news,
        'pending_social_news': pending_social_news,
        'pending_website_count': pending_website_count,
        'pending_social_count': pending_social_count,
        'total_pending_count': total_pending_count,
        'title': 'Haber Tarama & Bot Yönetimi'
    }
    return render(request, 'admin/scraper_control.html', context)


@user_passes_test(lambda u: u.is_superuser)
def permission_matrix(request):
    from django.contrib import admin

    # 1. POST İşlemleri
    if request.method == 'POST':
        # Yeni grup ekleme
        if 'new_group_name' in request.POST:
            gname = request.POST.get('new_group_name', '').strip()
            if gname:
                g, created = Group.objects.get_or_create(name=gname)
                if created:
                    messages.success(request, f"🎉 '{gname}' rolü başarıyla oluşturuldu.")
                else:
                    messages.info(request, f"ℹ️ '{gname}' rolü zaten mevcut.")
            return redirect('permission_matrix')

        # Grup silme
        if 'delete_group_id' in request.POST:
            gid = request.POST.get('delete_group_id')
            Group.objects.filter(id=gid).delete()
            messages.success(request, "🗑️ Rol başarıyla silindi.")
            return redirect('permission_matrix')

        # Varsayılan rolleri oluşturma
        if 'create_default_groups' in request.POST:
            default_roles = ["Genel Yayın Yönetmeni & Editör", "Köşe Yazarı", "Federasyon Temsilcisi", "Reklam Yöneticisi"]
            for r in default_roles:
                Group.objects.get_or_create(name=r)
            messages.success(request, "🎉 Varsayılan sistem rolleri başarıyla oluşturuldu.")
            return redirect('permission_matrix')

        # İzinleri kaydetme
        groups = Group.objects.all().order_by('id')
        for group in groups:
            selected_perms = []
            for key in request.POST.keys():
                if key.startswith(f'perm_{group.id}_'):
                    try:
                        perm_id = int(key.split('_')[-1])
                        selected_perms.append(perm_id)
                    except ValueError:
                        pass
            group.permissions.set(selected_perms)
            group.save()
        
        messages.success(request, '✅ Rol ve model izinleri başarıyla kaydedildi.')
        return redirect('permission_matrix')

    # 2. GET İşlemleri
    groups = Group.objects.all().order_by('id')
    
    # Sadece ilgilendiğimiz app'lerin modellerini alalım
    target_apps = ['haberler', 'auth']
    content_types = ContentType.objects.filter(app_label__in=target_apps).order_by('app_label', 'model')
    
    matrix_data = []
    
    for ct in content_types:
        model_name = ct.model_class()._meta.verbose_name if ct.model_class() else ct.model
        perms = Permission.objects.filter(content_type=ct)
        
        crud_perms = {
            'view': perms.filter(codename__startswith='view_').first(),
            'add': perms.filter(codename__startswith='add_').first(),
            'change': perms.filter(codename__startswith='change_').first(),
            'delete': perms.filter(codename__startswith='delete_').first(),
        }
        
        matrix_data.append({
            'model': str(model_name).title(),
            'app': ct.app_label,
            'perms': crud_perms,
            'all_perms': perms
        })

    context = dict(
        admin.site.each_context(request),
        groups=groups,
        matrix_data=matrix_data,
        title='İzin & Yetki Matrisi'
    )
    return render(request, 'admin/custom_permission_matrix.html', context)
