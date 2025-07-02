from django.db import models
from django.contrib.auth.models import User
import uuid
import os

class BaseUpload(models.Model):
    """Base model for all file uploads across different assistants"""
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_uploads')
    
    # File information
    original_filename = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_hash = models.CharField(max_length=64, help_text="SHA256 hash of the file")
    
    # Upload metadata
    project_name = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Processing information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    
    # n8n webhook information
    n8n_execution_id = models.CharField(max_length=100, blank=True, null=True)
    webhook_response = models.JSONField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} - {self.user.username if self.user else 'Unknown'} - {self.status}"
    
    @property
    def is_processing(self):
        return self.status in ['uploaded', 'processing']
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'

class BaseAnalysisOptions(models.Model):
    """Base model for analysis configuration across different assistants"""
    
    # AI model settings
    ai_model_version = models.CharField(max_length=50, default='gemini-pro')
    confidence_threshold = models.FloatField(default=0.8)
    max_analysis_time = models.PositiveIntegerField(default=300)  # seconds
    
    # Custom prompts
    custom_prompt_additions = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return f"Analysis Options for {self.upload.original_filename}"

class BaseAnalysisResult(models.Model):
    """Base model for analysis results across different assistants"""
    
    # Result data
    raw_data = models.JSONField(help_text="Raw JSON data from AI analysis")
    processed_data = models.JSONField(null=True, blank=True, help_text="Processed/cleaned data")
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Metadata
    extraction_method = models.CharField(max_length=50, default='gemini-ai')
    processing_time_seconds = models.FloatField(null=True, blank=True)
    
    # Generated files
    csv_file_path = models.FileField(upload_to='results/csv/%Y/%m/%d/', null=True, blank=True)
    report_file_path = models.FileField(upload_to='results/reports/%Y/%m/%d/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Analysis results for {self.upload.original_filename}"

class ProcessingLog(models.Model):
    """Model to track detailed processing logs across all assistants"""
    
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]
    
    # Generic foreign key to any upload model
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.UUIDField()
    
    level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES)
    message = models.TextField()
    
    # Context information
    step = models.CharField(max_length=100, help_text="Processing step (e.g., 'file_upload', 'ai_analysis', 'result_generation')")
    execution_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'level']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.step}: {self.message[:50]}..."

class UserPreferences(models.Model):
    """Model to store user preferences and settings across all assistants"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meiyume_preferences')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    processing_complete_notifications = models.BooleanField(default=True)
    
    # Azure AD information
    azure_ad_object_id = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    # Assistant-specific preferences (stored as JSON)
    assistant_preferences = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def get_assistant_preference(self, assistant_name, key, default=None):
        """Get a specific preference for an assistant"""
        return self.assistant_preferences.get(assistant_name, {}).get(key, default)
    
    def set_assistant_preference(self, assistant_name, key, value):
        """Set a specific preference for an assistant"""
        if assistant_name not in self.assistant_preferences:
            self.assistant_preferences[assistant_name] = {}
        self.assistant_preferences[assistant_name][key] = value
        self.save() 