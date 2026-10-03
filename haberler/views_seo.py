import datetime
from xml.sax.saxutils import escape
from django.http import HttpResponse
from django.utils import timezone
from django.urls import reverse
from django.contrib.sitemaps.views import sitemap as django_sitemap
from .models import Haber

def clean_xml(text):
    if not text:
        return ""
    # Remove null characters and illegal XML control characters
    text = "".join(c for c in str(text) if ord(c) >= 32 or c in "\n\r\t")
    return escape(text)

def clean_sitemap_view(request, sitemaps, **kwargs):
    """
    Standard sitemap view but explicitly strips the Django default
    'X-Robots-Tag: noindex, noodp, noarchive' header so search engines
    and SEO crawlers have full indexing permissions.
    """
    response = django_sitemap(request, sitemaps=sitemaps, **kwargs)
    if 'X-Robots-Tag' in response.headers:
        del response.headers['X-Robots-Tag']
    return response

def google_news_sitemap(request):
    """
    Google News Standard XML Sitemap (schema: sitemap-news/0.9)
    Includes news articles published in the last 48 hours (or last 30 articles fallback)
    """
    domain = "https://spor24.net"
    cutoff = timezone.now() - datetime.timedelta(days=2)
    
    # Query news in the last 48 hours
    articles = Haber.objects.filter(yayinlandi=True, olusturma_tarihi__gte=cutoff).order_by('-olusturma_tarihi')
    
    # If fewer than 10 articles in last 48 hours, fall back to last 30 articles so feed is never empty
    if articles.count() < 10:
        articles = Haber.objects.filter(yayinlandi=True).order_by('-olusturma_tarihi')[:30]

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
    ]

    for item in articles:
        loc = domain + reverse('haberler:haber_detay', args=[item.slug])
        # Format date as ISO 8601 with colon timezone (e.g. 2026-09-27T14:30:00+03:00)
        d = item.olusturma_tarihi
        now = timezone.now()
        if d > now: d = now
        pub_date = d.strftime('%Y-%m-%dT%H:%M:%S%z')
        if len(pub_date) >= 5 and pub_date[-5] in ('+', '-'):
            pub_date = pub_date[:-2] + ':' + pub_date[-2:]
            
        title = clean_xml(item.baslik)
        
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{loc}</loc>')
        xml_lines.append('    <news:news>')
        xml_lines.append('      <news:publication>')
        xml_lines.append('        <news:name>Spor24</news:name>')
        xml_lines.append('        <news:language>tr</news:language>')
        xml_lines.append('      </news:publication>')
        xml_lines.append(f'      <news:publication_date>{pub_date}</news:publication_date>')
        xml_lines.append(f'      <news:title>{title}</news:title>')
        xml_lines.append('    </news:news>')
        
        # Add image tag for Google Images & Discover carousel
        if item.resim:
            img_url = domain + item.resim.url
            xml_lines.append('    <image:image>')
            xml_lines.append(f'      <image:loc>{img_url}</image:loc>')
            xml_lines.append(f'      <image:title>{title}</image:title>')
            xml_lines.append('    </image:image>')
        elif getattr(item, 'kaynak_resim_url', None):
            xml_lines.append('    <image:image>')
            xml_lines.append(f'      <image:loc>{clean_xml(item.kaynak_resim_url)}</image:loc>')
            xml_lines.append(f'      <image:title>{title}</image:title>')
            xml_lines.append('    </image:image>')
            
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')
    content = '\n'.join(xml_lines)
    
    response = HttpResponse(content, content_type='application/xml; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=900'
    response['X-Robots-Tag'] = 'index, follow'
    return response


def news_rss_feed(request):
    """
    Google News & RSS 2.0 compliant feed with MediaRSS enclosures
    """
    domain = "https://spor24.net"
    articles = Haber.objects.filter(yayinlandi=True).order_by('-olusturma_tarihi')[:50]
    build_date = timezone.now().strftime("%a, %d %b %Y %H:%M:%S +0300")
    
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/">',
        '  <channel>',
        '    <title>Spor24 - Son Dakika Spor Haberleri</title>',
        '    <link>https://spor24.net/</link>',
        '    <description>Türkiye ve Dünya spor gündemi, federasyon haberleri, analizler ve özel röportajlar.</description>',
        '    <language>tr</language>',
        f'    <lastBuildDate>{build_date}</lastBuildDate>'
    ]

    for item in articles:
        loc = domain + reverse('haberler:haber_detay', args=[item.slug])
        title = clean_xml(item.baslik)
        desc = clean_xml(item.ozet)
        author_name = clean_xml(item.yazar.get_full_name() or item.yazar.username)
        pub_date = item.olusturma_tarihi.strftime("%a, %d %b %Y %H:%M:%S +0300")
        cat_name = clean_xml(item.kategori.ad if item.kategori else "Spor")
        
        xml_lines.append('    <item>')
        xml_lines.append(f'      <title>{title}</title>')
        xml_lines.append(f'      <link>{loc}</link>')
        xml_lines.append(f'      <guid isPermaLink="true">{loc}</guid>')
        xml_lines.append(f'      <description>{desc}</description>')
        xml_lines.append(f'      <dc:creator>{author_name}</dc:creator>')
        xml_lines.append(f'      <pubDate>{pub_date}</pubDate>')
        xml_lines.append(f'      <category>{cat_name}</category>')
        
        if item.resim:
            img_url = domain + item.resim.url
            xml_lines.append(f'      <enclosure url="{img_url}" type="image/jpeg" length="0" />')
            xml_lines.append(f'      <media:content url="{img_url}" medium="image"><media:title>{title}</media:title></media:content>')
        elif getattr(item, 'kaynak_resim_url', None):
            k_url = clean_xml(item.kaynak_resim_url)
            xml_lines.append(f'      <enclosure url="{k_url}" type="image/jpeg" length="0" />')
            xml_lines.append(f'      <media:content url="{k_url}" medium="image"><media:title>{title}</media:title></media:content>')
            
        xml_lines.append('    </item>')

    xml_lines.append('  </channel>')
    xml_lines.append('</rss>')
    
    content = '\n'.join(xml_lines)
    response = HttpResponse(content, content_type='application/rss+xml; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=900'
    return response


def custom_robots_txt(request):
    """
    Modern, SEO-compliant robots.txt allowing search engines full access to news and categories
    while protecting admin and internal APIs.
    """
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /api/\n"
        "Disallow: /yetkili-giris/\n"
        "Disallow: /cikis/\n"
        "Disallow: /reklam-proxy/\n\n"
        "User-agent: Googlebot-News\n"
        "Allow: /\n\n"
        "Sitemap: https://spor24.net/sitemap.xml\n"
        "Sitemap: https://spor24.net/sitemap-news.xml\n"
    )
    return HttpResponse(content, content_type="text/plain; charset=utf-8")
