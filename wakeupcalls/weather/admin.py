"""
Admin configuration for the weather app.
"""

from django.contrib import admin
from .models import WeatherCache, WeatherAPILog


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    """Admin configuration for WeatherCache model."""
    
    list_display = ['zip_code', 'cached_at', 'expires_at', 'is_expired']
    list_filter = ['cached_at', 'expires_at']
    search_fields = ['zip_code']
    readonly_fields = ['cached_at', 'weather_data', 'is_expired']
    ordering = ['-cached_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('zip_code', 'cached_at', 'expires_at', 'is_expired')
        }),
        ('Weather Data', {
            'fields': ('weather_data',),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(WeatherAPILog)
class WeatherAPILogAdmin(admin.ModelAdmin):
    """Admin configuration for WeatherAPILog model."""
    
    list_display = [
        'zip_code', 'status', 'response_time_ms', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['zip_code', 'error_message']
    readonly_fields = ['created_at', 'response_data']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('zip_code', 'status', 'response_time_ms', 'created_at')
        }),
        ('Response Data', {
            'fields': ('response_data',),
            'classes': ('collapse',)
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )