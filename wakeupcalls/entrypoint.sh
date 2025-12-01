#!/bin/bash
set -e

if [ "$1" = 'gunicorn' ]; then
    exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 wakeupcalls_project.wsgi:application
elif [ "$1" = 'celery_worker' ]; then
    exec celery -A wakeupcalls_project worker --loglevel=info
elif [ "$1" = 'celery_beat' ]; then
    exec celery -A wakeupcalls_project beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
    exec "$@"
fi
