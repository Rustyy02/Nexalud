from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as auth_views

from pacientes.viewsets import PacienteViewSet
from boxes.viewsets import BoxViewSet
from rutas_clinicas.viewsets import RutaClinicaViewSet
from atenciones.viewsets import AtencionViewSet

router = DefaultRouter()

router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'boxes', BoxViewSet, basename='box')
router.register(r'rutas-clinicas', RutaClinicaViewSet, basename='ruta-clinica')
router.register(r'atenciones', AtencionViewSet, basename='atencion')

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include(router.urls)),
    
    # Autenticación por Token ← AGREGAR ESTA LÍNEA
    path('api-token-auth/', auth_views.obtain_auth_token, name='api_token_auth'),
    
    # Autenticación (Django REST Framework)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Dashboard
    path('api/dashboard/', include('dashboard.urls')),
]

# Configuración del admin
admin.site.site_header = "Nexalud Admin"
admin.site.site_title = "Nexalud"
admin.site.index_title = "Panel de Administración"

