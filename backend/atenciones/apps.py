from django.apps import AppConfig


class AtencionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'atenciones'
    def ready(self):
        import atenciones.signals
