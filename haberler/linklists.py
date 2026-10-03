from linkcheck import Linklist
from haberler.models import Haber, FederasyonWebsite, BekleyenHaber, Reklam

class HaberLinklist(Linklist):
    model = Haber
    html_fields = ['icerik']
    url_fields = ['kaynak_url']
    image_fields = ['resim']
    ignore_empty = ['kaynak_url', 'resim']

class FederasyonWebsiteLinklist(Linklist):
    model = FederasyonWebsite
    url_fields = ['ana_url', 'facebook_url', 'instagram_url', 'x_url', 'youtube_url']
    image_fields = ['logo']
    ignore_empty = ['facebook_url', 'instagram_url', 'x_url', 'youtube_url', 'logo']

class BekleyenHaberLinklist(Linklist):
    model = BekleyenHaber
    url_fields = ['kaynak_url', 'kaynak_resim_url']
    ignore_empty = ['kaynak_url', 'kaynak_resim_url']

class ReklamLinklist(Linklist):
    model = Reklam
    url_fields = ['youtube_url', 'iframe_url']
    image_fields = ['resim']
    ignore_empty = ['youtube_url', 'iframe_url', 'resim']

linklists = {
    'Haberler': HaberLinklist,
    'Federasyonlar': FederasyonWebsiteLinklist,
    'BekleyenHaberler': BekleyenHaberLinklist,
    'Reklamlar': ReklamLinklist,
}
