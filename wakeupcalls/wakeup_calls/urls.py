"""
URL configuration for the wakeup_calls app.
"""

from django.urls import path
from . import views

app_name = 'wakeup_calls'

urlpatterns = [
    # Wake-up call CRUD (RECOMMENDED - Use these!)
    path('', views.WakeUpCallListCreateView.as_view(), name='list_create'),
    path('<int:pk>/', views.WakeUpCallDetailView.as_view(), name='detail'),
    
    # Testing endpoints
    path('<int:pk>/test-now/', views.test_wakeup_call_now, name='test_now'),
    path('<int:pk>/test-sms/', views.test_sms_now, name='test_sms'),
    
    # Executions
    path('executions/', views.WakeUpCallExecutionListView.as_view(), name='executions_list'),
    path('<int:wakeup_call_id>/executions/', views.WakeUpCallExecutionListView.as_view(), name='call_executions_list'),
    
    # Statistics
    path('stats/', views.wakeup_call_stats, name='stats'),
    
    # TwiML endpoints (for Twilio)
    path('twiml/<int:execution_id>/', views.twiml_wakeup_call, name='twiml'),
    path('twiml/<int:execution_id>/response/', views.twiml_wakeup_call_response, name='twiml_response'),
    
    # DEPRECATED endpoints (use PATCH /api/wakeup-calls/{id}/ instead)
    path('<int:pk>/status/', views.update_wakeup_call_status, name='update_status'),
    path('<int:pk>/schedule/', views.update_wakeup_call_schedule, name='update_schedule'),
    path('<int:pk>/contact-method/', views.update_wakeup_call_contact_method, name='update_contact_method'),
]
