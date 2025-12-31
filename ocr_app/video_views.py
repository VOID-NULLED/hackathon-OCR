"""
Background camera service status endpoints - No frontend.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .video_capture import get_camera
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def camera_status(request):
    """Get camera status and statistics"""
    camera = get_camera()
    stats = camera.get_stats()
    stats['message'] = 'Camera is running in background. Real-time OCR processing active.'
    stats['running'] = camera.is_running
    return JsonResponse(stats)


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    camera = get_camera()
    return JsonResponse({
        'status': 'healthy',
        'camera_running': camera.is_running,
        'message': 'Real-time OCR service active'
    })
