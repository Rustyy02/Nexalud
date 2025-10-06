from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import BoxViewSet

router = DefaultRouter()
router.register(r'boxes', BoxViewSet, basename='box')

urlpatterns = router.urls