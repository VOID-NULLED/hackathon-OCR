from django.apps import AppConfig
import logging
import os

logger = logging.getLogger(__name__)

class OcrAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ocr_app'
    verbose_name = 'OCR Application'
    
    def ready(self):
        """Start camera automatically when Django starts"""
        # Only run once in the main process
        run_once = os.environ.get('WERKZEUG_RUN_MAIN')
        if run_once == 'true':
            return
            
        try:
            from django.conf import settings
            from .video_capture import get_camera, start_camera
            
            if getattr(settings, 'AUTO_START_CAMERA', True):
                logger.info("=" * 60)
                logger.info("🎥 STARTING REAL-TIME OCR CAMERA SERVICE")
                logger.info("=" * 60)
                
                start_camera()
                camera = get_camera()
                
                if camera.is_running:
                    logger.info("✅ Camera opened successfully!")
                    logger.info("✅ Video enhancement: ACTIVE")
                    logger.info("✅ Real-time text detection: ACTIVE")  
                    logger.info("✅ Auto-save to database: ACTIVE")
                    logger.info("=" * 60)
                    logger.info("Service is running in background...")
                else:
                    logger.warning("⚠️  Camera failed to start - check camera availability")
                    
        except Exception as e:
            logger.error(f"❌ Failed to start camera service: {e}")
    
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
