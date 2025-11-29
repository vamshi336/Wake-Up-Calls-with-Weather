"""
URL configuration for wakeupcalls_project project.

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
from django.views.generic import TemplateView
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def api_root(request):
    """API root endpoint with available endpoints."""
    return Response({
        'message': 'Welcome to Vamshi Wake-up Calls API',
        'version': '1.0',
        'endpoints': {
            'accounts': '/api/accounts/',
            'wakeup_calls': '/api/wakeup-calls/',
            'notifications': '/api/notifications/',
            'admin': '/admin/',
        }
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Web interface
    path('', include('web.urls')),
    
    # API endpoints
    path('api/', api_root, name='api_root'),
    path('api/docs/', TemplateView.as_view(template_name='api_docs.html'), name='api_docs'),
    path('api/accounts/', include('accounts.urls')),
    path('api/wakeup-calls/', include('wakeup_calls.urls')),
    path('api/notifications/', include('notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
