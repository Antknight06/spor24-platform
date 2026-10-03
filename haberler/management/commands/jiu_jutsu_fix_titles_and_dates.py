from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from haberler.models import Haber, Kategori, FederasyonWebsite
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime


class Command(BaseCommand):
    help = "Jiu Jutsu (jujitsuturkiye.com) haberlerinin başlık ve tarihlerini düzeltir"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=int, default=200, help='Düzeltilecek maksimum haber sayısı'
        )
        parser.add_argument(
            '--dry-run', action='store_true', help='Gerçekten kaydetmeden göster'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry = options['dry_run']

        self.stdout.write('🥋 JIU JUTSU BAŞLIK ve TARİH DÜZELTME')
        self.stdout.write('=' * 50)

        fed = FederasyonWebsite.objects.filter(
            Q(ana_url__icontains='jujitsuturkiye.com') | Q(ad__icontains='Jiu') | Q(ad__icontains='Jutsu')
        ).first()

        if not fed:
            self.stdout.write(self.style.ERROR('❌ Jiu Jutsu federasyonu bulunamadı'))
            return

        kategori = Kategori.objects.filter(ad__iregex=r"jiu|jutsu|jujitsu|ju-jitsu").first()

        haberler = Haber.objects.filter(
            Q(federasyon_website=fed) | Q(kategori=kategori),
            kaynak_url__icontains='jujitsuturkiye.com'
        ).order_by('-olusturma_tarihi')[:limit]

        if not haberler:
            self.stdout.write(self.style.WARNING('⚠️  Düzeltilecek haber bulunamadı'))
            return

        fixed = 0
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
        })

        for i, haber in enumerate(haberler, 1):
            try:
                self.stdout.write(f"[{i}] İşleniyor: {haber.baslik[:60]}...")
                r = session.get(haber.kaynak_url, timeout=30, verify=False)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')

                new_title = self._extract_title(soup) or haber.baslik
                new_date = self._extract_date(soup, haber)

                changed = False

                if new_title and self._normalize(new_title) != self._normalize(haber.baslik):
                    self.stdout.write(f"   🏷️  Başlık: '{haber.baslik[:50]}' → '{new_title[:50]}'")
                    if not dry:
                        haber.baslik = new_title[:200]
                    changed = True

                if new_date and (not haber.olusturma_tarihi or new_date.date() != haber.olusturma_tarihi.date()):
                    self.stdout.write(f"   📅 Tarih: {haber.olusturma_tarihi} → {new_date}")
                    if not dry:
                        haber.olusturma_tarihi = timezone.make_aware(new_date) if timezone.is_naive(new_date) else new_date
                    changed = True

                if changed and not dry:
                    haber.save(update_fields=['baslik', 'olusturma_tarihi'])
                    fixed += 1
                    self.stdout.write("   ✅ Güncellendi")
                elif not changed:
                    self.stdout.write("   ⏭️  Değişiklik yok")

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   ⚠️  Atlandı: {e}"))
                continue

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Toplam {fixed} haber güncellendi"))

    def _normalize(self, s: str) -> str:
        return (s or '').strip().lower()

    def _extract_title(self, soup: BeautifulSoup):
        # Prefer h1, then og:title, then title
        for sel in ['h1.entry-title', 'h1.post-title', 'h1']:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t:
                    return t
        meta = soup.find('meta', property='og:title')
        if meta and meta.get('content'):
            return meta['content'].strip()
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return None

    def _extract_date(self, soup: BeautifulSoup, haber):
        # 0) Try schema.org JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string or '')
                candidates = data if isinstance(data, list) else [data]
                for obj in candidates:
                    if isinstance(obj, dict):
                        for key in ['datePublished', 'dateModified', 'uploadDate']:
                            if obj.get(key):
                                dt = self._parse_any_date(obj[key])
                                if dt:
                                    return dt
            except Exception:
                pass

        # 1) Try common meta tags
        meta_props = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'article:published_time'}),
            ('meta', {'name': 'pubdate'}),
            ('meta', {'name': 'date'}),
            ('meta', {'itemprop': 'datePublished'}),
            ('time', {}),
        ]
        for tag, attrs in meta_props:
            el = soup.find(tag, attrs=attrs)
            if el:
                val = el.get('content') or el.get('datetime') or el.get_text(strip=True)
                dt = self._parse_any_date(val)
                if dt:
                    return dt

        # 2) Search visible text for Turkish dates
        text = soup.get_text("\n", strip=True)
        # Examples: 15 Ocak 2024, 15.01.2024, 15/01/2024, 2024-01-15
        candidates = re.findall(r"(\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4})", text, flags=re.I)
        if candidates:
            dt = self._parse_any_date(candidates[0][0])
            if dt:
                return dt
        for pat in [r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b", r"\b\d{4}-\d{1,2}-\d{1,2}\b"]:
            m = re.search(pat, text)
            if m:
                dt = self._parse_any_date(m.group(0))
                if dt:
                    return dt

        # 3) Try within likely content containers
        for sel in ['article', '.single-post', '.post', '.entry-content', '.post-content', '.content', 'main', '#content']:
            el = soup.select_one(sel)
            if not el:
                continue
            t = el.get_text("\n", strip=True)
            m = re.search(r"(\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4})", t, flags=re.I)
            if m:
                dt = self._parse_any_date(m.group(1))
                if dt:
                    return dt
            for pat in [r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b", r"\b\d{4}-\d{1,2}-\d{1,2}\b"]:
                m = re.search(pat, t)
                if m:
                    dt = self._parse_any_date(m.group(0))
                    if dt:
                        return dt

        # 4) URL-based hints
        try:
            from urllib.parse import urlparse
            path = urlparse(haber.kaynak_url).path
            m = re.search(r"((?:19|20)\d{2})[\-/](\d{1,2})[\-/](\d{1,2})", path)
            if m:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return datetime(y, mo, d)
            yonly = re.search(r"(19|20)\d{2}", path)
            if yonly:
                y = int(yonly.group(0))
                return datetime(y, 7, 1)
        except Exception:
            pass

        return None

    def _parse_any_date(self, s: str):
        if not s:
            return None
        s = s.strip()
        try:
            months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", s, flags=re.I)
            if m:
                day = int(m.group(1))
                mon = months.get(m.group(2).lower())
                year = int(m.group(3))
                if mon:
                    return datetime(year, mon, day)
            m = re.match(r"(\d{1,2})[.](\d{1,2})[.](\d{4})", s)
            if m:
                d, mo, y = map(int, m.groups())
                return datetime(y, mo, d)
            m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
            if m:
                d, mo, y = map(int, m.groups())
                return datetime(y, mo, d)
            m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
            if m:
                y, mo, d = map(int, m.groups())
                return datetime(y, mo, d)
            # ISO datetime with time
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?", s)
            if m:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return datetime(y, mo, d)
        except Exception:
            return None
        return None


