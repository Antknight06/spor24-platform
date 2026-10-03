from django.core.management.base import BaseCommand
from haberler.models import FederasyonWebsite
import requests
from urllib.parse import urljoin

class Command(BaseCommand):
    help = 'Federasyon URL\'lerini düzeltir ve çalışan URL\'leri bulur'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\n🌐 FEDERASYON URL\'LERİ DÜZELTİLİYOR\n')
        )
        self.stdout.write('=' * 50)
        
        # Known working URLs for federations
        url_duzeltmeleri = {
            'Türkiye Taekwondo Federasyonu': {
                'ana_url': 'https://taekwondo.org.tr',
                'haberler_url': 'https://taekwondo.org.tr/haberler'
            },
            'Türkiye Judo Federasyonu': {
                'ana_url': 'https://judo.org.tr',
                'haberler_url': 'https://judo.org.tr/haberler'
            },
            'Türkiye Kickboks Federasyonu': {
                'ana_url': 'https://tkbf.gov.tr',
                'haberler_url': 'https://tkbf.gov.tr/tr/haberler'
            },
            'Türkiye Muay Thai Federasyonu': {
                'ana_url': 'https://www.tmtf.gov.tr',
                'haberler_url': 'https://www.tmtf.gov.tr/tr/haberler'
            },
            'Türkiye Boks Federasyonu': {
                'ana_url': 'https://boks.org.tr',
                'haberler_url': 'https://boks.org.tr/haberler'
            },
            'Türkiye Güreş Federasyonu': {
                'ana_url': 'https://gures.org.tr',
                'haberler_url': 'https://gures.org.tr/haberler'
            },
            'Türkiye Kendo Federasyonu': {
                'ana_url': 'https://kendo.org.tr',
                'haberler_url': 'https://kendo.org.tr/haberler'
            }
        }
        
        guncellenen_sayisi = 0
        
        for federasyon_adi, url_data in url_duzeltmeleri.items():
            try:
                federation = FederasyonWebsite.objects.get(ad=federasyon_adi)
                
                # Test if the new URLs work
                try:
                    # Test main URL
                    response_main = requests.get(url_data['ana_url'], timeout=10)
                    # Test news URL
                    response_news = requests.get(url_data['haberler_url'], timeout=10)
                    
                    if response_main.status_code == 200 and response_news.status_code == 200:
                        # Update URLs
                        federation.ana_url = url_data['ana_url']
                        federation.haberler_url = url_data['haberler_url']
                        federation.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {federasyon_adi} URL\'leri güncellendi')
                        )
                        guncellenen_sayisi += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ {federasyon_adi} için URL\'ler çalışmıyor')
                        )
                        
                except requests.RequestException as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ {federasyon_adi} için URL testi başarısız: {e}')
                    )
                    
            except FederasyonWebsite.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {federasyon_adi} bulunamadı')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ İşlem tamamlandı! {guncellenen_sayisi} federasyonun URL\'si güncellendi.'
            )
        )