from django.apps import AppConfig


class NmsConfig(AppConfig):
    name = 'native_title_management'

    def ready(self):
        import native_title_management.signals
