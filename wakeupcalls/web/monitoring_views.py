"""
Monitoring views for Celery workers and tasks.
"""

import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from celery import current_app
from wakeup_calls.models import WakeUpCall, WakeUpCallExecution
from notifications.models import NotificationLog


@staff_member_required
def celery_monitor(request):
    """
    Celery monitoring dashboard.
    """
    # Get worker stats
    try:
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        active_tasks = inspect.active()
        registered_tasks = inspect.registered()
        
        worker_info = []
        if stats:
            for worker_name, worker_stats in stats.items():
                pool_info = worker_stats.get('pool', {})
                worker_info.append({
                    'name': worker_name,
                    'pid': worker_stats.get('pid'),
                    'uptime': worker_stats.get('uptime', 0),
                    'total_tasks': worker_stats.get('total', {}),
                    'pool': pool_info,
                    'pool_implementation': pool_info.get('implementation', 'N/A'),
                    'pool_max_concurrency': pool_info.get('max-concurrency', 'N/A'),
                    'broker': worker_stats.get('broker', {}),
                    'active_tasks': active_tasks.get(worker_name, []) if active_tasks else [],
                    'registered_tasks': registered_tasks.get(worker_name, []) if registered_tasks else []
                })
    except Exception as e:
        worker_info = []
        stats = {'error': str(e)}
    
    # Get recent task executions
    recent_executions = WakeUpCallExecution.objects.select_related(
        'wakeup_call', 'wakeup_call__user'
    ).order_by('-created_at')[:20]
    
    # Get task statistics
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    task_stats = {
        'total_calls': WakeUpCall.objects.count(),
        'active_calls': WakeUpCall.objects.filter(status='active').count(),
        'executions_24h': WakeUpCallExecution.objects.filter(created_at__gte=last_24h).count(),
        'successful_24h': WakeUpCallExecution.objects.filter(
            created_at__gte=last_24h, status='completed'
        ).count(),
        'failed_24h': WakeUpCallExecution.objects.filter(
            created_at__gte=last_24h, status='failed'
        ).count(),
        'sms_sent_24h': NotificationLog.objects.filter(
            created_at__gte=last_24h, notification_type='sms', status='sent'
        ).count(),
    }
    
    # Get execution status breakdown
    status_breakdown = WakeUpCallExecution.objects.filter(
        created_at__gte=last_24h
    ).values('status').annotate(count=Count('id'))
    
    context = {
        'worker_info': worker_info,
        'recent_executions': recent_executions,
        'task_stats': task_stats,
        'status_breakdown': status_breakdown,
        'stats_json': json.dumps(stats, indent=2) if stats else '{}',
    }
    
    return render(request, 'web/celery_monitor.html', context)


@staff_member_required
def celery_api_stats(request):
    """
    API endpoint for real-time Celery stats.
    """
    try:
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        active_tasks = inspect.active()
        
        # Format for JSON response
        response_data = {
            'workers': [],
            'timestamp': datetime.now().isoformat()
        }
        
        if stats:
            for worker_name, worker_stats in stats.items():
                response_data['workers'].append({
                    'name': worker_name,
                    'pid': worker_stats.get('pid'),
                    'uptime': worker_stats.get('uptime', 0),
                    'total_tasks': worker_stats.get('total', {}),
                    'active_tasks_count': len(active_tasks.get(worker_name, []) if active_tasks else [])
                })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
