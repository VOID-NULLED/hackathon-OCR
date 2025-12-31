"""
URL configuration for OCR app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OCRDocumentViewSet, OCRResultViewSet, CodeBlockViewSet
from .video_views import (
    video_feed, start_camera_endpoint, stop_camera_endpoint,
    camera_stats, get_captures, process_captures
)
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'documents', OCRDocumentViewSet, basename='document')
router.register(r'results', OCRResultViewSet, basename='result')
router.register(r'code-blocks', CodeBlockViewSet, basename='codeblock')

urlpatterns = [
    path('', include(router.urls)),
    
    # Video endpoints
    path('video/feed/', video_feed, name='video-feed'),
    path('video/start/', start_camera_endpoint, name='video-start'),
    path('video/stop/', stop_camera_endpoint, name='video-stop'),
    path('video/stats/', camera_stats, name='video-stats'),
    path('video/captures/', get_captures, name='video-captures'),
    path('video/process-captures/', process_captures, name='process-captures'),
    
    # Live camera UI
    path('live/', TemplateView.as_view(template_name='live_camera.html'), name='live-camera'),
]
