from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import MedicoViewSet, AtencionViewSet
from .viewsets_medico import MedicoAtencionesViewSet

router = DefaultRouter()
router.register(r'medicos', MedicoViewSet, basename='medico')
router.register(r'atenciones', AtencionViewSet, basename='atencion')

# ✅ NUEVO: Endpoint para vista de médicos
router.register(r'medico/atenciones', MedicoAtencionesViewSet, basename='medico-atenciones')

urlpatterns = router.urls