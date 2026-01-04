from django.contrib import admin
from . import models
from .models import OCRDocument, OCRResult, CodeBlock, ProcessingLog


@admin.register(OCRDocument)
class OCRDocumentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'status', 'file_size', 'uploaded_at', 'processed_at']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['filename', 'id']
    readonly_fields = ['id', 'uploaded_at', 'processed_at', 'processing_time']
    
    fieldsets = (
        ('Document Info', {
            'fields': ('id', 'file', 'filename', 'file_size', 'file_type')
        }),
        ('Processing Status', {
            'fields': ('status', 'uploaded_at', 'processed_at', 'processing_time')
        }),
        ('Errors', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


@admin.register(OCRResult)
class OCRResultAdmin(admin.ModelAdmin):
    list_display = ['document', 'content_type', 'page_number', 'word_count', 'confidence', 'created_at']
    list_filter = ['content_type', 'language', 'created_at']
    search_fields = ['document__filename', 'extracted_text']
    readonly_fields = ['id', 'created_at', 'updated_at', 'word_count', 'line_count', 'character_count']
    
    fieldsets = (
        ('Document Reference', {
            'fields': ('id', 'document', 'page_number')
        }),
        ('OCR Content', {
            'fields': ('extracted_text', 'content_type', 'language', 'confidence')
        }),
        ('Statistics', {
            'fields': ('word_count', 'line_count', 'character_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CodeBlock)
class CodeBlockAdmin(admin.ModelAdmin):
    list_display = ['ocr_result', 'detected_language', 'line_start', 'line_end', 'is_valid_syntax', 'created_at']
    list_filter = ['detected_language', 'is_valid_syntax', 'created_at']
    search_fields = ['code_content', 'ocr_result__document__filename']
    readonly_fields = ['id', 'created_at']


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['document', 'level', 'message_preview', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['document__filename', 'message']
    readonly_fields = ['id', 'created_at']
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'


@admin.register(models.FrameMetadata)
class FrameMetadataAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'camera', 'enhanced', 'blur_var', 'illum_mean', 'ocr_conf', 'raw_ocr_conf', 'accuracy_display']
    list_filter = ['camera', 'enhanced', 'timestamp']
    search_fields = ['camera', 'ocr', 'raw_ocr']
    readonly_fields = ['timestamp', 'accuracy_improvement']
    
    fieldsets = (
        ('Camera Info', {
            'fields': ('timestamp', 'camera')
        }),
        ('Quality Metrics', {
            'fields': ('blur_var', 'illum_mean', 'enhanced')
        }),
        ('Enhanced OCR Results', {
            'fields': ('ocr', 'ocr_conf', 'count')
        }),
        ('Raw OCR Results', {
            'fields': ('raw_ocr', 'raw_ocr_conf', 'raw_count')
        }),
        ('Analytics', {
            'fields': ('metrics', 'accuracy_improvement')
        }),
    )
    
    def accuracy_display(self, obj):
        """Display accuracy improvement percentage."""
        improvement = obj.accuracy_improvement()
        if improvement > 0:
            return f"+{improvement:.2f}%"
        return f"{improvement:.2f}%"
    accuracy_display.short_description = 'Accuracy Improvement'

