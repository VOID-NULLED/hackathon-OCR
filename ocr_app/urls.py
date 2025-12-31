"""
URL configuration for OCR app - Background service only.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OCRDocumentViewSet, OCRResultViewSet, CodeBlockViewSet
from .video_views import camera_status, health_check

router = DefaultRouter()
router.register(r'documents', OCRDocumentViewSet, basename='document')
router.register(r'results', OCRResultViewSet, basename='result')
router.register(r'code-blocks', CodeBlockViewSet, basename='codeblock')

urlpatterns = [
    path('', include(router.urls)),
    
    # Status endpoints
    path('status/', camera_status, name='camera-status'),
    path('health/', health_check, name='health-check'),
]
