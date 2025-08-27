"""
URL configuration for meiyume_ai_assistant project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from datetime import datetime
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from simple_esg_webhook import simple_esg_webhook
from get_latest_esg import get_latest_esg_result
from simple_cad_webhook import simple_cad_webhook
from get_latest_cad import get_latest_cad_result

def test_webhook(request):
    """Test webhook endpoint to verify connectivity"""
    return HttpResponse("""
    <h1>Webhook Test</h1>
    <p>If you can see this, the webhook endpoint is accessible!</p>
    <p>Current time: """ + str(datetime.now()) + """</p>
    """, content_type="text/html")

def api_root(request):
    """Simple API root endpoint"""
    return HttpResponse("""
    <h1>Meiyume AI Assistant API</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><a href="/api/">API Root</a></li>
        <li><a href="/api/cad/">CAD Analysis</a></li>
        <li><a href="/api/esg/">ESG Analysis</a></li>
        <li><a href="/api/preferences/">User Preferences</a></li>
        <li><a href="/api/dashboard/stats/">Dashboard Stats</a></li>
        <li><a href="/api/health/">Health Check</a></li>
        <li><a href="/admin/">Admin Panel</a></li>
    </ul>
    """, content_type="text/html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),
    path('api/', include('meiyume_core.urls')),
    # path('api/cad/', include('assistants.cad.urls')),  # Temporarily disabled until DB is set up
    path('api/cad/webhook/', simple_cad_webhook, name='simple-cad-webhook'),
    path('api/cad/latest/', get_latest_cad_result, name='get-latest-cad'),
    path('api/test-webhook/', test_webhook, name='test-webhook'),
    # path('api/esg/', include('assistants.esg.urls')),  # Temporarily disabled until DB is set up
    path('api/esg/webhook/', simple_esg_webhook, name='simple-esg-webhook'),
    path('api/esg/latest/', get_latest_esg_result, name='get-latest-esg'),
    
    # JWT authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API authentication endpoints
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
