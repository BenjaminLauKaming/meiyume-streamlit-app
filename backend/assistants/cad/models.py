from django.db import models
from meiyume_core.models import BaseUpload, BaseAnalysisOptions, BaseAnalysisResult

class CADUpload(BaseUpload):
    """Model to track CAD file uploads and their metadata"""
    
    # CAD-specific fields
    drawing_number = models.CharField(max_length=100, blank=True, null=True)
    revision = models.CharField(max_length=50, blank=True, null=True)
    
    # Override file_path to use CAD-specific upload path
    file_path = models.FileField(upload_to='cad_files/%Y/%m/%d/')
    
    class Meta:
        verbose_name = "CAD Upload"
        verbose_name_plural = "CAD Uploads"

class CADAnalysisOptions(BaseAnalysisOptions):
    """Model to store CAD analysis configuration"""
    
    upload = models.OneToOneField(CADUpload, on_delete=models.CASCADE, related_name='analysis_options')
    
    # CAD-specific analysis settings
    extract_dimensions = models.BooleanField(default=True)
    extract_tolerances = models.BooleanField(default=True)
    analyze_part_relationships = models.BooleanField(default=True)
    extract_material_specifications = models.BooleanField(default=False)
    detect_assembly_components = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "CAD Analysis Options"
        verbose_name_plural = "CAD Analysis Options"

class CADAnalysisResult(BaseAnalysisResult):
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
    
    class Meta:
        unique_together = ['upload', 'result_type']
        verbose_name = "CAD Analysis Result"
        verbose_name_plural = "CAD Analysis Results" 