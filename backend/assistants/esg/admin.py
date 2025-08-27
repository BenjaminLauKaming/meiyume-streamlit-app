"""
ESG Assistant Admin

Admin interface for ESG audit document uploads and analysis results.
"""

from django.contrib import admin
from .models import ESGUpload, ESGAnalysisResult, ESGWebhookLog


@admin.register(ESGUpload)
class ESGUploadAdmin(admin.ModelAdmin):
    """Admin interface for ESG uploads"""
    
    list_display = [
        'original_filename', 'user', 'document_type', 'status', 
        'total_volume_display', 'created_at'
    ]
    list_filter = ['status', 'document_type', 'created_at']
    search_fields = ['original_filename', 'user__username', 'facility_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'file_hash']
    
    fieldsets = (
        ('File Information', {
            'fields': ('id', 'original_filename', 'file_path', 'file_size', 'file_hash')
        }),
        ('ESG Details', {
            'fields': ('document_type', 'facility_name', 'audit_period')
        }),
        ('Processing', {
            'fields': ('status', 'progress_percentage', 'n8n_execution_id', 'error_message')
        }),
        ('Metadata', {
            'fields': ('project_name', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processing_started_at', 'processing_completed_at')
        }),
    )
    
    def total_volume_display(self, obj):
        """Display total volume if analysis result exists"""
        if hasattr(obj, 'analysis_result') and obj.analysis_result.total_volume_litres:
            return f"{obj.analysis_result.total_volume_litres} L"
        return "-"
    total_volume_display.short_description = "Volume"


@admin.register(ESGAnalysisResult)
class ESGAnalysisResultAdmin(admin.ModelAdmin):
    """Admin interface for ESG analysis results"""
    
    list_display = [
        'upload', 'document_language', 'total_volume_litres', 
        'compliance_status', 'confidence_score', 'created_at'
    ]
    list_filter = ['document_language', 'compliance_status', 'created_at']
    search_fields = ['upload__original_filename', 'document_language']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Upload Information', {
            'fields': ('upload',)
        }),
        ('Analysis Results', {
            'fields': ('document_language', 'total_volume_litres', 'currency', 'total_cost', 'billing_period')
        }),
        ('Quality Metrics', {
            'fields': ('confidence_score', 'compliance_status', 'extraction_method', 'processing_time_seconds')
        }),
        ('Raw Data', {
            'fields': ('raw_data', 'processed_data'),
            'classes': ('collapse',)
        }),
        ('Files', {
            'fields': ('csv_file_path', 'report_file_path')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ESGWebhookLog)
class ESGWebhookLogAdmin(admin.ModelAdmin):
    """Admin interface for ESG webhook logs"""
    
    list_display = [
        'n8n_execution_id', 'upload', 'processed', 
        'received_at', 'error_message_short'
    ]
    list_filter = ['processed', 'received_at']
    search_fields = ['n8n_execution_id', 'upload__original_filename']
    readonly_fields = ['id', 'received_at', 'processed_at']
    
    fieldsets = (
        ('Webhook Information', {
            'fields': ('id', 'n8n_execution_id', 'upload')
        }),
        ('Processing Status', {
            'fields': ('processed', 'received_at', 'processed_at', 'error_message')
        }),
        ('Payload Data', {
            'fields': ('webhook_payload',),
            'classes': ('collapse',)
        }),
    )
    
    def error_message_short(self, obj):
        """Display shortened error message"""
        if obj.error_message:
            return obj.error_message[:50] + "..." if len(obj.error_message) > 50 else obj.error_message
        return "-"
    error_message_short.short_description = "Error"