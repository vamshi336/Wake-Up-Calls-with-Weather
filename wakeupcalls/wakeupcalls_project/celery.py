"""
Celery configuration for the wakeupcalls_project.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wakeupcalls_project.settings')

app = Celery('wakeupcalls_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'process-scheduled-wakeup-calls': {
        'task': 'wakeup_calls.tasks.process_scheduled_wakeup_calls',
        'schedule': 60.0,  # Run every minute
    },
    'cleanup-old-logs': {
        'task': 'notifications.tasks.cleanup_old_notification_logs',
        'schedule': 86400.0,  # Run daily
    },
    'cleanup-expired-weather-cache': {
        'task': 'weather.tasks.cleanup_expired_weather_cache',
        'schedule': 3600.0,  # Run hourly
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
