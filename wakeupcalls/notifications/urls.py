"""
URL configuration for the notifications app.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification logs
    path('logs/', views.NotificationLogListView.as_view(), name='logs'),
    path('stats/', views.notification_stats, name='stats'),
    
    # Webhooks
    path('webhook/twilio/', views.twilio_webhook, name='twilio_webhook'),
]
