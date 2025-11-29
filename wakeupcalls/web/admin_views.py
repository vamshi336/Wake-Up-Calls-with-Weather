"""
Admin-specific views for the web interface.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import timedelta, time, date
from django.contrib.auth import get_user_model
from wakeup_calls.models import WakeUpCall, WakeUpCallExecution
from wakeup_calls.tasks import update_next_execution_time
from notifications.models import NotificationLog
from accounts.models import PhoneVerification
import json

User = get_user_model()


@login_required
@staff_member_required
def admin_dashboard(request):
    """
    Admin dashboard with comprehensive system overview.
    """
    # Time ranges
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # User statistics
    user_stats = {
        'total_users': User.objects.count(),
        'new_users_24h': User.objects.filter(date_joined__gte=last_24h).count(),
        'verified_users': User.objects.filter(phone_verified=True).count(),
        'admin_users': User.objects.filter(role='admin').count(),
        'active_users_7d': User.objects.filter(last_login__gte=last_7d).count(),
    }
    
    # Wake-up call statistics
    call_stats = {
        'total_calls': WakeUpCall.objects.count(),
        'active_calls': WakeUpCall.objects.filter(status='active').count(),
        'demo_calls': WakeUpCall.objects.filter(is_demo=True).count(),
        'calls_with_weather': WakeUpCall.objects.filter(include_weather=True).count(),
        'voice_calls': WakeUpCall.objects.filter(contact_method='call').count(),
        'sms_calls': WakeUpCall.objects.filter(contact_method='sms').count(),
    }
    
    # Execution statistics
    execution_stats = {
        'total_executions': WakeUpCallExecution.objects.count(),
        'executions_24h': WakeUpCallExecution.objects.filter(executed_at__gte=last_24h).count(),
        'successful_24h': WakeUpCallExecution.objects.filter(
            executed_at__gte=last_24h, status='completed'
        ).count(),
        'failed_24h': WakeUpCallExecution.objects.filter(
            executed_at__gte=last_24h, status='failed'
        ).count(),
        'pending_executions': WakeUpCallExecution.objects.filter(status='pending').count(),
    }
    
    # Notification statistics
    notification_stats = {
        'total_notifications': NotificationLog.objects.count(),
        'sms_sent_24h': NotificationLog.objects.filter(
            sent_at__gte=last_24h, notification_type='sms'
        ).count(),
        'voice_calls_24h': NotificationLog.objects.filter(
            sent_at__gte=last_24h, notification_type='voice'
        ).count(),
        'demo_notifications': NotificationLog.objects.filter(is_demo=True).count(),
        'failed_notifications_24h': NotificationLog.objects.filter(
            sent_at__gte=last_24h, status='failed'
        ).count(),
    }
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_calls = WakeUpCall.objects.select_related('user').order_by('-created_at')[:10]
    recent_executions = WakeUpCallExecution.objects.select_related(
        'wakeup_call', 'wakeup_call__user'
    ).order_by('-executed_at')[:10]
    
    # System health indicators
    system_health = {
        'unverified_users': User.objects.filter(phone_verified=False).count(),
        'failed_executions_rate': (
            execution_stats['failed_24h'] / max(execution_stats['executions_24h'], 1) * 100
        ),
        'pending_verifications': PhoneVerification.objects.filter(
            is_verified=False, expires_at__gt=now
        ).count(),
    }
    
    context = {
        'user_stats': user_stats,
        'call_stats': call_stats,
        'execution_stats': execution_stats,
        'notification_stats': notification_stats,
        'recent_users': recent_users,
        'recent_calls': recent_calls,
        'recent_executions': recent_executions,
        'system_health': system_health,
    }
    
    return render(request, 'web/admin_dashboard.html', context)


@login_required
@staff_member_required
def admin_users_management(request):
    """
    Admin view for managing users with comprehensive details.
    """
    # Get users with related data for efficiency
    users = User.objects.prefetch_related(
        'wakeup_calls', 'notification_logs', 'phone_verifications'
    ).annotate(
        total_calls=Count('wakeup_calls'),
        active_calls=Count('wakeup_calls', filter=Q(wakeup_calls__status='active')),
        total_executions=Count('wakeup_calls__executions'),
        successful_executions=Count('wakeup_calls__executions', filter=Q(wakeup_calls__executions__status='completed'))
    ).order_by('-date_joined')
    
    # Handle user actions
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            
            if action == 'verify_phone':
                user.phone_verified = True
                user.save()
                messages.success(request, f'Phone verified for {user.email}')
                
            elif action == 'make_admin':
                user.role = 'admin'
                user.is_staff = True
                user.save()
                messages.success(request, f'{user.email} is now an admin')
                
            elif action == 'remove_admin':
                user.role = 'user'
                user.is_staff = False
                user.save()
                messages.success(request, f'Admin privileges removed from {user.email}')
                
            elif action == 'deactivate':
                user.is_active = False
                user.save()
                messages.success(request, f'User {user.email} deactivated')
                
            elif action == 'activate':
                user.is_active = True
                user.save()
                messages.success(request, f'User {user.email} activated')
                
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('web:admin_users')
    
    # Calculate summary statistics
    user_summary = {
        'total_users': users.count(),
        'verified_users': users.filter(phone_verified=True).count(),
        'admin_users': users.filter(role='admin').count(),
        'active_users': users.filter(is_active=True).count(),
        'demo_users': users.filter(email__contains='demo').count(),
    }
    
    context = {
        'users': users,
        'user_summary': user_summary,
    }
    
    return render(request, 'web/admin_users.html', context)


@login_required
@staff_member_required
def admin_user_detail(request, user_id):
    """
    Admin view for detailed user information and management.
    """
    user = User.objects.prefetch_related(
        'wakeup_calls', 'notification_logs', 'phone_verifications'
    ).get(id=user_id)
    
    # Get user's wake-up calls with execution stats
    wakeup_calls = user.wakeup_calls.annotate(
        execution_count=Count('executions'),
        successful_count=Count('executions', filter=Q(executions__status='completed')),
        failed_count=Count('executions', filter=Q(executions__status='failed'))
    ).order_by('-created_at')
    
    # Get recent executions
    recent_executions = WakeUpCallExecution.objects.filter(
        wakeup_call__user=user
    ).select_related('wakeup_call').order_by('-executed_at')[:10]
    
    # Get recent notifications
    recent_notifications = user.notification_logs.order_by('-sent_at')[:10]
    
    # Get phone verification history
    phone_verifications = user.phone_verifications.order_by('-created_at')[:5]
    
    # Calculate user statistics
    now = timezone.now()
    last_30d = now - timedelta(days=30)
    
    user_stats = {
        'total_calls': wakeup_calls.count(),
        'active_calls': wakeup_calls.filter(status='active').count(),
        'total_executions': WakeUpCallExecution.objects.filter(wakeup_call__user=user).count(),
        'successful_executions': WakeUpCallExecution.objects.filter(
            wakeup_call__user=user, status='completed'
        ).count(),
        'failed_executions': WakeUpCallExecution.objects.filter(
            wakeup_call__user=user, status='failed'
        ).count(),
        'executions_30d': WakeUpCallExecution.objects.filter(
            wakeup_call__user=user, executed_at__gte=last_30d
        ).count(),
        'notifications_sent': user.notification_logs.count(),
        'sms_sent': user.notification_logs.filter(notification_type='sms').count(),
        'voice_calls': user.notification_logs.filter(notification_type='voice').count(),
    }
    
    # Handle user actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            if action == 'verify_phone':
                user.phone_verified = True
                user.save()
                messages.success(request, f'Phone verified for {user.email}')
                
            elif action == 'make_admin':
                user.role = 'admin'
                user.is_staff = True
                user.save()
                messages.success(request, f'{user.email} is now an admin')
                
            elif action == 'remove_admin':
                user.role = 'user'
                user.is_staff = False
                user.save()
                messages.success(request, f'Admin privileges removed from {user.email}')
                
            elif action == 'deactivate':
                user.is_active = False
                user.save()
                messages.success(request, f'User {user.email} deactivated')
                
            elif action == 'activate':
                user.is_active = True
                user.save()
                messages.success(request, f'User {user.email} activated')
                
            elif action == 'reset_phone_verification':
                user.phone_verified = False
                user.phone_verification_code = None
                user.phone_verification_expires = None
                user.save()
                messages.success(request, f'Phone verification reset for {user.email}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('web:admin_user_detail', user_id=user.id)
    
    context = {
        'user_detail': user,
        'wakeup_calls': wakeup_calls,
        'recent_executions': recent_executions,
        'recent_notifications': recent_notifications,
        'phone_verifications': phone_verifications,
        'user_stats': user_stats,
    }
    
    return render(request, 'web/admin_user_detail.html', context)


@login_required
@staff_member_required
def admin_system_logs(request):
    """
    Admin view for system logs and monitoring.
    """
    # Recent executions with details
    executions = WakeUpCallExecution.objects.select_related(
        'wakeup_call', 'wakeup_call__user'
    ).order_by('-executed_at')[:50]
    
    # Recent notifications
    notifications = NotificationLog.objects.select_related('user').order_by('-sent_at')[:50]
    
    # Failed operations
    failed_executions = WakeUpCallExecution.objects.filter(
        status='failed'
    ).select_related('wakeup_call', 'wakeup_call__user').order_by('-executed_at')[:20]
    
    context = {
        'executions': executions,
        'notifications': notifications,
        'failed_executions': failed_executions,
    }
    
    return render(request, 'web/admin_logs.html', context)


@login_required
@staff_member_required
def admin_demo_management(request):
    """
    Admin view for managing demo data.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'clear_demo_data':
            # Clear demo data
            demo_executions = WakeUpCallExecution.objects.filter(wakeup_call__is_demo=True)
            demo_calls = WakeUpCall.objects.filter(is_demo=True)
            demo_notifications = NotificationLog.objects.filter(is_demo=True)
            demo_users = User.objects.filter(email__contains='demo')
            
            demo_executions_count = demo_executions.count()
            demo_calls_count = demo_calls.count()
            demo_notifications_count = demo_notifications.count()
            demo_users_count = demo_users.count()
            
            demo_executions.delete()
            demo_calls.delete()
            demo_notifications.delete()
            demo_users.delete()
            
            messages.success(
                request, 
                f'Cleared demo data: {demo_users_count} users, {demo_calls_count} calls, '
                f'{demo_executions_count} executions, {demo_notifications_count} notifications'
            )
            
        elif action == 'seed_demo_data':
            # Trigger demo data seeding
            from django.core.management import call_command
            try:
                call_command('seed_demo_data', '--users', '5', '--calls-per-user', '3', '--executions', '30')
                messages.success(request, 'Demo data seeded successfully!')
            except Exception as e:
                messages.error(request, f'Error seeding demo data: {str(e)}')
        
        return redirect('web:admin_demo')
    
    # Get current demo data stats
    demo_stats = {
        'demo_users': User.objects.filter(email__contains='demo').count(),
        'demo_calls': WakeUpCall.objects.filter(is_demo=True).count(),
        'demo_executions': WakeUpCallExecution.objects.filter(wakeup_call__is_demo=True).count(),
        'demo_notifications': NotificationLog.objects.filter(is_demo=True).count(),
    }
    
    context = {
        'demo_stats': demo_stats,
    }
    
    return render(request, 'web/admin_demo.html', context)


