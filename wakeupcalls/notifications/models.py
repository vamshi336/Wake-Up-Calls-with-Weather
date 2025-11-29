from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField


class NotificationLog(models.Model):
    """Model to log all notifications sent through the system."""
    
    TYPE_CHOICES = [
        ('wakeup_call', 'Wake-up Call'),
        ('wakeup_sms', 'Wake-up SMS'),
        ('verification_sms', 'Phone Verification SMS'),
        ('system_notification', 'System Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        blank=True, 
        null=True
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    recipient_phone = PhoneNumberField()
    
    # Content
    message_content = models.TextField(blank=True, null=True)
    
    # Twilio data
    twilio_sid = models.CharField(max_length=100, blank=True, null=True)
    twilio_status = models.CharField(max_length=50, blank=True, null=True)
    twilio_error_code = models.CharField(max_length=10, blank=True, null=True)
    twilio_error_message = models.TextField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    # Cost tracking
    cost = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    
    # Demo mode
    is_demo = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['twilio_sid']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient_phone} - {self.status}"


class TwilioWebhook(models.Model):
    """Model to store Twilio webhook events for tracking delivery status."""
    
    notification_log = models.ForeignKey(
        NotificationLog, 
        on_delete=models.CASCADE, 
        related_name='webhooks',
        blank=True,
        null=True
    )
    twilio_sid = models.CharField(max_length=100, db_index=True)
    event_type = models.CharField(max_length=50)  # delivered, failed, etc.
    
    # Raw webhook data
    webhook_data = models.JSONField()
    
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Webhook {self.event_type} for {self.twilio_sid}"
