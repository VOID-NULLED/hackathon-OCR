"""
Serializers for OCR API.
"""
from rest_framework import serializers
from .models import OCRDocument, OCRResult, CodeBlock, ProcessingLog


class CodeBlockSerializer(serializers.ModelSerializer):
    """Serializer for CodeBlock model."""
    
    class Meta:
        model = CodeBlock
        fields = [
            'id', 'code_content', 'detected_language', 'confidence',
            'line_start', 'line_end', 'is_valid_syntax', 'syntax_errors',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OCRResultSerializer(serializers.ModelSerializer):
    """Serializer for OCRResult model."""
    code_blocks = CodeBlockSerializer(many=True, read_only=True)
    
    class Meta:
        model = OCRResult
        fields = [
            'id', 'extracted_text', 'content_type', 'language',
            'confidence', 'page_number', 'word_count', 'line_count',
            'character_count', 'code_blocks', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'word_count', 'line_count', 'character_count',
            'created_at', 'updated_at'
        ]


class ProcessingLogSerializer(serializers.ModelSerializer):
    """Serializer for ProcessingLog model."""
    
    class Meta:
        model = ProcessingLog
        fields = ['id', 'level', 'message', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']


class OCRDocumentSerializer(serializers.ModelSerializer):
    """Serializer for OCRDocument model."""
    ocr_results = OCRResultSerializer(many=True, read_only=True)
    processing_logs = ProcessingLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = OCRDocument
        fields = [
            'id', 'file', 'filename', 'file_size', 'file_type',
            'status', 'uploaded_at', 'processed_at', 'processing_time',
            'error_message', 'ocr_results', 'processing_logs'
        ]
        read_only_fields = [
            'id', 'filename', 'file_size', 'file_type', 'status',
            'uploaded_at', 'processed_at', 'processing_time',
            'error_message'
        ]
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size
        if value.size > settings.OCR_MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of "
                f"{settings.OCR_MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Check file extension
        ext = value.name.split('.')[-1].lower()
        if ext not in settings.OCR_ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"File type '{ext}' not allowed. Allowed types: "
                f"{', '.join(settings.OCR_ALLOWED_EXTENSIONS)}"
            )
        
        return value


class OCRDocumentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for document list view."""
    result_count = serializers.SerializerMethodField()
    
    class Meta:
        model = OCRDocument
        fields = [
            'id', 'filename', 'file_size', 'file_type', 'status',
            'uploaded_at', 'processed_at', 'processing_time',
            'result_count'
        ]
        read_only_fields = fields
    
    def get_result_count(self, obj):
        """Get count of OCR results."""
        return obj.ocr_results.count()


class OCRUploadSerializer(serializers.Serializer):
    """Serializer for file upload."""
    file = serializers.FileField()
    language = serializers.CharField(
        max_length=50,
        default='eng',
        help_text="OCR language code (e.g., 'eng' for English)"
    )
    
    def validate_file(self, value):
        """Validate uploaded file."""
        from django.conf import settings
        
        # Check file size
        if value.size > settings.OCR_MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of "
                f"{settings.OCR_MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Check file extension
        ext = value.name.split('.')[-1].lower()
        if ext not in settings.OCR_ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"File type '{ext}' not allowed. Allowed types: "
                f"{', '.join(settings.OCR_ALLOWED_EXTENSIONS)}"
            )
        
        return value
    
    def validate_language(self, value):
        """Validate language code."""
        from django.conf import settings
        
        if value not in settings.OCR_LANGUAGES:
            raise serializers.ValidationError(
                f"Language '{value}' not supported. Supported languages: "
                f"{', '.join(settings.OCR_LANGUAGES)}"
            )
        
        return value