@login_required
@staff_member_required
@require_POST
def admin_create_call_for_user(request):
    """
    Admin endpoint to create a wake-up call for any user.
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        # Get the target user
        target_user = get_object_or_404(User, id=user_id)
        
        # Validate required fields
        required_fields = ['name', 'contact_method', 'scheduled_time', 'frequency']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field.replace("_", " ").title()} is required'
                }, status=400)
        
        # Parse time
        try:
            scheduled_time = time.fromisoformat(data['scheduled_time'])
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid time format'
            }, status=400)
        
        # Create the wake-up call
        wakeup_call = WakeUpCall.objects.create(
            user=target_user,
            name=data['name'],
            phone_number=target_user.phone_number or '+1234567890',  # Use user's phone or placeholder
            contact_method=data['contact_method'],
            scheduled_time=scheduled_time,
            frequency=data['frequency'],
            start_date=date.today(),
            include_weather=data.get('include_weather', False),
            weather_zip_code=target_user.zip_code,
            custom_message=data.get('custom_message', ''),
            status='active',
            is_demo=False  # Admin-created calls are real
        )
        
        # Update next execution time
        update_next_execution_time(wakeup_call)
        
        return JsonResponse({
            'success': True,
            'message': f'Wake-up call "{wakeup_call.name}" created successfully for {target_user.email}',
            'call_id': wakeup_call.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@staff_member_required
def bulk_phone_verification(request):
    """
    Admin tool for bulk phone number verification.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_numbers = data.get('phone_numbers', [])
            verification_method = data.get('method', 'bypass')  # 'bypass' or 'twilio'
            
            results = []
            
            for phone_number in phone_numbers:
                phone_number = phone_number.strip()
                if not phone_number:
                    continue
                
                try:
                    if verification_method == 'bypass':
                        # Development bypass - mark as verified in our system
                        from accounts.models import PhoneVerification
                        from django.utils import timezone
                        
                        # Create or get user (for admin testing, we can create a test user)
                        user, created = User.objects.get_or_create(
                            username=f'test_{phone_number.replace("+", "").replace(" ", "")}',
                            defaults={
                                'email': f'test_{phone_number.replace("+", "").replace(" ", "")}@example.com',
                                'phone_number': phone_number,
                                'phone_verified': True,
                                'first_name': 'Test',
                                'last_name': 'User'
                            }
                        )
                        
                        if not created:
                            user.phone_number = phone_number
                            user.phone_verified = True
                            user.save()
                        
                        # Create verification record
                        PhoneVerification.objects.create(
                            user=user,
                            phone_number=phone_number,
                            verification_code='ADMIN_BYPASS',
                            is_verified=True,
                            attempts=0,
                            expires_at=timezone.now() + timezone.timedelta(days=365)
                        )
                        
                        results.append({
                            'phone': phone_number,
                            'status': 'success',
                            'method': 'bypass',
                            'message': 'Verified via admin bypass'
                        })
                        
                    elif verification_method == 'twilio':
                        # Try Twilio verification (will likely fail on trial)
                        from notifications.services import twilio_service
                        result = twilio_service.auto_verify_phone_number(phone_number)
                        
                        results.append({
                            'phone': phone_number,
                            'status': 'success' if result['success'] else 'failed',
                            'method': 'twilio',
                            'message': result.get('message', result.get('error', 'Unknown result'))
                        })
                        
                except Exception as e:
                    results.append({
                        'phone': phone_number,
                        'status': 'error',
                        'method': verification_method,
                        'message': str(e)
                    })
            
            return JsonResponse({
                'success': True,
                'results': results,
                'total_processed': len(results)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - show the bulk verification page
    return render(request, 'web/bulk_phone_verification.html')
