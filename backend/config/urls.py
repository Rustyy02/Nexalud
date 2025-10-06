"URLs principales para el proyecto"

from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include('pacientes.urls')),
    path('api/', include('rutas_clinicas.urls')),
    path('api/', include('boxes.urls')),
    path('api/', include('atenciones.urls')),
    
    # Autenticación (Django REST Framework)
    path('api-auth/', include('rest_framework.urls')),
]

# Configuración del admin
admin.site.site_header = "Nexalud Admin"
admin.site.site_title = "Nexalud"
admin.site.index_title = "Panel de Administración"