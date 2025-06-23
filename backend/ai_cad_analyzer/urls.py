"""
URL configuration for ai_cad_analyzer project.

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

def api_root(request):
    """Simple API root endpoint"""
    return HttpResponse("""
    <h1>AI CAD Analyzer API</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><a href="/api/">API Root</a></li>
        <li><a href="/api/uploads/">CAD Uploads</a></li>
        <li><a href="/api/results/">Processing Results</a></li>
        <li><a href="/api/preferences/">User Preferences</a></li>
        <li><a href="/api/dashboard/stats/">Dashboard Stats</a></li>
        <li><a href="/api/health/">Health Check</a></li>
        <li><a href="/admin/">Admin Panel</a></li>
    </ul>
    """, content_type="text/html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),
    path('api/', include('cad_core.urls')),
    
    # API authentication endpoints
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
