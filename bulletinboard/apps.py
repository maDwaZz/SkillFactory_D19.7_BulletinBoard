from django.apps import AppConfig


class BulletinboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bulletinboard'

    def ready(self):
        import bulletinboard.signals