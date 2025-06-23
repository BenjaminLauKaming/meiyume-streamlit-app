from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'uploads', views.CADUploadViewSet, basename='cadupload')
router.register(r'preferences', views.UserPreferencesViewSet, basename='userpreferences')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Standalone API endpoints
    path('results/<uuid:task_id>/', views.get_processing_status, name='processing-status'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('health/', views.health_check, name='health-check'),
    
    # n8n webhook callback (no authentication required)
    path('webhook/n8n-callback/', views.n8n_webhook_callback, name='n8n-webhook-callback'),
] 