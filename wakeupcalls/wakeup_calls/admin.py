"""
Admin configuration for the wakeup_calls app.
"""

from django.contrib import admin
from .models import WakeUpCall, WakeUpCallExecution


@admin.register(WakeUpCall)
class WakeUpCallAdmin(admin.ModelAdmin):
    """Admin configuration for WakeUpCall model."""
    
    list_display = [
        'name', 'user', 'contact_method', 'scheduled_time', 
        'frequency', 'status', 'next_execution', 'is_demo'
    ]
    list_filter = [
        'contact_method', 'frequency', 'status', 'is_demo', 
        'include_weather', 'created_at'
    ]
    search_fields = ['name', 'user__email', 'phone_number', 'custom_message']
    readonly_fields = ['created_at', 'updated_at', 'last_executed', 'next_execution']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'phone_number', 'contact_method', 'is_demo')
        }),
        ('Schedule', {
            'fields': (
                'scheduled_time', 'frequency', 'start_date', 'end_date',
                ('monday', 'tuesday', 'wednesday', 'thursday'),
                ('friday', 'saturday', 'sunday')
            )
        }),
        ('Content', {
            'fields': ('include_weather', 'weather_zip_code', 'custom_message')
        }),
        ('Status', {
            'fields': ('status', 'last_executed', 'next_execution')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(WakeUpCallExecution)
class WakeUpCallExecutionAdmin(admin.ModelAdmin):
    """Admin configuration for WakeUpCallExecution model."""
    
    list_display = [
        'wakeup_call', 'scheduled_for', 'executed_at', 'status', 
        'twilio_status', 'user_response'
    ]
    list_filter = ['status', 'twilio_status', 'scheduled_for', 'executed_at']
    search_fields = [
        'wakeup_call__name', 'wakeup_call__user__email', 
        'twilio_sid', 'error_message'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'twilio_sid', 'twilio_status',
        'weather_data', 'interaction_data'
    ]
    ordering = ['-scheduled_for']
    
    fieldsets = (
        ('Execution Info', {
            'fields': ('wakeup_call', 'scheduled_for', 'executed_at', 'status')
        }),
        ('Twilio Data', {
            'fields': ('twilio_sid', 'twilio_status'),
            'classes': ('collapse',)
        }),
        ('User Interaction', {
            'fields': ('user_response', 'interaction_data'),
            'classes': ('collapse',)
        }),
        ('Weather Data', {
            'fields': ('weather_data',),
            'classes': ('collapse',)
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wakeup_call', 'wakeup_call__user')