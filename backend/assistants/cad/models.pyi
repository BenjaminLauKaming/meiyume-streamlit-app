"""
Type stubs for CAD models to help Pyright understand Django model attributes
"""

from typing import Any, Optional
from django.db import models
from django.db.models.manager import Manager

class CADUploadManager(Manager):
    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> Any: ...
    def create(self, **kwargs) -> Any: ...

class CADAnalysisOptionsManager(Manager):
    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> Any: ...
    def create(self, **kwargs) -> Any: ...

class CADAnalysisResultManager(Manager):
    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> Any: ...
    def get_or_create(self, **kwargs) -> Any: ...

class CADUpload(models.Model):
    objects: CADUploadManager
    DoesNotExist: type[Exception]
    
    id: Any
    user: Any
    original_filename: str
    file_path: Any
    file_size: int
    file_hash: str
    project_name: Optional[str]
    notes: Optional[str]
    status: str
    processing_started_at: Optional[Any]
    processing_completed_at: Optional[Any]
    progress_percentage: int
    n8n_execution_id: Optional[str]
    webhook_response: Optional[dict]
    error_message: Optional[str]
    retry_count: int
    created_at: Any
    updated_at: Any
    
    def save(self) -> None: ...

class CADAnalysisOptions(models.Model):
    objects: CADAnalysisOptionsManager
    
    upload: CADUpload
    ai_model_version: str
    confidence_threshold: float
    max_analysis_time: int
    custom_prompt_additions: Optional[str]
    extract_dimensions: bool
    extract_tolerances: bool
    analyze_part_relationships: bool
    extract_material_specifications: bool
    detect_assembly_components: bool
    created_at: Any
    updated_at: Any
    
    def save(self) -> None: ...

class CADAnalysisResult(models.Model):
    objects: CADAnalysisResultManager
    
    upload: CADUpload
    result_type: str
    raw_data: dict
    processed_data: Optional[dict]
    confidence_score: Optional[float]
    extraction_method: str
    processing_time_seconds: Optional[float]
    csv_file_path: Optional[Any]
    report_file_path: Optional[Any]
    created_at: Any
    updated_at: Any
    
    def save(self) -> None: ... 