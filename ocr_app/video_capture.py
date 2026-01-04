"""
Real-time video capture and OCR detection service.
Monitors camera feed and automatically captures text/code using GPU-accelerated OCR.
"""
import cv2
import numpy as np
import logging
import time
import threading
from typing import Optional, Tuple, Dict
from collections import deque
from django.conf import settings

logger = logging.getLogger(__name__)


class VideoEnhancer:
    """Enhance video frames for better OCR accuracy."""
    
    @staticmethod
    def deblur_frame(frame: np.ndarray) -> np.ndarray:
        """
        Apply deblurring techniques to improve frame quality.
        """
        # Convert to grayscale for processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to reduce noise while keeping edges
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply unsharp masking for deblurring
        gaussian = cv2.GaussianBlur(denoised, (0, 0), 2.0)
        unsharp = cv2.addWeighted(denoised, 2.0, gaussian, -1.0, 0)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(unsharp)
        
        # Convert back to BGR for consistency
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    @staticmethod
    def enhance_frame(frame: np.ndarray) -> np.ndarray:
        """
        Apply comprehensive enhancement to frame.
        """
        # Deblur
        frame = VideoEnhancer.deblur_frame(frame)
        
        # Increase sharpness
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        frame = cv2.filter2D(frame, -1, kernel)
        
        # Auto brightness/contrast adjustment
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        frame = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return frame


class TextDetector:
    """Detect text and code in video frames using GPU-accelerated OCR."""
    
    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # seconds
        
        # Initialize GPU OCR service
        from .gpu_services import get_gpu_ocr_service
        self.gpu_ocr = get_gpu_ocr_service()
        logger.info(f"TextDetector initialized with GPU OCR (GPU: {self.gpu_ocr.use_gpu})")
    
    def has_text(self, frame: np.ndarray) -> Tuple[bool, float, str]:
        """
        Check if frame contains significant text using GPU OCR.
        
        Returns:
            Tuple of (has_text, confidence, preview_text)
        """
        # Cooldown to avoid excessive processing
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return False, 0.0, ""
        
        try:
            # Use GPU OCR for detection
            result = self.gpu_ocr.process_image_from_array(frame, enhanced=False)
            
            if not result['success']:
                return False, 0.0, ""
            
            text = result['text']
            confidence = result['confidence']
            
            # Check if text exists and confidence is high enough
            if text.strip() and confidence >= self.confidence_threshold * 100:
                self.last_detection_time = current_time
                preview = ' '.join(text.split()[:10])  # First 10 words
                return True, confidence / 100, preview
            
            return False, confidence / 100, text[:50] if text else ""
            
        except Exception as e:
            logger.error(f"Error detecting text with GPU OCR: {e}")
            return False, 0.0, ""
    
    def detect_code_patterns(self, text: str) -> bool:
        """
        Check if detected text contains code patterns.
        """
        code_indicators = [
            'def ', 'class ', 'import ', 'function', 'const ', 'let ',
            'var ', 'public ', 'private ', 'void ', 'return ', 'if(',
            'for(', 'while(', '{', '}', '=>', '==', '!=', '//', '/*'
        ]
        
        return any(indicator in text for indicator in code_indicators)



