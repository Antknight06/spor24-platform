from django.apps import AppConfig


class HaberlerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'haberler'
    
    def ready(self):
        import haberler.signals