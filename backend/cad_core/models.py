from django.db import models
from django.contrib.auth.models import User
import uuid
import os

class CADUpload(models.Model):
    """Model to track CAD file uploads and their metadata"""
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cad_uploads')
    
    # File information
    original_filename = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='cad_files/%Y/%m/%d/')
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_hash = models.CharField(max_length=64, help_text="SHA256 hash of the file")
    
    # Upload metadata
    project_name = models.CharField(max_length=200, blank=True, null=True)
    drawing_number = models.CharField(max_length=100, blank=True, null=True)
    revision = models.CharField(max_length=50, blank=True, null=True)
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
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} - {self.user.username} - {self.status}"
    
    @property
    def is_processing(self):
        return self.status in ['uploaded', 'processing']
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'

class AnalysisOptions(models.Model):
    """Model to store analysis configuration for each upload"""
    
    upload = models.OneToOneField(CADUpload, on_delete=models.CASCADE, related_name='analysis_options')
    
    # Analysis settings
    extract_dimensions = models.BooleanField(default=True)
    extract_tolerances = models.BooleanField(default=True)
    analyze_part_relationships = models.BooleanField(default=True)
    extract_material_specifications = models.BooleanField(default=False)
    detect_assembly_components = models.BooleanField(default=False)
    
    # AI model settings
    ai_model_version = models.CharField(max_length=50, default='gemini-pro')
    confidence_threshold = models.FloatField(default=0.8)
    max_analysis_time = models.PositiveIntegerField(default=300)  # seconds
    
    # Custom prompts
    custom_prompt_additions = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analysis Options for {self.upload.original_filename}"

class AnalysisResult(models.Model):
    """Model to store the results of CAD analysis"""
    
    RESULT_TYPE_CHOICES = [
        ('dimensions', 'Dimensions'),
        ('tolerances', 'Tolerances'),
        ('relationships', 'Part Relationships'),
        ('materials', 'Materials'),
        ('assembly', 'Assembly Components'),
    ]
    
    upload = models.ForeignKey(CADUpload, on_delete=models.CASCADE, related_name='results')
    result_type = models.CharField(max_length=20, choices=RESULT_TYPE_CHOICES)
    
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
        unique_together = ['upload', 'result_type']
        indexes = [
            models.Index(fields=['upload', 'result_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.result_type} results for {self.upload.original_filename}"

class ProcessingLog(models.Model):
    """Model to track detailed processing logs"""
    
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug'),
    ]
    
    upload = models.ForeignKey(CADUpload, on_delete=models.CASCADE, related_name='processing_logs')
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
            models.Index(fields=['upload', 'level']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.step}: {self.message[:50]}..."

class UserPreferences(models.Model):
    """Model to store user preferences and settings"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cad_preferences')
    
    # Analysis preferences
    default_extract_dimensions = models.BooleanField(default=True)
    default_extract_tolerances = models.BooleanField(default=True)
    default_analyze_relationships = models.BooleanField(default=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    processing_complete_notifications = models.BooleanField(default=True)
    
    # Azure AD information
    azure_ad_object_id = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
