from django.contrib import admin
from django.utils.html import format_html
from .models import UserPreferences, ProcessingLog

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_notifications', 'processing_complete_notifications',
        'department', 'job_title'
    ]
    list_filter = ['email_notifications', 'processing_complete_notifications']
    search_fields = ['user__username', 'user__email', 'department', 'job_title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'processing_complete_notifications')
        }),
        ('Azure AD Information', {
            'fields': ('azure_ad_object_id', 'department', 'job_title'),
            'classes': ('collapse',)
        }),
        ('Assistant Preferences', {
            'fields': ('assistant_preferences',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'object_id', 'level', 'step', 'message_short', 'execution_time_ms', 'created_at']
    list_filter = ['level', 'step', 'created_at', 'content_type']
    search_fields = ['message', 'step']
    readonly_fields = ['created_at']
    
    def message_short(self, obj):
        """Display truncated message"""
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_short.short_description = "Message"

# Customize admin site headers
admin.site.site_header = "Meiyume AI Assistant Administration"
admin.site.site_title = "Meiyume AI Assistant Admin"
admin.site.index_title = "Welcome to Meiyume AI Assistant Administration" 