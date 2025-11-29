"""
URL configuration for the web app.
"""

from django.urls import path
from . import views, monitoring_views, admin_views, dashboard_views, user_dashboard_views

app_name = 'web'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Authenticated pages
    path('dashboard/', user_dashboard_views.user_dashboard, name='user_dashboard'),
    path('requirements-dashboard/', dashboard_views.main_dashboard, name='main_dashboard'),
    path('dashboard/admin-action/', dashboard_views.admin_action, name='admin_action'),
    path('dashboard/test-call/<int:call_id>/', dashboard_views.test_wakeup_call, name='test_wakeup_call'),
    path('api-test/', dashboard_views.api_test_page, name='api_test'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_web, name='change_password'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
    
    # Wake-up calls
    path('wakeup-calls/', views.wakeup_calls_list, name='wakeup_calls'),
    path('wakeup-calls/create/', views.create_wakeup_call, name='create_wakeup_call'),
    path('wakeup-calls/<int:pk>/', views.wakeup_call_detail, name='wakeup_call_detail'),
    path('wakeup-calls/<int:call_id>/update-status/', views.update_wakeup_call_status, name='update_wakeup_call_status'),
    path('auto-verify-phone/', views.auto_verify_phone_number, name='auto_verify_phone'),
    
    # Monitoring
    path('monitor/', monitoring_views.celery_monitor, name='celery_monitor'),
    
    # Admin views
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', admin_views.admin_users_management, name='admin_users'),
    path('admin-users/<int:user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),
    path('admin-users/create-call/', admin_views.admin_create_call_for_user, name='admin_create_call'),
    path('admin-bulk-verify/', admin_views.bulk_phone_verification, name='bulk_phone_verification'),
    path('admin-logs/', admin_views.admin_system_logs, name='admin_logs'),
    path('admin-demo/', admin_views.admin_demo_management, name='admin_demo'),
    path('api/monitor/stats/', monitoring_views.celery_api_stats, name='celery_api_stats'),
]
