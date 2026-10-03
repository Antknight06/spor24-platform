from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import Kategori, FederasyonWebsite

class Command(BaseCommand):
    help = 'Yeni bir kategori oluşturur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--isim',
            type=str,
            required=True,
            help='Kategori ismi'
        )
        parser.add_argument(
            '--aciklama',
            type=str,
            help='Kategori açıklaması'
        )
        parser.add_argument(
            '--federasyon',
            type=str,
            help='Federasyon ismi (opsiyonel)'
        )

    def handle(self, *args, **options):
        kategori_ismi = options['isim']
        aciklama = options.get('aciklama') or f'{kategori_ismi} haberleri'
        federasyon_adi = options.get('federasyon')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n➕ YENİ KATEGORİ OLUŞTURULUYOR: {kategori_ismi}\n')
        )
        self.stdout.write('=' * 50)
        
        # Kategori slug oluştur
        kategori_slug = slugify(kategori_ismi)
        
        # Kategori zaten var mı kontrol et
        if Kategori.objects.filter(slug=kategori_slug).exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️  Kategori zaten mevcut: {kategori_ismi}')
            )
            return
        
        # Federasyon varsa bul
        federasyon = None
        if federasyon_adi:
            try:
                federasyon = FederasyonWebsite.objects.get(ad__icontains=federasyon_adi)
            except FederasyonWebsite.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Federasyon bulunamadı: {federasyon_adi}')
                )
        
        # Kategori oluştur
        try:
            kategori = Kategori.objects.create(
                ad=kategori_ismi,
                slug=kategori_slug,
                aciklama=aciklama,
                federasyon_website=federasyon
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Kategori başarıyla oluşturuldu: {kategori.ad}')
            )
            
            if federasyon:
                self.stdout.write(
                    self.style.SUCCESS(f'🔗 Federasyon ile ilişkilendirildi: {federasyon.ad}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Kategori oluşturulurken hata: {e}')
            )