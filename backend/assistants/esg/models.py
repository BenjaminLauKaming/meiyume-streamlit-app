"""
ESG Assistant Models

Models for handling ESG audit document uploads and analysis results.
"""

from django.db import models
from django.contrib.auth.models import User
from meiyume_core.models import BaseUpload, BaseAnalysisResult
import uuid


class ESGUpload(BaseUpload):
    """Model for ESG audit document uploads"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('water_bill', 'Water Bill'),
        ('fluid_usage', 'Fluid Usage Report'),
        ('chemical_inventory', 'Chemical Inventory Form'),
        ('utility_receipt', 'Utility Receipt'),
        ('other', 'Other Factory Document'),
    ]
    
    # ESG-specific fields
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPE_CHOICES, 
        default='other',
        help_text="Type of factory document"
    )
    
    # Audit metadata
    facility_name = models.CharField(max_length=200, blank=True, null=True)
    audit_period = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Q1 2024, Jan 2024")
    
    class Meta:
        db_table = 'esg_uploads'
        verbose_name = 'ESG Upload'
        verbose_name_plural = 'ESG Uploads'
    
    def __str__(self):
        return f"ESG Upload: {self.original_filename} ({self.document_type})"


class ESGAnalysisResult(BaseAnalysisResult):
    """Model for ESG analysis results"""
    
    upload = models.OneToOneField(
        ESGUpload, 
        on_delete=models.CASCADE, 
        related_name='analysis_result'
    )
    
    # ESG-specific analysis fields
    document_language = models.CharField(max_length=50, blank=True, null=True)
    total_volume_litres = models.FloatField(null=True, blank=True, help_text="Total volume in litres")
    
    # Additional extracted data
    currency = models.CharField(max_length=10, blank=True, null=True)
    total_cost = models.FloatField(null=True, blank=True)
    billing_period = models.CharField(max_length=100, blank=True, null=True)
    
    # Compliance flags
    compliance_status = models.CharField(
        max_length=20,
        choices=[
            ('compliant', 'Compliant'),
            ('non_compliant', 'Non-Compliant'),
            ('requires_review', 'Requires Review'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    
    class Meta:
        db_table = 'esg_analysis_results'
        verbose_name = 'ESG Analysis Result'
        verbose_name_plural = 'ESG Analysis Results'
    
    def __str__(self):
        return f"ESG Analysis: {self.upload.original_filename} - {self.document_language} - {self.total_volume_litres}L"


class ESGWebhookLog(models.Model):
    """Model to log webhook calls from n8n"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    upload = models.ForeignKey(ESGUpload, on_delete=models.CASCADE, related_name='webhook_logs', null=True, blank=True)
    
    # Webhook data
    n8n_execution_id = models.CharField(max_length=100, blank=True, null=True)
    webhook_payload = models.JSONField()
    
    # Processing status
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'esg_webhook_logs'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['n8n_execution_id']),
            models.Index(fields=['processed', 'received_at']),
        ]
    
    def __str__(self):
        return f"ESG Webhook: {self.n8n_execution_id} - {self.received_at}"