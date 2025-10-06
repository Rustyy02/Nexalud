from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import MedicoViewSet, AtencionViewSet

router = DefaultRouter()
router.register(r'medicos', MedicoViewSet, basename='medico')
router.register(r'atenciones', AtencionViewSet, basename='atencion')

urlpatterns = router.urls