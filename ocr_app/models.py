"""
Models for OCR application.
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import uuid


class OCRDocument(models.Model):
    """
    Model to store uploaded documents and their OCR processing status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(
            allowed_extensions=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf']
        )]
    )
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['-uploaded_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.filename} - {self.status}"
    
    def mark_processing(self):
        """Mark document as being processed."""
        self.status = 'processing'
        self.save(update_fields=['status'])
    
    def mark_completed(self, processing_time=None):
        """Mark document as successfully processed."""
        self.status = 'completed'
        self.processed_at = timezone.now()
        if processing_time:
            self.processing_time = processing_time
        self.save(update_fields=['status', 'processed_at', 'processing_time'])
    
    def mark_failed(self, error_message):
        """Mark document as failed with error message."""
        self.status = 'failed'
        self.processed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'processed_at', 'error_message'])


class OCRResult(models.Model):
    """
    Model to store OCR extracted text results.
    """
    CONTENT_TYPE_CHOICES = [
        ('text', 'Plain Text'),
        ('code', 'Code'),
        ('mixed', 'Mixed Content'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        OCRDocument,
        on_delete=models.CASCADE,
        related_name='ocr_results'
    )
    
    # OCR Results
    extracted_text = models.TextField(help_text="Full extracted text from OCR")
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='text'
    )
    
    # Metadata
    language = models.CharField(max_length=50, default='eng')
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="OCR confidence score (0-100)"
    )
    page_number = models.IntegerField(default=1, help_text="Page number for multi-page documents")
    
    # Analysis
    word_count = models.IntegerField(default=0)
    line_count = models.IntegerField(default=0)
    character_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['document', 'page_number']
        indexes = [
            models.Index(fields=['document', 'page_number']),
            models.Index(fields=['content_type']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"OCR Result for {self.document.filename} (Page {self.page_number})"
    
    def save(self, *args, **kwargs):
        """Calculate statistics on save."""
        if self.extracted_text:
            self.character_count = len(self.extracted_text)
            self.word_count = len(self.extracted_text.split())
            self.line_count = len(self.extracted_text.split('\n'))
        super().save(*args, **kwargs)


class CodeBlock(models.Model):
    """
    Model to store identified code blocks from OCR results.
    """
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('csharp', 'C#'),
        ('ruby', 'Ruby'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('sql', 'SQL'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('shell', 'Shell'),
        ('unknown', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ocr_result = models.ForeignKey(
        OCRResult,
        on_delete=models.CASCADE,
        related_name='code_blocks'
    )
    
    code_content = models.TextField(help_text="Extracted code content")
    detected_language = models.CharField(
        max_length=50,
        choices=LANGUAGE_CHOICES,
        default='unknown'
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Language detection confidence"
    )
    
    line_start = models.IntegerField(help_text="Starting line number in original text")
    line_end = models.IntegerField(help_text="Ending line number in original text")
    
    # Analysis
    is_valid_syntax = models.BooleanField(default=False)
    syntax_errors = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['ocr_result', 'line_start']
        indexes = [
            models.Index(fields=['ocr_result']),
            models.Index(fields=['detected_language']),
        ]
    
    def __str__(self):
        return f"{self.detected_language} code block from {self.ocr_result.document.filename}"


class ProcessingLog(models.Model):
    """
    Model to log processing events for debugging and monitoring.
    """
    LOG_LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        OCRDocument,
        on_delete=models.CASCADE,
        related_name='processing_logs'
    )
    
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='info')
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', '-created_at']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.document.filename} - {self.message[:50]}"
