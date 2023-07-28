from django.apps import AppConfig


class MediaFileConfig(AppConfig):
    name = 'media_file'

    def ready(self):
        import media_file.signals
