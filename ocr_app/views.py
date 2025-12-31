"""
API views for OCR application.
"""
import os
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings

from .models import OCRDocument, OCRResult, CodeBlock
from .serializers import (
    OCRDocumentSerializer,
    OCRDocumentListSerializer,
    OCRResultSerializer,
    CodeBlockSerializer,
    OCRUploadSerializer
)
from .tasks import process_ocr_task

logger = logging.getLogger(__name__)


class OCRDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing OCR documents.
    
    Endpoints:
    - GET /api/documents/ - List all documents
    - POST /api/documents/ - Upload a new document
    - GET /api/documents/{id}/ - Retrieve document details
    - DELETE /api/documents/{id}/ - Delete a document
    - POST /api/documents/upload/ - Upload and process document
    - POST /api/documents/{id}/reprocess/ - Reprocess a document
    """
    queryset = OCRDocument.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return OCRDocumentListSerializer
        elif self.action == 'upload':
            return OCRUploadSerializer
        return OCRDocumentSerializer
    
    def list(self, request, *args, **kwargs):
        """List all documents with optional filtering."""
        queryset = self.get_queryset()
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Order by
        order_by = request.query_params.get('order_by', '-uploaded_at')
        queryset = queryset.order_by(order_by)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Handle document upload (without processing)."""
        return Response(
            {
                "error": "Use /api/documents/upload/ endpoint to upload and process documents"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload and process a document with OCR.
        
        Request:
            - file: The document file (image or PDF)
            - language: OCR language code (optional, default: 'eng')
        
        Response:
            - document: Created document object
            - task_id: Celery task ID for tracking
        """
        serializer = OCRUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = serializer.validated_data['file']
        language = serializer.validated_data.get('language', 'eng')
        
        # Create document record
        document = OCRDocument.objects.create(
            file=uploaded_file,
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=uploaded_file.content_type,
            status='pending'
        )
        
        logger.info(f"Document uploaded: {document.id} - {document.filename}")
        
        # Queue OCR processing task
        task = process_ocr_task.delay(str(document.id), language)
        
        return Response(
            {
                'document': OCRDocumentSerializer(document).data,
                'task_id': task.id,
                'message': 'Document uploaded successfully. Processing started.'
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """
        Reprocess an existing document.
        
        Request:
            - language: OCR language code (optional)
        """
        document = self.get_object()
        language = request.data.get('language', 'eng')
        
        # Check if document exists
        if not os.path.exists(document.file.path):
            return Response(
                {'error': 'Document file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Reset document status
        document.status = 'pending'
        document.error_message = None
        document.save()
        
        # Clear old results
        document.ocr_results.all().delete()
        
        # Queue reprocessing task
        task = process_ocr_task.delay(str(document.id), language)
        
        return Response(
            {
                'document': OCRDocumentSerializer(document).data,
                'task_id': task.id,
                'message': 'Document reprocessing started.'
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get all OCR results for a document."""
        document = self.get_object()
        results = document.ocr_results.all()
        serializer = OCRResultSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def code_blocks(self, request, pk=None):
        """Get all detected code blocks for a document."""
        document = self.get_object()
        code_blocks = CodeBlock.objects.filter(
            ocr_result__document=document
        )
        serializer = CodeBlockSerializer(code_blocks, many=True)
        return Response(serializer.data)


class OCRResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing OCR results.
    
    Endpoints:
    - GET /api/results/ - List all results
    - GET /api/results/{id}/ - Retrieve result details
    """
    queryset = OCRResult.objects.all()
    serializer_class = OCRResultSerializer
    
    def get_queryset(self):
        """Filter results based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by document
        document_id = self.request.query_params.get('document')
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        return queryset


class CodeBlockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing detected code blocks.
    
    Endpoints:
    - GET /api/code-blocks/ - List all code blocks
    - GET /api/code-blocks/{id}/ - Retrieve code block details
    """
    queryset = CodeBlock.objects.all()
    serializer_class = CodeBlockSerializer
    
    def get_queryset(self):
        """Filter code blocks based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(detected_language=language)
        
        # Filter by document
        document_id = self.request.query_params.get('document')
        if document_id:
            queryset = queryset.filter(ocr_result__document_id=document_id)
        
        return queryset
