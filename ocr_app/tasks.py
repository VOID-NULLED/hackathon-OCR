"""
Celery tasks for asynchronous OCR processing.
"""
import os
import time
import logging
from celery import shared_task
from django.core.files.base import File

from .models import OCRDocument, OCRResult, CodeBlock, ProcessingLog
from .services import OCRService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_ocr_task(self, document_id: str, language: str = 'eng'):
    """
    Celery task to process OCR on uploaded documents.
    
    Args:
        document_id: UUID of the OCRDocument
        language: Language code for OCR processing
    
    Returns:
        dict: Processing result with success status
    """
    try:
        # Get document
        document = OCRDocument.objects.get(id=document_id)
        
        # Mark as processing
        document.mark_processing()
        
        # Log start
        ProcessingLog.objects.create(
            document=document,
            level='info',
            message=f'Started OCR processing with language: {language}',
            details={'task_id': self.request.id}
        )
        
        # Initialize OCR service
        ocr_service = OCRService()
        
        # Get file path
        file_path = document.file.path
        file_extension = os.path.splitext(file_path)[1].lower()
        
        start_time = time.time()
        
        # Process based on file type
        if file_extension == '.pdf':
            results = ocr_service.process_pdf(file_path, language)
        else:
            result = ocr_service.process_image(file_path, language)
            results = [result]
        
        # Save results to database
        for result_data in results:
            if not result_data.get('success', False):
                raise Exception(result_data.get('error', 'OCR processing failed'))
            
            # Determine content type
            content_type = ocr_service.analyze_text_type(result_data['text'])
            
            # Create OCR result
            ocr_result = OCRResult.objects.create(
                document=document,
                extracted_text=result_data['text'],
                content_type=content_type,
                language=result_data['language'],
                confidence=result_data.get('confidence', 0),
                page_number=result_data.get('page_number', 1)
            )
            
            # Detect and save code blocks
            if content_type in ['code', 'mixed']:
                code_blocks = ocr_service.detect_code_blocks(result_data['text'])
                
                for block_data in code_blocks:
                    CodeBlock.objects.create(
                        ocr_result=ocr_result,
                        code_content=block_data['code'],
                        detected_language=block_data['language'],
                        line_start=block_data['line_start'],
                        line_end=block_data['line_end']
                    )
            
            # Log success for this page
            ProcessingLog.objects.create(
                document=document,
                level='info',
                message=f'Successfully processed page {result_data.get("page_number", 1)}',
                details={
                    'confidence': result_data.get('confidence', 0),
                    'word_count': result_data.get('word_count', 0),
                    'content_type': content_type
                }
            )
        
        # Calculate total processing time
        processing_time = time.time() - start_time
        
        # Mark document as completed
        document.mark_completed(processing_time)
        
        # Final log
        ProcessingLog.objects.create(
            document=document,
            level='info',
            message='OCR processing completed successfully',
            details={
                'processing_time': processing_time,
                'total_pages': len(results),
                'task_id': self.request.id
            }
        )
        
        logger.info(f"Successfully processed document {document_id}")
        
        return {
            'success': True,
            'document_id': str(document_id),
            'processing_time': processing_time,
            'pages_processed': len(results)
        }
    
    except OCRDocument.DoesNotExist:
        error_msg = f"Document {document_id} not found"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    except Exception as exc:
        error_msg = f"Error processing document {document_id}: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        
        try:
            document = OCRDocument.objects.get(id=document_id)
            document.mark_failed(str(exc))
            
            ProcessingLog.objects.create(
                document=document,
                level='error',
                message='OCR processing failed',
                details={
                    'error': str(exc),
                    'task_id': self.request.id
                }
            )
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
        
        # Retry task if retries available
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {'success': False, 'error': error_msg}


@shared_task
def cleanup_old_documents(days: int = 30):
    """
    Celery task to cleanup old processed documents.
    
    Args:
        days: Delete documents older than this many days
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Find old documents
    old_documents = OCRDocument.objects.filter(
        uploaded_at__lt=cutoff_date,
        status='completed'
    )
    
    count = old_documents.count()
    
    # Delete files and records
    for document in old_documents:
        try:
            if os.path.exists(document.file.path):
                os.remove(document.file.path)
            document.delete()
        except Exception as e:
            logger.error(f"Error deleting document {document.id}: {str(e)}")
    
    logger.info(f"Cleaned up {count} old documents")
    return {'deleted': count}


@shared_task
def generate_statistics():
    """
    Generate statistics about OCR processing.
    """
    from django.db.models import Count, Avg, Sum
    
    stats = {
        'total_documents': OCRDocument.objects.count(),
        'by_status': dict(
            OCRDocument.objects.values('status').annotate(count=Count('id'))
            .values_list('status', 'count')
        ),
        'avg_processing_time': OCRDocument.objects.filter(
            processing_time__isnull=False
        ).aggregate(Avg('processing_time'))['processing_time__avg'],
        'total_results': OCRResult.objects.count(),
        'by_content_type': dict(
            OCRResult.objects.values('content_type').annotate(count=Count('id'))
            .values_list('content_type', 'count')
        ),
        'code_blocks': CodeBlock.objects.count(),
        'by_language': dict(
            CodeBlock.objects.values('detected_language').annotate(count=Count('id'))
            .values_list('detected_language', 'count')
        )
    }
    
    logger.info(f"Generated statistics: {stats}")
    return stats
