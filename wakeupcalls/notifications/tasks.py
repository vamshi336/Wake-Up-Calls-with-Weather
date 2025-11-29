"""
Celery tasks for notification management.
"""

import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from .models import NotificationLog, TwilioWebhook

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_notification_logs():
    """
    Clean up old notification logs to prevent database bloat.
    Keeps logs for the last 90 days.
    """
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count, _ = NotificationLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old notification logs")
    return deleted_count


@shared_task
def cleanup_old_webhook_logs():
    """
    Clean up old Twilio webhook logs.
    Keeps logs for the last 30 days.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count, _ = TwilioWebhook.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old webhook logs")
    return deleted_count


@shared_task
def process_twilio_webhook(webhook_data: dict):
    """
    Process a Twilio webhook event asynchronously.
    
    Args:
        webhook_data: The webhook payload from Twilio
    """
    try:
        message_sid = webhook_data.get('MessageSid') or webhook_data.get('CallSid')
        event_type = webhook_data.get('MessageStatus') or webhook_data.get('CallStatus')
        
        if not message_sid:
            logger.warning("Webhook received without SID")
            return
        
        # Create webhook log entry
        webhook_log = TwilioWebhook.objects.create(
            twilio_sid=message_sid,
            event_type=event_type,
            webhook_data=webhook_data
        )
        
        # Find corresponding notification log
        try:
            notification_log = NotificationLog.objects.get(twilio_sid=message_sid)
            webhook_log.notification_log = notification_log
            
            # Update notification status based on webhook
            if event_type in ['delivered', 'sent']:
                notification_log.status = 'delivered'
                notification_log.delivered_at = timezone.now()
            elif event_type in ['failed', 'undelivered']:
                notification_log.status = 'failed'
                notification_log.twilio_error_code = webhook_data.get('ErrorCode')
                notification_log.twilio_error_message = webhook_data.get('ErrorMessage')
            
            notification_log.twilio_status = event_type
            notification_log.save()
            
            logger.info(f"Updated notification {notification_log.id} status to {event_type}")
            
        except NotificationLog.DoesNotExist:
            logger.warning(f"No notification log found for Twilio SID: {message_sid}")
        
        webhook_log.processed = True
        webhook_log.save()
        
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        raise
