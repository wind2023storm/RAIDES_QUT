from django.apps import AppConfig


class LmsConfig(AppConfig):
    name = 'lms'

    def ready(self):
        import lms.signals
