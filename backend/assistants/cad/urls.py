"""
URL patterns for CAD assistant
"""

from django.urls import path
from . import views

app_name = 'cad'

urlpatterns = [
    # File uploads
    path('uploads/', views.CADUploadListCreateView.as_view(), name='upload-list-create'),
    path('uploads/<uuid:pk>/', views.CADUploadDetailView.as_view(), name='upload-detail'),
    
    # Analysis results
    path('results/', views.CADAnalysisResultListView.as_view(), name='result-list'),
    path('results/<uuid:upload_id>/', views.CADAnalysisResultDetailView.as_view(), name='result-detail'),
    
    # Analysis options
    path('options/<uuid:upload_id>/', views.CADAnalysisOptionsView.as_view(), name='analysis-options'),
    
    # Webhook callback
    path('webhook/n8n-callback/', views.N8nWebhookCallbackView.as_view(), name='n8n-callback'),
] 