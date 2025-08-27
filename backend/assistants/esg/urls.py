"""
URL patterns for ESG assistant
"""

from django.urls import path
from . import views

app_name = 'esg'

urlpatterns = [
    # ESG uploads
    path('uploads/', views.ESGUploadListCreateView.as_view(), name='upload-list-create'),
    path('uploads/<uuid:pk>/', views.ESGUploadDetailView.as_view(), name='upload-detail'),
    path('uploads/<uuid:upload_id>/status/', views.ESGUploadStatusView.as_view(), name='upload-status'),
    
    # Analysis results
    path('results/<uuid:upload_id>/', views.ESGAnalysisResultView.as_view(), name='analysis-result'),
    
    # Dashboard and statistics
    path('dashboard/stats/', views.esg_dashboard_stats, name='dashboard-stats'),
    
    # Upload creation for n8n integration
    path('create-upload/', views.create_esg_upload_record, name='create-upload'),
    
    # Webhook endpoint for n8n
    path('webhook/', views.esg_webhook_receiver, name='webhook-receiver'),
]
