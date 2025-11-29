"""
Admin configuration for the notifications app.
"""

from django.contrib import admin
from .models import NotificationLog, TwilioWebhook


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationLog model."""
    
    list_display = [
        'notification_type', 'user', 'recipient_phone', 'status',
        'sent_at', 'delivered_at', 'is_demo', 'cost'
    ]
    list_filter = [
        'notification_type', 'status', 'is_demo', 'sent_at', 'delivered_at'
    ]
    search_fields = [
        'user__email', 'recipient_phone', 'twilio_sid', 
        'message_content', 'twilio_error_message'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'twilio_sid', 'twilio_status',
        'twilio_error_code', 'twilio_error_message', 'sent_at', 'delivered_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'notification_type', 'recipient_phone', 'status', 'is_demo')
        }),
        ('Content', {
            'fields': ('message_content',)
        }),
        ('Twilio Data', {
            'fields': (
                'twilio_sid', 'twilio_status', 'twilio_error_code', 
                'twilio_error_message'
            ),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at')
        }),
        ('Cost', {
            'fields': ('cost',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(TwilioWebhook)
class TwilioWebhookAdmin(admin.ModelAdmin):
    """Admin configuration for TwilioWebhook model."""
    
    list_display = [
        'twilio_sid', 'event_type', 'notification_log', 'processed', 'created_at'
    ]
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['twilio_sid', 'event_type']
    readonly_fields = ['created_at', 'webhook_data']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('twilio_sid', 'event_type', 'notification_log', 'processed')
        }),
        ('Webhook Data', {
            'fields': ('webhook_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notification_log')