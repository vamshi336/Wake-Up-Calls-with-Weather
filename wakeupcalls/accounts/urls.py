"""
URL configuration for the accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Phone verification
    path('verify-phone/request/', views.request_phone_verification, name='request_phone_verification'),
    path('verify-phone/verify/', views.verify_phone_code, name='verify_phone_code'),
    path('verify-phone/resend/', views.resend_verification_code, name='resend_verification_code'),
    path('verify-phone/status/', views.phone_verification_status, name='phone_verification_status'),
]
