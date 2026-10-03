from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from haberler.models import Haber, Kategori
import requests
from bs4 import BeautifulSoup
import re


class Command(BaseCommand):
    help = 'Jiu Jutsu (jujitsuturkiye.com) bozuk haberleri düzeltir; düzelmeyenleri siler'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=200, help='İşlenecek maksimum haber sayısı')
        parser.add_argument('--dry-run', action='store_true', help='Sadece raporla, değişiklik yapma')

    def handle(self, *args, **options):
        limit = options['limit']
        dry = options['dry_run']

        self.stdout.write('🥋 JIU JUTSU BOZUK HABER TEMİZLİĞİ')
        self.stdout.write('=' * 50)

        bad_title_patterns = Q(baslik__iexact='DevamńĪ ¬Ľ') | Q(baslik__istartswith='Haberler - ')
        bad_content_patterns = Q(icerik__icontains='Ju Jitsu Türkiye Federasyonu Resmi İnternet Sitesi') | Q(icerik__iregex=r'ANA SAYFA\s*FEDERASYON KURULLARI')
        domain_filter = Q(kaynak_url__icontains='jujitsuturkiye.com')
        cat_filter = Q(kategori__ad__iregex='jiu|jutsu')

        qs = Haber.objects.filter(domain_filter & (bad_title_patterns | bad_content_patterns)).order_by('-olusturma_tarihi')
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f'📊 Aday haber: {total}')
        if total == 0:
            return

        fixed, deleted = 0, 0
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
        })

        for i, haber in enumerate(qs, 1):
            try:
                self.stdout.write(f"[{i}/{total}] İşleniyor: {haber.baslik[:60]}...")
                r = session.get(haber.kaynak_url, timeout=30, verify=False)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')

                new_title = self._extract_title(soup) or haber.baslik
                new_content = self._extract_clean_content(soup)

                # Baslık/icerik doğrulama: içerik uzunluğu ve nav spam kontrolü
                content_ok = new_content and len(new_content) >= 200 and not self._looks_like_menu(new_content)
                title_ok = new_title and len(new_title.strip()) >= 5 and not new_title.strip().lower().startswith('haberler -') and 'devam' not in new_title.lower()

                if content_ok and title_ok:
                    if not dry:
                        haber.baslik = new_title[:200]
                        haber.ozet = new_title[:500]
                        haber.icerik = new_content[:15000]
                        haber.save(update_fields=['baslik', 'ozet', 'icerik'])
                    fixed += 1
                    self.stdout.write('   ✅ Düzeltildi')
                else:
                    if not dry:
                        haber.delete()
                    deleted += 1
                    self.stdout.write('   🗑️  Silindi (düzeltilemedi)')

            except Exception as e:
                self.stdout.write(f'   ⚠️  Atlandı: {e}')
                continue

        self.stdout.write(f'\n📌 Sonuç: {fixed} düzeltildi, {deleted} silindi')

    def _extract_title(self, soup: BeautifulSoup):
        for sel in ['h1.entry-title', 'h1.post-title', 'article h1', 'h1', 'title']:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t:
                    # Title etiketinde site adı varsa kırp
                    t = re.sub(r'\s*[-|–].*$', '', t).strip()
                    return t
        og = soup.find('meta', property='og:title')
        if og and og.get('content'):
            return og['content'].strip()
        return None

    def _extract_clean_content(self, soup: BeautifulSoup):
        # Ana içerik adayları
        candidates = [
            'article', '.single-post', '.post', '.entry-content', '.post-content',
            '.content', 'main', '#content'
        ]
        content_el = None
        for sel in candidates:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 150:
                content_el = el
                break
        if not content_el:
            content_el = soup.find('body') or soup

        # İstenmeyen kısımlar
        unwanted = [
            'nav', 'header', 'footer', 'aside', '.navigation', '.menu', '.sidebar',
            '.header', '.footer', '#menu', '#navigation', '#sidebar', '#header', '#footer',
            '.breadcrumb', '.pagination', '.comments', '.advertisement', '.ads', '.widget',
            '.share-buttons', '.tags', '.author-box', '.post-meta', '.entry-meta', '.logo',
            '.branding', '.site-header', '.site-footer', '.main-navigation'
        ]
        for sel in unwanted:
            for el in content_el.select(sel):
                el.decompose()

        text = content_el.get_text('\n', strip=True)

        # Menü/altbilgi tekrarlarını temizle
        lines = [ln for ln in text.split('\n') if ln.strip()]
        cleaned = []
        nav_keywords = [
            'ANA SAYFA', 'FEDERASYON', 'KURULLAR', 'YÖNETMELİK', 'MÜSABAKA', 'İLETİŞİM',
            'EN ÇOK OKUNAN', 'GÜNCEL DUYURULAR', 'HAKKIMIZDA', 'İl Temsilcileri', 'Basında'
        ]
        for ln in lines:
            up = ln.upper()
            if any(k in up for k in nav_keywords):
                continue
            cleaned.append(ln)

        content = '\n'.join(cleaned)
        # Alt kısım telif/slogan
        content = re.sub(r'Ju Jitsu Türkiye Federasyonu Resmi İnternet Sitesi.*$', '', content, flags=re.I|re.S)
        return content.strip()

    def _looks_like_menu(self, text: str) -> bool:
        return 'ANA SAYFA' in text.upper() and 'FEDERASYON' in text.upper() and 'KURULLAR' in text.upper()


