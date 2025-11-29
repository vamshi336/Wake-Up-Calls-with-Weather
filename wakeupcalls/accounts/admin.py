"""
Admin configuration for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import PhoneVerification

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""
    
    list_display = [
        'email', 'username', 'first_name', 'last_name', 
        'phone_number', 'phone_verified', 'role', 'is_active', 'created_at'
    ]
    list_filter = ['role', 'phone_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'phone_verified', 'zip_code', 'timezone', 'role')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'phone_verified']
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'phone_number', 'zip_code', 'timezone', 'role')
        }),
    )


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    """Admin configuration for PhoneVerification model."""
    
    list_display = [
        'user', 'phone_number', 'is_verified', 'attempts', 
        'created_at', 'expires_at'
    ]
    list_filter = ['is_verified', 'created_at', 'expires_at']
    search_fields = ['user__email', 'phone_number']
    readonly_fields = ['verification_code', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')