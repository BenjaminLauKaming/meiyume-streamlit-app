"""
Type stubs for meiyume_core models to help Pyright understand Django model attributes
"""

from typing import Any, Optional, Dict
from django.db import models
from django.db.models.manager import Manager
from django.contrib.auth.models import User

class UserPreferencesManager(Manager):
    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> Any: ...
    def get_or_create(self, **kwargs) -> Any: ...

class ProcessingLogManager(Manager):
    def filter(self, **kwargs) -> Any: ...
    def get(self, **kwargs) -> Any: ...

class UserPreferences(models.Model):
    objects: UserPreferencesManager
    
    user: User
    email_notifications: bool
    processing_complete_notifications: bool
    azure_ad_object_id: Optional[str]
    department: Optional[str]
    job_title: Optional[str]
    assistant_preferences: Dict[str, Any]
    created_at: Any
    updated_at: Any
    
    def save(self) -> None: ...
    def get_assistant_preference(self, assistant_name: str, key: str, default: Any = None) -> Any: ...
    def set_assistant_preference(self, assistant_name: str, key: str, value: Any) -> None: ...

class ProcessingLog(models.Model):
    objects: ProcessingLogManager
    
    content_type: Any
    object_id: Any
    level: str
    message: str
    step: str
    execution_time_ms: Optional[int]
    metadata: Optional[Dict[str, Any]]
    created_at: Any
    
    def save(self) -> None: ... 