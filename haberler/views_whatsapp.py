from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json, urllib.request, base64, os, re, mimetypes
from .models import Haber
from django.conf import settings

TARGET_MAP = {
    "kenan": {
        "jid": "905425329090@s.whatsapp.net",
        "name": "Kenan ANT (Şahsi Hesabım)",
        "is_newsletter": False
    },
    "ant_tv": {
        "jid": "120363185266313023@newsletter",
        "name": "Ant Tv Kanalı",
        "is_newsletter": True
    },
    "spor_medya": {
        "jid": "120363409614734849@newsletter",
        "name": "Spor Medya Merkezi",
        "is_newsletter": True
    }
}

@require_http_methods(["GET", "POST"])
def api_whatsapp_channel_share(request, news_id):
    # Sadece yetkili editör veya master token
    is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    token = request.headers.get("token") or request.GET.get("token")
    if not is_admin and token != "Spor24MasterToken2026!":
        return JsonResponse({"success": False, "error": "Yetkisiz erişim. Sadece editör ve yöneticiler paylaşım yapabilir."}, status=403)
        
    try:
        haber = Haber.objects.get(id=news_id)
        target_key = request.GET.get("target") or request.POST.get("target") or "kenan"
        target_info = TARGET_MAP.get(target_key, TARGET_MAP["kenan"])
        phone_target = target_info["jid"]
        target_name = target_info["name"]
        is_newsletter = target_info.get("is_newsletter", False)
        
        title = haber.baslik
        ozet = haber.ozet or ""
        if not ozet and haber.icerik:
            clean_txt = re.sub(r"<[^>]+>", "", haber.icerik)
            ozet = clean_txt[:220].strip()
            
        url = f"https://spor24.net/post.html?id={haber.id}"
        
        image_path = None
        if haber.resim:
            image_path = os.path.join(settings.MEDIA_ROOT, str(haber.resim))
            
        has_image = bool(image_path and os.path.exists(image_path))
        
        # Akıllı Mod Seçimi:
        # WhatsApp Kanalları (@newsletter) E2EE kart önizlemelerini çözemediği ve flu gösterdiği için
        # kanallarda ve görseli olan haberlerde HER ZAMAN 'image' (HD Afiş) modu kullanılır.
        # Böylece kanal akışında dev 1200x675 görsel, sıfır flu, sıfır indirme butonuyla cam gibi görünür.
        mode_param = request.GET.get("mode") or request.POST.get("mode")
        if mode_param:
            mode = mode_param
        elif has_image:
            mode = "image"
        else:
            mode = "card"
            
        airtag_link = f"https://spor24.net/c/{haber.id}?tag=wa_channel"
        
        if mode == "image" and has_image:
            mime, _ = mimetypes.guess_type(image_path)
            mime = mime or "image/jpeg"
            
            with open(image_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
                
            caption = f"🏆 {title}\n\n{ozet}\n\nDetaylar için 👇\n🔗 {airtag_link}"
            payload = {
                "Phone": phone_target,
                "Image": f"data:{mime};base64,{b64_data}",
                "Caption": caption
            }
            api_url = "http://localhost:8085/chat/send/image"
        else:
            # Görseli olmayan veya özellikle kart istenen durumlarda metin + link preview
            body_text = f"🏆 {title}\n\n{ozet}\n\nDetaylar için 👇\n{airtag_link}"
            payload = {
                "Phone": phone_target,
                "Body": body_text,
                "LinkPreview": True
            }
            api_url = "http://localhost:8085/chat/send/text"
            
        tokens_to_try = [
            "Spor24MasterToken2026!",
            "AysunKarateWuzapiToken2026!"
        ]
        
        last_error = None
        res_data = None
        
        for w_token in tokens_to_try:
            try:
                req = urllib.request.Request(
                    api_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "token": w_token
                    },
                    method="POST"
                )
                resp = urllib.request.urlopen(req, timeout=15)
                res_data = json.loads(resp.read().decode("utf-8"))
                last_error = None
                break
            except urllib.error.HTTPError as http_err:
                try:
                    err_body = http_err.read().decode("utf-8")
                    err_json = json.loads(err_body)
                    last_error = err_json.get("error") or http_err.reason
                except:
                    last_error = str(http_err)
            except Exception as ex:
                last_error = str(ex)

        if res_data is not None:
            return JsonResponse({
                "success": True,
                "message": f"{target_name} hedefine başarıyla gönderildi.",
                "target": phone_target,
                "target_name": target_name,
                "news_id": haber.id,
                "mode": mode,
                "data": res_data
            })
        else:
            return JsonResponse({
                "success": False,
                "error": f"WhatsApp Bağlantı Uyarısı: {last_error or 'Oturum bağlı değil'}"
            }, status=500)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
