from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import Haber
import re

class Command(BaseCommand):
    help = 'Kickboks haberlerindeki boş slug\'ları düzeltir'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🔧 KICKBOKS HABER SLUG\'LARI DÜZELTİLİYOR\n')
        )
        self.stdout.write('=' * 50)
        
        # Kickboks kategorisindeki haberleri al
        kickboks_haberler = Haber.objects.filter(kategori__slug='kickboks')
        
        self.stdout.write(f"📊 Toplam {kickboks_haberler.count()} kickboks haberi bulundu")
        
        # Boş veya geçersiz slug'ları bul
        bos_slug_haberler = kickboks_haberler.filter(slug__in=['', None])
        gecersiz_slug_haberler = kickboks_haberler.exclude(slug__regex=r'^[a-zA-Z0-9_-]+$')
        
        self.stdout.write(f"❌ {bos_slug_haberler.count()} haber boş slug'a sahip")
        self.stdout.write(f"⚠️ {gecersiz_slug_haberler.count()} haber geçersiz slug'a sahip")
        
        duzeltilen_sayisi = 0
        
        # Tüm kickboks haberlerini kontrol et
        for haber in kickboks_haberler:
            try:
                # Mevcut slug'ı kontrol et
                if not haber.slug or not re.match(r'^[a-zA-Z0-9_-]+$', haber.slug):
                    
                    self.stdout.write(f"\n🔧 Düzeltiliyor: {haber.baslik[:50]}...")
                    self.stdout.write(f"   Eski slug: '{haber.slug}'")
                    
                    # Yeni slug oluştur
                    new_slug = self.create_unique_slug(haber.baslik, haber.id)
                    
                    # Slug'ı güncelle
                    haber.slug = new_slug
                    haber.save()
                    
                    self.stdout.write(f"   ✅ Yeni slug: '{new_slug}'")
                    duzeltilen_sayisi += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Hata: {haber.baslik[:30]}... - {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 {duzeltilen_sayisi} haber slug'ı düzeltildi!")
        )
        
        # Kontrol et
        self.verify_slugs()

    def create_unique_slug(self, title, haber_id):
        """Benzersiz slug oluşturur"""
        
        # Başlıktan slug oluştur
        base_slug = slugify(title)
        
        # Eğer slug oluşturulamazsa varsayılan kullan
        if not base_slug:
            base_slug = f"kickboks-haber-{haber_id}"
        
        # Benzersizlik kontrolü
        slug = base_slug
        counter = 1
        
        while Haber.objects.filter(slug=slug).exclude(id=haber_id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

    def verify_slugs(self):
        """Slug'ları doğrular"""
        
        self.stdout.write("\n🔍 SLUG DOĞRULAMA")
        self.stdout.write("-" * 30)
        
        kickboks_haberler = Haber.objects.filter(kategori__slug='kickboks')
        
        # Boş slug kontrolü
        bos_sluglar = kickboks_haberler.filter(slug__in=['', None])
        if bos_sluglar.exists():
            self.stdout.write(
                self.style.ERROR(f"❌ Hala {bos_sluglar.count()} boş slug var!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Boş slug yok")
            )
        
        # Tekrar eden slug kontrolü
        from django.db.models import Count
        tekrar_eden_sluglar = (kickboks_haberler
                              .values('slug')
                              .annotate(count=Count('slug'))
                              .filter(count__gt=1))
        
        if tekrar_eden_sluglar.exists():
            self.stdout.write(
                self.style.ERROR(f"❌ {tekrar_eden_sluglar.count()} tekrar eden slug var!")
            )
            for item in tekrar_eden_sluglar:
                self.stdout.write(f"   - '{item['slug']}' ({item['count']} kez)")
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Tekrar eden slug yok")
            )
        
        # Geçersiz karakter kontrolü
        gecersiz_sluglar = kickboks_haberler.exclude(slug__regex=r'^[a-zA-Z0-9_-]+$')
        if gecersiz_sluglar.exists():
            self.stdout.write(
                self.style.ERROR(f"❌ {gecersiz_sluglar.count()} geçersiz slug var!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Tüm slug'lar geçerli")
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Toplam {kickboks_haberler.count()} kickboks haberi kontrol edildi")
        )