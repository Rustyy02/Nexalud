from django.urls import path
from . import views

urlpatterns = [
    # Métricas generales (carga inicial)
    path('metricas/', 
         views.dashboard_metricas_generales, 
         name='dashboard-metricas'),
    
    # Tiempo real (polling)
    path('tiempo-real/', 
         views.dashboard_metricas_tiempo_real, 
         name='dashboard-tiempo-real'),
    
    # Estadísticas detalladas (gráficos)
    path('estadisticas/', 
         views.dashboard_estadisticas_detalladas, 
         name='dashboard-estadisticas'),
]