class RealtimeOCRCamera:
    """
    Real-time camera OCR system with auto-capture.
    """
    
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.camera = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Components
        self.enhancer = VideoEnhancer()
        self.detector = TextDetector(confidence_threshold=0.65)
        
        # Frame buffer for stability
        self.frame_buffer = deque(maxlen=5)
        
        # Statistics
        self.stats = {
            'total_frames': 0,
            'enhanced_frames': 0,
            'detected_text': 0,
            'auto_captures': 0,
            'fps': 0
        }
        
        # Capture queue
        self.capture_queue = []
        self.capture_lock = threading.Lock()
    
    def start(self):
        """Start the camera capture."""
        logger.info(f"Starting camera {self.camera_id}...")
        
        self.camera = cv2.VideoCapture(self.camera_id)
        
        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_id}")
        
        # Set camera properties for better quality
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_running = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        logger.info("Camera started successfully")
    
    def stop(self):
        """Stop the camera capture."""
        logger.info("Stopping camera...")
        self.is_running = False
        
        if self.camera:
            self.camera.release()
        
        logger.info("Camera stopped")
    
    def _capture_loop(self):
        """Continuously capture frames from camera."""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.is_running:
            ret, frame = self.camera.read()
            
            if not ret:
                logger.warning("Failed to read frame from camera")
                time.sleep(0.1)
                continue
            
            # Update stats
            self.stats['total_frames'] += 1
            fps_counter += 1
            
            # Calculate FPS
            if time.time() - fps_start_time >= 1.0:
                self.stats['fps'] = fps_counter
                fps_counter = 0
                fps_start_time = time.time()
            
            # Store frame
            with self.frame_lock:
                self.current_frame = frame.copy()
                self.frame_buffer.append(frame.copy())
            
            # Small delay to control CPU usage
            time.sleep(0.01)
    
    def _process_loop(self):
        """Process frames for text detection and enhancement."""
        while self.is_running:
            frame = None
            
            with self.frame_lock:
                if self.current_frame is not None:
                    frame = self.current_frame.copy()
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            try:
                # Enhance frame
                enhanced_frame = self.enhancer.enhance_frame(frame)
                self.stats['enhanced_frames'] += 1
                
                # Detect text
                has_text, confidence, preview = self.detector.has_text(enhanced_frame)
                
                if has_text:
                    self.stats['detected_text'] += 1
                    
                    # Check if it's code
                    is_code = self.detector.detect_code_patterns(preview)
                    
                    logger.info(
                        f"Text detected! Confidence: {confidence:.2%} | "
                        f"Type: {'CODE' if is_code else 'TEXT'} | "
                        f"Preview: {preview[:50]}..."
                    )
                    
                    # Auto-capture
                    self._auto_capture(enhanced_frame, confidence, preview, is_code)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
            
            # Process at reasonable rate
            time.sleep(0.5)
    
    def _auto_capture(self, frame: np.ndarray, confidence: float, 
                     text_preview: str, is_code: bool):
        """
        Automatically capture frame when text/code is detected.
        Processes with GPU OCR to get enhanced results for FrameMetadata.
        """
        try:
            from .gpu_services import get_gpu_ocr_service
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.png"
            
            # Save frame
            capture_path = f"/tmp/{filename}"
            cv2.imwrite(capture_path, frame)
            
            # Get GPU OCR service and process enhanced frame
            gpu_ocr = get_gpu_ocr_service()
            enhanced_result = gpu_ocr.process_image_from_array(frame, enhanced=True)
            
            # Add to queue for processing
            capture_data = {
                'path': capture_path,
                'timestamp': timestamp,
                'confidence': confidence,
                'preview': text_preview,
                'is_code': is_code,
                'camera_id': f'camera_{self.camera_id}',
                'enhanced_result': enhanced_result  # Include GPU OCR results
            }
            
            with self.capture_lock:
                self.capture_queue.append(capture_data)
                self.stats['auto_captures'] += 1
            
            logger.info(
                f"Auto-captured: {filename} (confidence: {confidence:.2%}, "
                f"GPU: {enhanced_result.get('gpu_used', False)}, "
                f"Blur: {enhanced_result.get('blur_variance', 0):.2f})"
            )
            
        except Exception as e:
            logger.error(f"Error in auto-capture: {e}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the current enhanced frame."""
        with self.frame_lock:
            if self.current_frame is not None:
                frame = self.current_frame.copy()
                return self.enhancer.enhance_frame(frame)
        return None
    
    def get_capture_queue(self) -> list:
        """Get and clear the capture queue."""
        with self.capture_lock:
            queue = self.capture_queue.copy()
            self.capture_queue.clear()
            return queue
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return self.stats.copy()


# Global camera instance
_camera_instance = None
_camera_lock = threading.Lock()


def get_camera() -> RealtimeOCRCamera:
    """Get or create the global camera instance."""
    global _camera_instance
    
    with _camera_lock:
        if _camera_instance is None:
            camera_id = getattr(settings, 'CAMERA_ID', 0)
            _camera_instance = RealtimeOCRCamera(camera_id)
        
        return _camera_instance


def start_camera():
    """Start the global camera."""
    camera = get_camera()
    if not camera.is_running:
        camera.start()


def stop_camera():
    """Stop the global camera."""
    global _camera_instance
    
    with _camera_lock:
        if _camera_instance and _camera_instance.is_running:
            _camera_instance.stop()
            _camera_instance = None
