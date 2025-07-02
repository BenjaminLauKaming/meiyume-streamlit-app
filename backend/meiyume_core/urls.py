"""
URL patterns for meiyume_core app - shared functionality across all assistants
"""

from django.urls import path
from . import views

app_name = 'meiyume_core'

urlpatterns = [
    # User preferences
    path('preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
    
    # Dashboard and statistics
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # Health check
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    
    # Processing logs
    path('logs/', views.ProcessingLogView.as_view(), name='processing-logs'),
] 