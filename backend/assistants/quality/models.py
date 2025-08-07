from django.db import models
from django.contrib.auth.models import User
from meiyume_core.models import BaseUpload
import uuid


class QualityChatSession(models.Model):
    """Model for storing quality chat sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quality_chat_sessions')
    session_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'quality_chat_sessions'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Quality Chat Session {self.session_id} - {self.user.username}"


class QualityChatMessage(models.Model):
    """Model for storing individual chat messages"""
    
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('assistant', 'Assistant Response'),
        ('system', 'System Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(QualityChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='user')
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(null=True, blank=True)  # Response time in seconds
    tokens_used = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'quality_chat_messages'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type} message in session {self.session.session_id}"


class QualityChatResponse(models.Model):
    """Model for storing detailed response information"""
    
    RESPONSE_STATUS = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('partial', 'Partial Success'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.OneToOneField(QualityChatMessage, on_delete=models.CASCADE, related_name='response_details')
    status = models.CharField(max_length=20, choices=RESPONSE_STATUS, default='success')
    n8n_webhook_url = models.URLField()
    n8n_response = models.JSONField(default=dict, blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quality_chat_responses'
    
    def __str__(self):
        return f"Response for message {self.message.id} - {self.status}"


class QualityKnowledgeBase(models.Model):
    """Model for storing quality control knowledge base entries"""
    
    ENTRY_TYPES = [
        ('standard', 'Quality Standard'),
        ('procedure', 'Testing Procedure'),
        ('guideline', 'Best Practice Guideline'),
        ('regulation', 'Regulation/Compliance'),
        ('faq', 'Frequently Asked Question'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    content = models.TextField()
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='guideline')
    tags = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=500, blank=True, null=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quality_knowledge_base'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} ({self.entry_type})"


class QualityChatAnalytics(models.Model):
    """Model for storing chat analytics and metrics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(QualityChatSession, on_delete=models.CASCADE, related_name='analytics')
    total_messages = models.IntegerField(default=0)
    user_messages = models.IntegerField(default=0)
    assistant_messages = models.IntegerField(default=0)
    total_tokens_used = models.IntegerField(default=0)
    average_response_time = models.FloatField(null=True, blank=True)
    topics_discussed = models.JSONField(default=list, blank=True)
    session_duration = models.FloatField(null=True, blank=True)  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quality_chat_analytics'
    
    def __str__(self):
        return f"Analytics for session {self.session.session_id}" 