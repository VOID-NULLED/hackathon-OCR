from django.contrib import admin
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
