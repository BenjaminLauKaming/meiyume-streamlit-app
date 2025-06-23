from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CADUpload, AnalysisOptions, AnalysisResult, ProcessingLog, UserPreferences

@admin.register(CADUpload)
class CADUploadAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'user', 'status', 'progress_percentage', 
        'project_name', 'drawing_number', 'file_size_mb', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['original_filename', 'project_name', 'drawing_number', 'user__username']
    readonly_fields = [
        'id', 'file_hash', 'file_size', 'processing_started_at', 
        'processing_completed_at', 'n8n_execution_id', 'webhook_response',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('File Information', {
            'fields': ('id', 'original_filename', 'file_path', 'file_size', 'file_hash')
        }),
        ('Project Details', {
            'fields': ('project_name', 'drawing_number', 'revision', 'notes')
        }),
        ('Processing Status', {
            'fields': ('status', 'progress_percentage', 'processing_started_at', 
                      'processing_completed_at', 'error_message', 'retry_count')
        }),
        ('n8n Integration', {
            'fields': ('n8n_execution_id', 'webhook_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def file_size_mb(self, obj):
        """Display file size in MB"""
        return f"{obj.file_size / (1024*1024):.2f} MB"
    file_size_mb.short_description = "File Size"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(AnalysisOptions)
class AnalysisOptionsAdmin(admin.ModelAdmin):
    list_display = [
        'upload', 'extract_dimensions', 'extract_tolerances', 
        'analyze_part_relationships', 'ai_model_version', 'confidence_threshold'
    ]
    list_filter = ['extract_dimensions', 'extract_tolerances', 'analyze_part_relationships', 'ai_model_version']
    search_fields = ['upload__original_filename', 'upload__user__username']
    
    fieldsets = (
        ('Analysis Settings', {
            'fields': ('extract_dimensions', 'extract_tolerances', 'analyze_part_relationships',
                      'extract_material_specifications', 'detect_assembly_components')
        }),
        ('AI Configuration', {
            'fields': ('ai_model_version', 'confidence_threshold', 'max_analysis_time')
        }),
        ('Custom Prompts', {
            'fields': ('custom_prompt_additions',),
            'classes': ('collapse',)
        })
    )

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = [
        'upload', 'result_type', 'confidence_score', 'extraction_method', 
        'processing_time_seconds', 'has_csv', 'has_report', 'created_at'
    ]
    list_filter = ['result_type', 'extraction_method', 'created_at']
    search_fields = ['upload__original_filename', 'upload__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Result Information', {
            'fields': ('upload', 'result_type', 'confidence_score', 'extraction_method', 'processing_time_seconds')
        }),
        ('Data', {
            'fields': ('raw_data', 'processed_data'),
            'classes': ('collapse',)
        }),
        ('Generated Files', {
            'fields': ('csv_file_path', 'report_file_path')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_csv(self, obj):
        """Check if CSV file exists"""
        return bool(obj.csv_file_path)
    has_csv.boolean = True
    has_csv.short_description = "CSV File"
    
    def has_report(self, obj):
        """Check if report file exists"""
        return bool(obj.report_file_path)
    has_report.boolean = True
    has_report.short_description = "Report File"

@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['upload', 'level', 'step', 'message_short', 'execution_time_ms', 'created_at']
    list_filter = ['level', 'step', 'created_at']
    search_fields = ['upload__original_filename', 'message', 'step']
    readonly_fields = ['created_at']
    
    def message_short(self, obj):
        """Display truncated message"""
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_short.short_description = "Message"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('upload', 'upload__user')

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'default_extract_dimensions', 'default_extract_tolerances',
        'email_notifications', 'department', 'job_title'
    ]
    list_filter = ['default_extract_dimensions', 'default_extract_tolerances', 'email_notifications']
    search_fields = ['user__username', 'user__email', 'department', 'job_title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Default Analysis Preferences', {
            'fields': ('default_extract_dimensions', 'default_extract_tolerances', 'default_analyze_relationships')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'processing_complete_notifications')
        }),
        ('Azure AD Information', {
            'fields': ('azure_ad_object_id', 'department', 'job_title'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Customize admin site headers
admin.site.site_header = "AI CAD Analyzer Administration"
admin.site.site_title = "CAD Analyzer Admin"
admin.site.index_title = "Welcome to AI CAD Analyzer Administration"
