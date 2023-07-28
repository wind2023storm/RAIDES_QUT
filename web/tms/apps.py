from django.apps import AppConfig


class TmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tms'

    def ready(self):
        import tms.signals
