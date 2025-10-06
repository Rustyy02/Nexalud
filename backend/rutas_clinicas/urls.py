from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import RutaClinicaViewSet, EtapaRutaViewSet

router = DefaultRouter()
router.register(r'rutas-clinicas', RutaClinicaViewSet, basename='ruta-clinica')
router.register(r'etapas', EtapaRutaViewSet, basename='etapa')

# URLs generadas automáticamente:
# 
# RUTAS CLÍNICAS:
# GET    /api/rutas-clinicas/                          - Lista todas las rutas
# POST   /api/rutas-clinicas/                          - Crea una nueva ruta
# GET    /api/rutas-clinicas/{id}/                     - Detalle de una ruta
# GET    /api/rutas-clinicas/{id}/timeline/            - Timeline completo (IMPORTANTE)
# POST   /api/rutas-clinicas/{id}/recalcular_progreso/ - Recalcula progreso
# POST   /api/rutas-clinicas/{id}/pausar/              - Pausa la ruta
# POST   /api/rutas-clinicas/{id}/reanudar/            - Reanuda la ruta
# GET    /api/rutas-clinicas/{id}/retrasos/            - Etapas con retraso
# 
# ETAPAS:
# GET    /api/etapas/                                  - Lista todas las etapas
# POST   /api/etapas/                                  - Crea una nueva etapa
# GET    /api/etapas/{id}/                             - Detalle de una etapa
# POST   /api/etapas/{id}/iniciar/                     - Inicia la etapa
# POST   /api/etapas/{id}/finalizar/                   - Finaliza la etapa
# POST   /api/etapas/{id}/pausar/                      - Pausa etapa (nodo estático)
# POST   /api/etapas/{id}/reanudar/                    - Reanuda etapa pausada
# GET    /api/etapas/{id}/progreso/                    - Info detallada progreso

urlpatterns = router.urls