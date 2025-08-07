from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    QualityChatSession,
    QualityChatMessage,
    QualityChatResponse,
    QualityKnowledgeBase,
    QualityChatAnalytics
)


@admin.register(QualityChatSession)
class QualityChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'title', 'message_count', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['session_id', 'title', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(QualityChatMessage)
class QualityChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'message_type', 'content_preview', 'timestamp', 'response_time', 'model_used']
    list_filter = ['message_type', 'timestamp', 'model_used']
    search_fields = ['content', 'session__session_id', 'session__user__username']
    readonly_fields = ['id', 'timestamp']
    ordering = ['-timestamp']
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__user')


@admin.register(QualityChatResponse)
class QualityChatResponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'status', 'processing_time', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['message__content', 'error_message']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message', 'message__session')


@admin.register(QualityKnowledgeBase)
class QualityKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'entry_type', 'source', 'version', 'is_active', 'created_at']
    list_filter = ['entry_type', 'is_active', 'created_at', 'updated_at']
    search_fields = ['title', 'content', 'source', 'tags']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'entry_type', 'is_active')
        }),
        ('Metadata', {
            'fields': ('source', 'version', 'tags'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(QualityChatAnalytics)
class QualityChatAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['session', 'total_messages', 'user_messages', 'assistant_messages', 'total_tokens_used', 'average_response_time']
    list_filter = ['created_at']
    search_fields = ['session__session_id', 'session__user__username']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__user')


# Custom admin site configuration
admin.site.site_header = "Meiyume AI Assistant - Quality Control"
admin.site.site_title = "Quality Control Admin"
admin.site.index_title = "Quality Control Administration" 