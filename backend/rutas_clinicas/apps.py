from django.apps import AppConfig


class RutasClinicasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rutas_clinicas'
    
    def ready(self):
        """
        Se ejecuta cuando la aplicación está lista.
        Aquí importamos los signals para que se registren.
        """
        import rutas_clinicas.signals  # Importar los signals para registrarlos
        print("✅ Signals de la API registrados correctamente")


