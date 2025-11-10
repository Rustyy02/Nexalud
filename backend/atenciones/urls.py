# backend/atenciones/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import MedicoViewSet, AtencionViewSet
from .viewsets_medico import MedicoAtencionesViewSet

# Router principal
router = DefaultRouter()
router.register(r'medicos', MedicoViewSet, basename='medico')
router.register(r'atenciones', AtencionViewSet, basename='atencion')

# Router separado para endpoints de médicos
medico_router = DefaultRouter()
medico_router.register(r'atenciones', MedicoAtencionesViewSet, basename='medico-atenciones')

urlpatterns = [
    path('', include(router.urls)),
    path('medico/', include(medico_router.urls)),  # /api/medico/atenciones/
]