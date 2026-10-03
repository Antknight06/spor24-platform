from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.text import slugify
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import UserProfile, Haber, Kategori, Yorum, Favori, BekleyenYetkiliHaberi, Reklam, BultenAbone, BekleyenSosyalMedyaHaberi, BekleyenHaber
from .email_validator import EmailValidator

# Initialize the improved email validator
email_validator = EmailValidator()
from django.core.paginator import Paginator
import json
import secrets
import time
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

@require_http_methods(["POST"])
def validate_email_ajax(request):
    """AJAX endpoint for real-time email validation"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()

        if not email:
            return JsonResponse({'valid': False, 'message': 'Email adresi gereklidir'})

        if User.objects.filter(email=email).exists():
            return JsonResponse({'valid': False, 'message': 'Bu email adresi zaten kullanımda'})

        is_valid, message = email_validator.validate_email(email)
        return JsonResponse({'valid': is_valid, 'message': message})

    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'message': 'Geçersiz istek'})
    except Exception as e:
        return JsonResponse({'valid': False, 'message': 'Email doğrulanırken hata oluştu'})

@csrf_protect
@sensitive_post_parameters('password1', 'password2', 'abone_password1', 'abone_password2', 'yetkili_password1', 'yetkili_password2')
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user_type = request.POST.get('user_type', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
          login(request, user, backend='django.contrib.auth.backends.ModelBackend')

          # YENİ YÖNLENDİRME MANTIĞI
          if user.is_superuser:
             return redirect('haberler:admin_dashboard')
          elif user.is_staff: # "Görev durumu" işaretli olanlar
             return redirect('haberler:yetkili_dashboard')
          else: # Diğer herkes
             return redirect('haberler:abone_dashboard')
              # YENİ MANTIK SONU
                
                    
            
                
                
        else:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')

    user_type = request.GET.get('user_type', '')
    context = {'user_type': user_type}
    return render(request, 'auth/login.html', context)

def custom_logout(request):
    logout(request)
    return redirect('anasayfa')

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    
    total_haberler = Haber.objects.count()
    total_kullanicilar = User.objects.count()
    total_kategoriler = Kategori.objects.count()
    total_yetkililer = UserProfile.objects.filter(user_type='yetkili').count()
    total_reklamlar = Reklam.objects.count()
    total_bulten_aboneleri = BultenAbone.objects.count()
    total_sosyal_medya = BekleyenSosyalMedyaHaberi.objects.filter(onaylandi=False, reddedildi=False).count()
    total_bekleyen_haber = BekleyenHaber.objects.filter(onaylandi=False, reddedildi=False).count()
    total_bekleyen_yetkili = BekleyenYetkiliHaberi.objects.filter(onaylandi=False, reddedildi=False).count()
    
    context = {
        'user_type': 'Yönetici',
        'dashboard_title': 'Yönetici Paneli',
        'permissions': [
            'Tüm haberleri düzenleme',
            'Kullanıcı yönetimi',
            'Kategori yönetimi',
            'Sistem ayarları'
        ],
        'total_haberler': total_haberler,
        'total_kullanicilar': total_kullanicilar,
        'total_kategoriler': total_kategoriler,
        'total_yetkililer': total_yetkililer,
        'total_reklamlar': total_reklamlar,
        'total_bulten_aboneleri': total_bulten_aboneleri,
        'total_sosyal_medya': total_sosyal_medya,
        'total_bekleyen_haber': total_bekleyen_haber,
        'total_bekleyen_yetkili': total_bekleyen_yetkili,
    }
    return render(request, 'auth/dashboard_admin.html', context)

@login_required
def yetkili_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    user_haberler = Haber.objects.filter(yazar=request.user, kose_yazisi=False, otomatik_eklendi=False).count()
    user_kose_yazilari = Haber.objects.filter(yazar=request.user, kose_yazisi=True, otomatik_eklendi=False).count()
    bekleyen_yetkili_haberler = BekleyenYetkiliHaberi.objects.filter(yazar=request.user)
    bekleyen_onay = bekleyen_yetkili_haberler.filter(onaylandi=False, reddedildi=False).count()
    onaylanan_yetkili = bekleyen_yetkili_haberler.filter(onaylandi=True).count()
    reddedilen_yetkili = bekleyen_yetkili_haberler.filter(reddedildi=True).count()
    user_yorumlar = 0
    haberler = Haber.objects.filter(yazar=request.user, otomatik_eklendi=False)
    for haber in haberler:
        user_yorumlar += haber.yorumlar.filter(onaylandi=True).count()
    user_taslak = Haber.objects.filter(yazar=request.user, yayinlandi=False, otomatik_eklendi=False).count()
    context = { 'user_type': 'Yetkili', 'dashboard_title': 'Yetkili Paneli', 'permissions': ['Haber ekleme', 'Kendi haberlerini düzenleme', 'Köşe yazısı ekleme', 'Kendi köşe yazılarını düzenleme', 'Yorum yönetimi'], 'user_haberler': user_haberler, 'user_kose_yazilari': user_kose_yazilari, 'user_yorumlar': user_yorumlar, 'user_taslak': user_taslak, 'bekleyen_onay': bekleyen_onay, 'onaylanan_yetkili': onaylanan_yetkili, 'reddedilen_yetkili': reddedilen_yetkili, 'toplam_bekleyen': bekleyen_onay }
    return render(request, 'auth/dashboard_yetkili.html', context)

@login_required
def abone_dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    context = { 'user_type': 'Abone', 'dashboard_title': 'Abone Paneli', 'permissions': ['Haber okuma', 'Yorum yapma', 'Profil yönetimi'] }
    return render(request, 'auth/dashboard_abone.html', context)

@csrf_protect
@sensitive_post_parameters('password1', 'password2', 'abone_password1', 'abone_password2', 'yetkili_password1', 'yetkili_password2')
@transaction.atomic 
def register(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'abone')
        print(f"Registration attempt - User type: {user_type}")

        if user_type == 'admin':
            messages.error(request, 'Yönetici hesabı sadece sistem yöneticisi tarafından oluşturulabilir.')
            return render(request, 'auth/register.html', {'user_type': user_type})

        if user_type == 'abone':
            email = request.POST.get('abone_email', '').strip()
            password1 = request.POST.get('abone_password1', '').strip()
            password2 = request.POST.get('abone_password2', '').strip()
            first_name = ''
            last_name = ''
            username = email 
        else: # yetkili
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('yetkili_email', '').strip()
            password1 = request.POST.get('yetkili_password1', '').strip()
            password2 = request.POST.get('yetkili_password2', '').strip()
            username = f"{first_name} {last_name}".strip()
            
            if not username:
                 messages.error(request, 'Yetkili kaydı için Ad ve Soyad gereklidir.')
                 return render(request, 'auth/register.html', {'user_type': user_type})
            
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username} {counter}"
                counter += 1

        if not email or not password1:
            messages.error(request, 'E-posta ve şifre alanları gereklidir.')
            return render(request, 'auth/register.html', {'user_type': user_type})
        
        if password1 != password2:
            messages.error(request, 'Şifreler eşleşmiyor.')
            return render(request, 'auth/register.html', {'user_type': user_type})

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Bu e-posta adresi zaten kullanımda.')
            return render(request, 'auth/register.html', {'user_type': user_type})
        
        if cache.get(f'verify_{email}_timestamp'):
             messages.error(request, 'Bu e-posta adresi için zaten bir doğrulama kodu gönderildi. Lütfen e-postanızı kontrol edin veya 5 dakika sonra tekrar deneyin.')
             return render(request, 'auth/register.html', {'user_type': user_type})

        try:
            hashed_password = make_password(password1)

            pending_data = {
                'username': username,
                'email': email,
                'hashed_password': hashed_password,
                'first_name': first_name,
                'last_name': last_name,
                'user_type': user_type
            }

            cache.set(f'pending_user_{email}', pending_data, 300)

            verification_code = secrets.token_hex(3).upper()
            cache.set(f'verify_{email}', verification_code, 300)
            cache.set(f'verify_{email}_timestamp', time.time(), 300) 
            print(f"Kod oluşturuldu: {email} için {verification_code}")

            subject = 'NET Spor Hesap Doğrulama Kodu'
            message = f'Hesabınızı doğrulamak için kodunuz: {verification_code}\nKod 5 dakika geçerlidir.'
            from_email_formatted = f"NET Spor <{settings.DEFAULT_FROM_EMAIL}>"

            try:
                send_mail(
                    subject,
                    message,
                    from_email_formatted,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, f'{email} adresine bir doğrulama kodu gönderildi. Lütfen kodunuzu girin.')
            except Exception as mail_err:
                print(f"E-posta gönderimi başarısız oldu: {mail_err}")
                messages.warning(
                    request,
                    f"E-posta gönderim servisinde teknik bir sorun oluştu ({mail_err}). "
                    f"Hesabınızı doğrulamak için geçici onay kodunuz: {verification_code}"
                )
            
            return redirect(reverse('haberler:verify_email', kwargs={'user_email': email}))

        except Exception as e:
            messages.error(request, f'Kayıt sırasında bir hata oluştu: {e}. Lütfen tekrar deneyin.')
            return render(request, 'auth/register.html', {'user_type': user_type})

    user_type = request.GET.get('user_type', 'abone')
    if user_type == 'admin':
        user_type = 'abone'
    return render(request, 'auth/register.html', {'user_type': user_type})

@login_required
def yeni_kose_yazisi(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    if request.method == 'POST':
        baslik = request.POST.get('baslik', '').strip()
        ozet = request.POST.get('ozet', '').strip()
        icerik = request.POST.get('icerik', '').strip()
        kategori_id = request.POST.get('kategori')
        resim = request.FILES.get('resim')
        if not baslik or not ozet or not icerik or not kategori_id:
            messages.error(request, 'Tüm alanlar gereklidir.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/yeni_kose_yazisi.html', {'kategoriler': kategoriler})
        try:
            kategori = Kategori.objects.get(id=kategori_id)
            bekleyen_haber = BekleyenYetkiliHaberi.objects.create(
                baslik=baslik,
                ozet=ozet,
                icerik=icerik,
                kategori=kategori,
                yazar=request.user,
                kose_yazisi=True,
                resim=resim
            )
            messages.success(request, '🎯 Köşe yazınız admin onayına gönderildi. Onaylandıktan sonra yayınlanacaktır.')
            return redirect('haberler:bekleyen_yetkili_haberlerim')
        except Kategori.DoesNotExist:
            messages.error(request, 'Geçersiz kategori.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/yeni_kose_yazisi.html', {'kategoriler': kategoriler})
        except Exception as e:
            messages.error(request, f'Köşe yazısı gönderilirken bir hata oluştu: {str(e)}')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/yeni_kose_yazisi.html', {'kategoriler': kategoriler})
    kategoriler = Kategori.objects.all()
    return render(request, 'auth/yeni_kose_yazisi.html', {'kategoriler': kategoriler})

@login_required
def kose_yazisi_duzenle(request, haber_id):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    haber = get_object_or_404(Haber, id=haber_id, yazar=request.user, kose_yazisi=True)
    if request.method == 'POST':
        baslik = request.POST.get('baslik', '').strip()
        ozet = request.POST.get('ozet', '').strip()
        icerik = request.POST.get('icerik', '').strip()
        kategori_id = request.POST.get('kategori')
        resim = request.FILES.get('resim')
        if not baslik or not ozet or not icerik or not kategori_id:
            messages.error(request, 'Tüm alanlar gereklidir.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/kose_yazisi_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})
        try:
            kategori = Kategori.objects.get(id=kategori_id)
            haber.baslik = baslik
            haber.slug = slugify(baslik) + '-' + str(haber.id)
            haber.ozet = ozet
            haber.icerik = icerik
            haber.kategori = kategori
            if resim:
                haber.resim = resim
            haber.save()
            messages.success(request, 'Köşe yazınız başarıyla güncellendi.')
            return redirect('haberler:kose_yazisi_duzenle', haber_id=haber.id)
        except Kategori.DoesNotExist:
            messages.error(request, 'Geçersiz kategori.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/kose_yazisi_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})
        except Exception as e:
            messages.error(request, f'Köşe yazısı güncellenirken bir hata oluştu: {str(e)}')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/kose_yazisi_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})
    kategoriler = Kategori.objects.all()
    return render(request, 'auth/kose_yazisi_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})

@login_required
def kose_yazilarim(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    kose_yazilari = Haber.objects.filter(yazar=request.user, kose_yazisi=True, otomatik_eklendi=False).order_by('-olusturma_tarihi')
    return render(request, 'auth/kose_yazilarim.html', {'kose_yazilari': kose_yazilari})

@login_required
def yeni_haber(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    if request.method == 'POST':
        baslik = request.POST.get('baslik', '').strip()
        ozet = request.POST.get('ozet', '').strip()
        icerik = request.POST.get('icerik', '').strip()
        kategori_id = request.POST.get('kategori')
        resim = request.FILES.get('resim')
        if not baslik or not ozet or not icerik or not kategori_id:
            messages.error(request, 'Tüm alanlar gereklidir.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/yeni_haber.html', {'kategoriler': kategoriler})
        try:
            kategori = Kategori.objects.get(id=kategori_id)
            bekleyen_haber = BekleyenYetkiliHaberi.objects.create(
                baslik=baslik,
                ozet=ozet,
                icerik=icerik,
                kategori=kategori,
                yazar=request.user,
                kose_yazisi=False,
                resim=resim
            )
            messages.success(request, '📰 Haberiniz admin onayına gönderildi. Onaylandıktan sonra yayınlanacaktır.')
            return redirect('haberler:bekleyen_yetkili_haberlerim')
        except Kategori.DoesNotExist:
            messages.error(request, 'Geçersiz kategori.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/yeni_haber.html', {'kategoriler': kategoriler})
        except Exception as e:
            messages.error(request, f'Haber gönderilirken bir hata oluştu: {str(e)}')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/yeni_haber.html', {'kategoriler': kategoriler})
    kategoriler = Kategori.objects.all()
    return render(request, 'auth/yeni_haber.html', {'kategoriler': kategoriler})

@login_required
def haber_duzenle(request, haber_id):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    haber = get_object_or_404(Haber, id=haber_id, yazar=request.user, kose_yazisi=False)
    if request.method == 'POST':
        baslik = request.POST.get('baslik', '').strip()
        ozet = request.POST.get('ozet', '').strip()
        icerik = request.POST.get('icerik', '').strip()
        kategori_id = request.POST.get('kategori')
        resim = request.FILES.get('resim')
        if not baslik or not ozet or not icerik or not kategori_id:
            messages.error(request, 'Tüm alanlar gereklidir.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/haber_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})
        try:
            kategori = Kategori.objects.get(id=kategori_id)
            haber.baslik = baslik
            haber.slug = slugify(baslik) + '-' + str(haber.id)
            haber.ozet = ozet
            haber.icerik = icerik
            haber.kategori = kategori
            if resim:
                haber.resim = resim
            haber.save()
            messages.success(request, 'Haberiniz başarıyla güncellendi.')
            return redirect('haberler:haber_duzenle', haber_id=haber.id)
        except Kategori.DoesNotExist:
            messages.error(request, 'Geçersiz kategori.')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/haber_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})
        except Exception as e:
            messages.error(request, f'Haber güncellenirken bir hata oluştu: {str(e)}')
            kategoriler = Kategori.objects.all()
            return render(request, 'auth/haber_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})
    kategoriler = Kategori.objects.all()
    return render(request, 'auth/haber_duzenle.html', {'haber': haber, 'kategoriler': kategoriler})

@login_required
def haberlerim(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    haberler = Haber.objects.filter(yazar=request.user, kose_yazisi=False, otomatik_eklendi=False).order_by('-olusturma_tarihi')
    return render(request, 'auth/haberlerim.html', {'haberler': haberler})

@login_required
def yorum_yonetimi(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    context = {'dashboard_title': 'Yorum Yönetimi'}
    return render(request, 'auth/yorum_yonetimi.html', context)

@login_required
def istatistikler(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    user_haberler = Haber.objects.filter(yazar=request.user, kose_yazisi=False, otomatik_eklendi=False)
    user_kose_yazilari = Haber.objects.filter(yazar=request.user, kose_yazisi=True, otomatik_eklendi=False)
    toplam_haber = user_haberler.count() + user_kose_yazilari.count()
    toplam_goruntulenme = sum(haber.goruntulenme_sayisi for haber in user_haberler) + sum(haber.goruntulenme_sayisi for haber in user_kose_yazilari)
    toplam_yorum = 0
    for haber in user_haberler:
        toplam_yorum += haber.yorumlar.filter(onaylandi=True).count()
    for haber in user_kose_yazilari:
        toplam_yorum += haber.yorumlar.filter(onaylandi=True).count()
    toplam_kelime = 0
    toplam_haber_sayisi = toplam_haber
    for haber in user_haberler:
        toplam_kelime += len(haber.icerik.split())
    for haber in user_kose_yazilari:
        toplam_kelime += len(haber.icerik.split())
    ortalama_okuma_suresi = round(toplam_kelime / 200) if toplam_haber_sayisi > 0 else 0
    haber_goruntulenme = sum(haber.goruntulenme_sayisi for haber in user_haberler)
    kose_yazisi_goruntulenme = sum(haber.goruntulenme_sayisi for haber in user_kose_yazilari)
    context = { 'dashboard_title': 'İstatistikler', 'toplam_haber': toplam_haber, 'toplam_goruntulenme': toplam_goruntulenme, 'toplam_yorum': toplam_yorum, 'ortalama_okuma_suresi': ortalama_okuma_suresi, 'haber_goruntulenme': haber_goruntulenme, 'kose_yazisi_goruntulenme': kose_yazisi_goruntulenme, 'haber_sayisi': user_haberler.count(), 'kose_yazisi_sayisi': user_kose_yazilari.count() }
    return render(request, 'auth/istatistikler.html', context)

@login_required
def galeri(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    context = {'dashboard_title': 'Galeri'}
    return render(request, 'auth/galeri.html', context)

@login_required
def favori_haberler(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    favoriler = Favori.objects.filter(kullanici=request.user).select_related('haber', 'haber__kategori')
    paginator = Paginator(favoriler, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'dashboard_title': 'Favori Haberler', 'favoriler': page_obj}
    return render(request, 'auth/favori_haberler.html', context)

@login_required
def yorumlarim(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    yorumlar = Yorum.objects.filter(yazar=request.user).select_related('haber')
    paginator = Paginator(yorumlar, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'dashboard_title': 'Yorumlarım', 'yorumlar': page_obj}
    return render(request, 'auth/yorumlarim.html', context)

@login_required
def profil_ayarlari(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        profile = user.userprofile
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        profile.save()
        messages.success(request, 'Profil bilgileriniz güncellendi.')
        return redirect('haberler:profil_ayarlari')
    context = {'dashboard_title': 'Profil Ayarları'}
    return render(request, 'auth/profil_ayarlari.html', context)
@login_required
def haber_ekle_favori(request, haber_id):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('anasayfa')
    haber = get_object_or_404(Haber, id=haber_id, yayinlandi=True)
    favori, created = Favori.objects.get_or_create(kullanici=request.user, haber=haber)
    if created:
        messages.success(request, 'Haber favorilerinize eklendi.')
    else:
        messages.info(request, 'Bu haber zaten favorilerinizde.')
    return redirect('haberler:haber_detay', slug=haber.slug)

@login_required
def haber_kaldir_favori(request, favori_id):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('anasayfa')
    favori = get_object_or_404(Favori, id=favori_id, kullanici=request.user)
    haber_baslik = favori.haber.baslik
    favori.delete()
    messages.success(request, f'"{haber_baslik}" favorilerinizden kaldırıldı.')
    return redirect('haberler:favori_haberler')

@login_required
def haber_kaldir_favori_by_haber(request, haber_id):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('anasayfa')
    favori = get_object_or_404(Favori, haber_id=haber_id, kullanici=request.user)
    haber_baslik = favori.haber.baslik
    favori.delete()
    messages.success(request, f'"{haber_baslik}" favorilerinizden kaldırıldı.')
    return redirect('haberler:haber_detay', slug=favori.haber.slug)

@login_required
def yorum_ekle(request, haber_id):
    if request.user.userprofile.user_type not in ['abone', 'yetkili']:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('anasayfa')
    haber = get_object_or_404(Haber, id=haber_id, yayinlandi=True)
    if request.method == 'POST':
        icerik = request.POST.get('icerik', '').strip()
        if icerik:
            Yorum.objects.create(haber=haber, yazar=request.user, icerik=icerik)
            messages.success(request, 'Yorumunuz eklendi.')
        else:
            messages.error(request, 'Yorum içeriği boş olamaz.')
    return redirect('haberler:haber_detay', slug=haber.slug)

@login_required
def yorum_yanitla(request, yorum_id):
    if request.user.userprofile.user_type not in ['abone', 'yetkili']:
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('anasayfa')
    ust_yorum = get_object_or_404(Yorum, id=yorum_id)
    haber = ust_yorum.haber
    if request.method == 'POST':
        icerik = request.POST.get('icerik', '').strip()
        if icerik:
            Yorum.objects.create(haber=haber, yazar=request.user, icerik=icerik, ust_yorum=ust_yorum)
            messages.success(request, 'Yanıtınız eklendi.')
        else:
            messages.error(request, 'Yanıt içeriği boş olamaz.')
    return redirect('haberler:haber_detay', slug=haber.slug)

@login_required
def haber_favori_goruntule(request, haber_id):
    haber = get_object_or_404(Haber, id=haber_id, yazar=request.user)
    favoriler = Favori.objects.filter(haber=haber).select_related('kullanici').order_by('-olusturma_tarihi')
    context = {'haber': haber, 'favoriler': favoriler, 'dashboard_title': f'"{haber.baslik}" Haberi İçin Favoriler'}
    return render(request, 'auth/haber_favori_goruntule.html', context)

@login_required
def bekleyen_yetkili_haberlerim(request):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    bekleyen_haberler = BekleyenYetkiliHaberi.objects.filter(yazar=request.user).order_by('-olusturma_tarihi')
    bekleyen_onay = bekleyen_haberler.filter(onaylandi=False, reddedildi=False)
    onaylanan = bekleyen_haberler.filter(onaylandi=True)
    reddedilen = bekleyen_haberler.filter(reddedildi=True)
    context = {'bekleyen_onay': bekleyen_onay, 'onaylanan': onaylanan, 'reddedilen': reddedilen, 'total_bekleyen': bekleyen_onay.count(), 'total_onaylanan': onaylanan.count(), 'total_reddedilen': reddedilen.count()}
    return render(request, 'auth/bekleyen_yetkili_haberlerim.html', context)

@login_required
def bekleyen_yetkili_haber_detay(request, haber_id):
    if not request.user.is_staff:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    bekleyen_haber = get_object_or_404(BekleyenYetkiliHaberi, id=haber_id, yazar=request.user)
    context = {'bekleyen_haber': bekleyen_haber}
    return render(request, 'auth/bekleyen_yetkili_haber_detay.html', context)

@csrf_protect
def verify_email(request, user_email):
    # Önbellek anahtarları
    attempt_key = f'verify_attempts_{user_email}'
    code_key = f'verify_{user_email}'
    timestamp_key = f'verify_{user_email}_timestamp'
    pending_user_key = f'pending_user_{user_email}'

    # --- YARDIMCI FONKSİYON: Önbelleği temizle ve yönlendir ---
    def clear_cache_and_redirect(email):
        pending_data = cache.get(pending_user_key, {})
        user_type = pending_data.get('user_type', 'abone')
        
        cache.delete(code_key)
        cache.delete(attempt_key)
        cache.delete(timestamp_key)
        cache.delete(pending_user_key)
        
        register_url = reverse('haberler:register') + f'?user_type={user_type}'
        return redirect(register_url)
    # --- YARDIMCI FONKSİYON BİTİŞİ ---

    
    # --- SÜRE KONTROLÜ (ZOMBİ ENGELLEME) ---
    creation_time = cache.get(timestamp_key)

    if creation_time is None:
        messages.error(request, 'Doğrulama kodunuzun süresi dolmuş. Lütfen tekrar kayıt olunuz.')
        return clear_cache_and_redirect(user_email)
    
    elapsed_time = time.time() - creation_time
    remaining_seconds = 300 - int(elapsed_time)

    if remaining_seconds <= 0:
        messages.error(request, 'Doğrulama kodunuzun süresi dolmuş. Lütfen tekrar kayıt olunuz.')
        return clear_cache_and_redirect(user_email)
    # --- SÜRE KONTROLÜ BİTİŞİ ---


    if request.method == 'POST':
        code = request.POST.get('verification_code', '').strip().upper()
        cached_code = cache.get(code_key) 
        current_attempts = cache.get(attempt_key, 0)

        if cached_code and code == cached_code:
            # === BAŞARILI DOĞRULAMA: KULLANICIYI ŞİMDİ OLUŞTUR ===
            
            pending_data = cache.get(pending_user_key)
            if not pending_data:
                messages.error(request, 'Kayıt verisi bulunamadı (süre dolmuş olabilir). Lütfen tekrar kayıt olunuz.')
                return clear_cache_and_redirect(user_email)
            
            try:
                # 1. KULLANICIYI VERİTABANINDA OLUŞTUR

                # Kullanıcı tipi 'yetkili' ise is_staff=True olarak ayarla
                is_staff_flag = True if pending_data.get('user_type') == 'yetkili' else False

                user = User.objects.create(
                username=pending_data['username'],
                email=pending_data['email'],
                password=pending_data['hashed_password'],
                first_name=pending_data['first_name'],
                last_name=pending_data['last_name'],
                is_active=True, # Doğrudan AKTİF olarak başlat!
                is_staff=is_staff_flag # <-- EKLENEN SATIR
           )
                
                # 2. Sinyalin profili 'abone' olarak oluşturmuş olabileceği ihtimaline karşı
                #    profili al (get) veya oluştur (create).
                profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'user_type': pending_data['user_type']}
           )

                # 3. Sinyal 'abone' olarak oluştursa bile, tipi HER ZAMAN
                #    önbellekteki (pending_data) tipe GÜNCELLE.
                if profile.user_type != pending_data['user_type']:
                    profile.user_type = pending_data['user_type']
                    profile.save()
            
            except Exception as e: 
                messages.error(request, f'Hesap oluşturulurken beklenmedik bir hata oluştu: {e}')
                User.objects.filter(email=pending_data['email']).delete()
                return clear_cache_and_redirect(user_email)
            
            # 4. Başarılı olduğuna göre tüm önbelleği temizle
            cache.delete(code_key) 
            cache.delete(attempt_key)
            cache.delete(timestamp_key)
            cache.delete(pending_user_key)
            
            # 5. Kullanıcıyı sisteme giriş yaptır
            login(request, user, backend='django.contrib.auth.backends.ModelBackend') 
            messages.success(request, 'Hesabınız başarıyla doğrulandı! Giriş yaptınız.')
            
            # === DOĞRU YÖNLENDİRME (pending_data'ya göre) ===
            # 6. Dashboard'a önbellekteki tipe göre yönlendir
            if pending_data['user_type'] == 'yetkili':
                return redirect('haberler:yetkili_dashboard')
            else:
                return redirect('haberler:abone_dashboard')
            # === YÖNLENDİRME BİTİŞİ ===
                
        else:
            # === HATALI KOD GİRİŞİ ===
            current_attempts += 1 

            if current_attempts >= 3:
                messages.error(request, '3 kere hatalı girdiniz. Lütfen tekrar kayıt olunuz.')
                return clear_cache_and_redirect(user_email)
            else:
                cache.set(attempt_key, current_attempts, remaining_seconds) 
                remaining = 3 - current_attempts
                messages.error(request, f'Geçersiz doğrulama kodu. Kalan deneme hakkınız: {remaining}')

    # GET isteği VEYA Hatalı kod (deneme hakkı varken)
    return render(request, 'auth/verify_email.html', {
        'user_email': user_email,
        'remaining_seconds': remaining_seconds 
    })

@login_required
def yetki_matrisi(request):
    if not request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim izniniz yok.')
        return redirect('anasayfa')
    
    yetkililer = UserProfile.objects.filter(user_type='yetkili').select_related('user')
    
    if request.method == 'POST':
        for yetkili in yetkililer:
            user_id = yetkili.user.id
            yetkili.can_add_news = request.POST.get(f'can_add_news_{user_id}') == 'on'
            yetkili.can_edit_news = request.POST.get(f'can_edit_news_{user_id}') == 'on'
            yetkili.can_add_column = request.POST.get(f'can_add_column_{user_id}') == 'on'
            yetkili.can_manage_comments = request.POST.get(f'can_manage_comments_{user_id}') == 'on'
            yetkili.save()
            
        messages.success(request, 'Yetki matrisi başarıyla güncellendi.')
        return redirect('haberler:yetki_matrisi')
        
    context = {
        'yetkililer': yetkililer,
        'dashboard_title': 'Yetki Matrisi',
    }
    return render(request, 'auth/yetki_matrisi.html', context)

