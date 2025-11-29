"""
Comprehensive dashboard views for the wake-up calls application.
All requirements in one place.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from wakeup_calls.models import WakeUpCall, WakeUpCallExecution
from notifications.models import NotificationLog
from accounts.models import PhoneVerification
from wakeup_calls.tasks import execute_wakeup_call

User = get_user_model()


@login_required
def main_dashboard(request):
    """
    Single comprehensive dashboard that handles all requirements:
    1. User wake-up call management
    2. Admin user management (if admin)
    3. Demo data management
    4. System monitoring
    """
    user = request.user
    
    # User's own wake-up calls
    user_calls = user.wakeup_calls.all().order_by('-created_at')
    user_executions = WakeUpCallExecution.objects.filter(
        wakeup_call__user=user
    ).order_by('-executed_at')[:10]
    
    # User statistics
    user_stats = {
        'total_calls': user_calls.count(),
        'active_calls': user_calls.filter(status='active').count(),
        'total_executions': WakeUpCallExecution.objects.filter(wakeup_call__user=user).count(),
        'phone_verified': user.phone_verified,
    }
    
    # Admin data (only if user is admin)
    admin_data = None
    if user.is_staff or user.role == 'admin':
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        admin_data = {
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(phone_verified=True).count(),
            'admin_users': User.objects.filter(Q(is_staff=True) | Q(role='admin')).count(),
            'demo_users': User.objects.filter(email__contains='demo').count(),
            'total_calls': WakeUpCall.objects.count(),
            'active_calls': WakeUpCall.objects.filter(status='active').count(),
            'demo_calls': WakeUpCall.objects.filter(is_demo=True).count(),
            'executions_24h': WakeUpCallExecution.objects.filter(executed_at__gte=last_24h).count(),
            'failed_24h': WakeUpCallExecution.objects.filter(
                executed_at__gte=last_24h, status='failed'
            ).count(),
            'recent_users': User.objects.order_by('-date_joined')[:5],
            'recent_executions': WakeUpCallExecution.objects.select_related(
                'wakeup_call', 'wakeup_call__user'
            ).order_by('-executed_at')[:10],
            'failed_executions': WakeUpCallExecution.objects.filter(
                status='failed'
            ).select_related('wakeup_call', 'wakeup_call__user').order_by('-executed_at')[:5],
        }
    
    context = {
        'user_calls': user_calls,
        'user_executions': user_executions,
        'user_stats': user_stats,
        'admin_data': admin_data,
        'is_admin': user.is_staff or user.role == 'admin',
    }
    
    return render(request, 'web/main_dashboard.html', context)


@login_required
@require_POST
def admin_action(request):
    """Handle admin actions from the dashboard."""
    if not (request.user.is_staff or request.user.role == 'admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'seed_demo_data':
            from django.core.management import call_command
            call_command('seed_demo_data', '--users', '5', '--calls-per-user', '3', '--executions', '30')
            return JsonResponse({'success': True, 'message': 'Demo data seeded successfully!'})
        
        elif action == 'clear_demo_data':
            # Clear demo data
            demo_executions = WakeUpCallExecution.objects.filter(wakeup_call__is_demo=True)
            demo_calls = WakeUpCall.objects.filter(is_demo=True)
            demo_notifications = NotificationLog.objects.filter(is_demo=True)
            demo_users = User.objects.filter(email__contains='demo')
            
            counts = {
                'executions': demo_executions.count(),
                'calls': demo_calls.count(),
                'notifications': demo_notifications.count(),
                'users': demo_users.count(),
            }
            
            demo_executions.delete()
            demo_calls.delete()
            demo_notifications.delete()
            demo_users.delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'Cleared {counts["users"]} users, {counts["calls"]} calls, {counts["executions"]} executions'
            })
        
        elif action == 'verify_user_phone':
            user_id = data.get('user_id')
            target_user = User.objects.get(id=user_id)
            target_user.phone_verified = True
            target_user.save()
            return JsonResponse({'success': True, 'message': f'Phone verified for {target_user.email}'})
        
        elif action == 'make_admin':
            user_id = data.get('user_id')
            target_user = User.objects.get(id=user_id)
            target_user.role = 'admin'
            target_user.is_staff = True
            target_user.save()
            return JsonResponse({'success': True, 'message': f'{target_user.email} is now an admin'})
        
        else:
            return JsonResponse({'error': 'Unknown action'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def test_wakeup_call(request, call_id):
    """Test a wake-up call immediately."""
    wakeup_call = get_object_or_404(WakeUpCall, id=call_id, user=request.user)
    
    if not request.user.phone_verified:
        return JsonResponse({'error': 'Phone number not verified'}, status=400)
    
    try:
        # Create immediate execution
        now = timezone.now()
        execution = WakeUpCallExecution.objects.create(
            wakeup_call=wakeup_call,
            scheduled_for=now,
            status='pending'
        )
        
        # Queue the task
        execute_wakeup_call.delay(execution.id)
        
        return JsonResponse({
            'success': True, 
            'message': 'Test call queued successfully!',
            'execution_id': execution.id
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_test_page(request):
    """Simple page to test the new API design."""
    user_calls = request.user.wakeup_calls.all()[:5]  # Get first 5 calls for testing
    
    context = {
        'user_calls': user_calls,
    }
    
    return render(request, 'web/api_test.html', context)
