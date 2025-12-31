"""
URL configuration for OCR app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OCRDocumentViewSet, OCRResultViewSet, CodeBlockViewSet

router = DefaultRouter()
router.register(r'documents', OCRDocumentViewSet, basename='document')
router.register(r'results', OCRResultViewSet, basename='result')
router.register(r'code-blocks', CodeBlockViewSet, basename='codeblock')

urlpatterns = [
    path('', include(router.urls)),
]
