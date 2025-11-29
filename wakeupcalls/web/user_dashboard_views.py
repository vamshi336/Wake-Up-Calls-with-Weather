"""
Clean, user-friendly dashboard views.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from django.contrib.auth import get_user_model

from wakeup_calls.models import WakeUpCall, WakeUpCallExecution

User = get_user_model()


@login_required
def user_dashboard(request):
    """
    Clean, user-friendly dashboard for regular users.
    """
    user = request.user
    
    # User's wake-up calls (show recent 5)
    user_calls = user.wakeup_calls.all().order_by('-created_at')[:5]
    
    # Recent executions (show last 8)
    user_executions = WakeUpCallExecution.objects.filter(
        wakeup_call__user=user
    ).order_by('-executed_at')[:8]
    
    # User statistics
    user_stats = {
        'total_calls': user.wakeup_calls.count(),
        'active_calls': user.wakeup_calls.filter(status='active').count(),
        'total_executions': WakeUpCallExecution.objects.filter(wakeup_call__user=user).count(),
        'phone_verified': user.phone_verified,
    }
    
    context = {
        'user_calls': user_calls,
        'user_executions': user_executions,
        'user_stats': user_stats,
    }
    
    return render(request, 'web/user_dashboard.html', context)
