from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import PacienteViewSet

# Crear router para registrar viewsets
router = DefaultRouter()
router.register(r'pacientes', PacienteViewSet, basename='paciente')

# URLs generadas automáticamente:
# GET    /api/pacientes/                    - Lista todos los pacientes
# POST   /api/pacientes/                    - Crea un nuevo paciente
# GET    /api/pacientes/{id}/               - Detalle de un paciente específico
# PUT    /api/pacientes/{id}/               - Actualiza completamente un paciente
# PATCH  /api/pacientes/{id}/               - Actualiza parcialmente un paciente
# DELETE /api/pacientes/{id}/               - Elimina un paciente
# POST   /api/pacientes/{id}/cambiar_estado/ - Cambia el estado del paciente
# GET    /api/pacientes/activos/            - Lista pacientes activos
# GET    /api/pacientes/en_espera/          - Lista pacientes en espera
# GET    /api/pacientes/estadisticas/       - Estadísticas de pacientes
# GET    /api/pacientes/{id}/rutas_clinicas/ - Rutas clínicas del paciente
# GET    /api/pacientes/{id}/atenciones/    - Atenciones del paciente

urlpatterns = router.urls