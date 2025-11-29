"""
API views for the notifications app.
"""

import logging
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import NotificationLog, TwilioWebhook
from .tasks import process_twilio_webhook

logger = logging.getLogger(__name__)


class NotificationLogListView(generics.ListAPIView):
    """API view for listing user's notification logs."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationLog.objects.filter(user=self.request.user).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Basic serialization for notification logs
        notifications = []
        for log in queryset[:50]:  # Limit to recent 50
            notifications.append({
                'id': log.id,
                'notification_type': log.notification_type,
                'recipient_phone': str(log.recipient_phone),
                'status': log.status,
                'sent_at': log.sent_at,
                'delivered_at': log.delivered_at,
                'twilio_status': log.twilio_status,
                'error_message': log.twilio_error_message,
                'is_demo': log.is_demo,
                'created_at': log.created_at,
            })
        
        return Response({
            'notifications': notifications,
            'count': len(notifications)
        })


@csrf_exempt
@require_POST
def twilio_webhook(request):
    """
    Webhook endpoint for Twilio status updates.
    This endpoint receives delivery status updates from Twilio.
    """
    try:
        # Log the incoming webhook
        logger.info(f"Received Twilio webhook: {request.POST}")
        
        # Extract webhook data
        webhook_data = dict(request.POST)
        
        # Process webhook asynchronously
        process_twilio_webhook.delay(webhook_data)
        
        # Return success response to Twilio
        return HttpResponse('OK', status=200)
        
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        return HttpResponse('Error', status=500)


@api_view(['GET'])
def notification_stats(request):
    """API view to get notification statistics for the user."""
    
    user_notifications = NotificationLog.objects.filter(user=request.user)
    
    stats = {
        'total_notifications': user_notifications.count(),
        'sent_notifications': user_notifications.filter(status='sent').count(),
        'delivered_notifications': user_notifications.filter(status='delivered').count(),
        'failed_notifications': user_notifications.filter(status='failed').count(),
        'demo_notifications': user_notifications.filter(is_demo=True).count(),
        'by_type': {
            'wakeup_calls': user_notifications.filter(notification_type='wakeup_call').count(),
            'wakeup_sms': user_notifications.filter(notification_type='wakeup_sms').count(),
            'verification_sms': user_notifications.filter(notification_type='verification_sms').count(),
        }
    }
    
    return Response(stats)