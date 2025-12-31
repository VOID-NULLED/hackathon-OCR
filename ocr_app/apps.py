from django.apps import AppConfig


class OcrAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ocr_app'
    verbose_name = 'OCR Application'
    
    def ready(self):
        """Initialize components when Django starts."""
        # Import here to avoid AppRegistryNotReady error
        import logging
        logger = logging.getLogger(__name__)
        
        # Auto-start camera when configured
        try:
            from django.conf import settings
            if getattr(settings, 'AUTO_START_CAMERA', False):
                from .video_capture import start_camera
                logger.info("Auto-starting camera...")
                start_camera()
        except Exception as e:
            logger.warning(f"Could not auto-start camera: {e}")
