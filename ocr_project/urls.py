"""
URL configuration for ocr_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def root_view(request):
    """Root endpoint showing service information"""
    return JsonResponse({
        'service': 'Real-time OCR Camera Service',
        'status': 'running',
        'info': 'Camera automatically opens on startup and processes OCR in background.',
        'endpoints': {
            'status': '/api/status/',
            'health': '/api/health/',
            'documents': '/api/documents/',
            'results': '/api/results/',
            'admin': '/admin/'
        }
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('ocr_app.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
