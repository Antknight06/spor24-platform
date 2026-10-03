from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from linkcheck.models import Link
from haberler.models import Haber, BekleyenHaber
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def _clean_content_url(obj, url):
    """Clean both <a> hyperlinks and broken <img> gallery tags from icerik"""
    if not hasattr(obj, 'icerik') or not obj.icerik:
        return False
    soup = BeautifulSoup(obj.icerik, 'html.parser')
    modified = False

    # 1. Clean broken img tags
    imgs = soup.find_all('img', src=lambda s: s and url in s)
    if imgs:
        for img in imgs:
            img.decompose()
        modified = True

    # 2. Clean broken a tags
    tags = soup.find_all('a', href=lambda h: h and url in h)
    if tags:
        for a in tags:
            if a.get_text(strip=True).lower() in ['indir', 'download']:
                a.decompose()
            else:
                a.unwrap()
        modified = True

    if modified:
        obj.icerik = str(soup)
        obj.save(update_fields=['icerik'])
    return modified

@staff_member_required
@require_POST
def linkcheck_action(request):
    action = request.POST.get('action')
    
    # 1. DELETE AN ENTIRE NEWS OBJECT (Haberi Tamamen Sil)
    if action == 'delete_object':
        model_name = request.POST.get('model_name')
        object_id = request.POST.get('object_id')
        try:
            if model_name == 'haber':
                obj = Haber.objects.get(id=object_id)
                deleted_title = obj.baslik
                obj.delete()
            elif model_name == 'bekleyenhaber':
                obj = BekleyenHaber.objects.get(id=object_id)
                deleted_title = obj.baslik
                obj.delete()
            else:
                return JsonResponse({'success': False, 'error': f'Geçersiz model: {model_name}'}, status=400)
            
            return JsonResponse({
                'success': True,
                'message': f'"{deleted_title[:45]}..." haberi ve bağlı tüm bağlantıları başarıyla silindi.'
            })
        except Exception as e:
            logger.exception("Error in linkcheck delete_object")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # 2. AUTO-FIX / UNLINK A SINGLE BROKEN LINK (Haberi Koru, Ölü Linki Ayıkla)
    elif action == 'autofix_link':
        link_id = request.POST.get('link_id')
        try:
            link = Link.objects.get(id=link_id)
            obj = link.content_object
            field = link.field
            url = link.url.url
            
            if field == 'kaynak_url' and hasattr(obj, 'kaynak_url'):
                if isinstance(obj, Haber):
                    obj.kaynak_url = None
                else:
                    obj.kaynak_url = 'https://spor24.net/'
                obj.save(update_fields=['kaynak_url'])
            elif field == 'icerik':
                _clean_content_url(obj, url)
            
            link.delete()
            return JsonResponse({
                'success': True,
                'message': 'Kırık link metinden başarıyla ayıklandı. Haber içeriği bozulmadan korundu!'
            })
        except Exception as e:
            logger.exception("Error in linkcheck autofix_link")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # 3. BULK AUTO-FIX ALL BROKEN LINKS (Tek Tıkla Tüm Kırık Linkleri Ayıkla - Haberleri Koru)
    elif action == 'autofix_all_broken':
        try:
            broken_links = list(Link.objects.filter(ignore=False, url__status=False))
            fixed_count = 0
            
            for link in broken_links:
                try:
                    with transaction.atomic():
                        obj = link.content_object
                        if not obj:
                            link.delete()
                            fixed_count += 1
                            continue
                        
                        field = link.field
                        url = link.url.url
                        
                        if field == 'kaynak_url' and hasattr(obj, 'kaynak_url'):
                            if isinstance(obj, Haber):
                                obj.kaynak_url = None
                            else:
                                obj.kaynak_url = 'https://spor24.net/'
                            obj.save(update_fields=['kaynak_url'])
                        elif field == 'icerik':
                            _clean_content_url(obj, url)
                        
                        link.delete()
                        fixed_count += 1
                except Exception as inner_e:
                    logger.warning(f"Failed to fix link {link.id}: {inner_e}")
                
            return JsonResponse({
                'success': True,
                'count': fixed_count,
                'message': f'Mükemmel! {fixed_count} adet kırık link haber metinlerinden ve kaynaklardan otomatik olarak ayıklandı. Hiçbir haber silinmedi, arşiviniz tertemiz hale getirildi!'
            })
        except Exception as e:
            logger.exception("Error in linkcheck autofix_all_broken")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # 4. BULK DELETE ALL BROKEN NEWS (Kırık Link İçeren Tüm Haberleri Toplu Sil)
    elif action == 'delete_all_broken_news':
        try:
            broken_links = Link.objects.filter(ignore=False, url__status=False)
            haber_ids = set()
            bh_ids = set()
            for l in broken_links:
                if l.content_type.model == 'haber':
                    haber_ids.add(l.object_id)
                elif l.content_type.model == 'bekleyenhaber':
                    bh_ids.add(l.object_id)
            
            del_h, _ = Haber.objects.filter(id__in=haber_ids).delete()
            del_bh, _ = BekleyenHaber.objects.filter(id__in=bh_ids).delete()
            
            return JsonResponse({
                'success': True,
                'count': del_h + del_bh,
                'message': f'Toplam {del_h + del_bh} adet haber ve bekleyen haber sistemden tamamen silindi.'
            })
        except Exception as e:
            logger.exception("Error in linkcheck delete_all_broken_news")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Bilinmeyen işlem.'}, status=400)
