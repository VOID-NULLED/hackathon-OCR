"""
Real-time video streaming views and endpoints.
"""
import cv2
import logging
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status

from .video_capture import get_camera, start_camera, stop_camera
from .tasks import process_captured_frame_task

logger = logging.getLogger(__name__)


def generate_frames():
    """
    Generator function to stream video frames.
    """
    camera = get_camera()
    
    while True:
        frame = camera.get_frame()
        
        if frame is None:
            continue
        
        # Add stats overlay
        stats = camera.get_stats()
        cv2.putText(
            frame,
            f"FPS: {stats['fps']} | Detected: {stats['detected_text']} | Captures: {stats['auto_captures']}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        
        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@require_http_methods(["GET"])
def video_feed(request):
    """
    Stream live video feed with OCR detection.
    """
    try:
        # Start camera if not running
        camera = get_camera()
        if not camera.is_running:
            start_camera()
        
        return StreamingHttpResponse(
            generate_frames(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error(f"Error in video feed: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def start_camera_endpoint(request):
    """
    Start the camera capture.
    """
    try:
        start_camera()
        camera = get_camera()
        
        return Response({
            'status': 'started',
            'camera_id': camera.camera_id,
            'message': 'Camera started successfully'
        })
    except Exception as e:
        logger.error(f"Error starting camera: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def stop_camera_endpoint(request):
    """
    Stop the camera capture.
    """
    try:
        stop_camera()
        
        return Response({
            'status': 'stopped',
            'message': 'Camera stopped successfully'
        })
    except Exception as e:
        logger.error(f"Error stopping camera: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def camera_stats(request):
    """
    Get camera statistics.
    """
    try:
        camera = get_camera()
        stats = camera.get_stats()
        
        return Response({
            'is_running': camera.is_running,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting camera stats: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_captures(request):
    """
    Get auto-captured frames pending processing.
    """
    try:
        camera = get_camera()
        captures = camera.get_capture_queue()
        
        return Response({
            'count': len(captures),
            'captures': captures
        })
    except Exception as e:
        logger.error(f"Error getting captures: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def process_captures(request):
    """
    Process all captured frames through OCR pipeline.
    """
    try:
        camera = get_camera()
        captures = camera.get_capture_queue()
        
        processed = 0
        for capture in captures:
            # Queue for processing
            task = process_captured_frame_task.delay(capture)
            processed += 1
        
        return Response({
            'processed': processed,
            'message': f'Queued {processed} captures for OCR processing'
        })
    except Exception as e:
        logger.error(f"Error processing captures: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
