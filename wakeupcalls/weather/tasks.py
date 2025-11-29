"""
Celery tasks for weather data management.
"""

import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from .models import WeatherCache, WeatherAPILog

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_weather_cache():
    """
    Clean up expired weather cache entries.
    """
    deleted_count, _ = WeatherCache.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} expired weather cache entries")
    return deleted_count


@shared_task
def cleanup_old_weather_api_logs():
    """
    Clean up old weather API logs to prevent database bloat.
    Keeps logs for the last 30 days.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count, _ = WeatherAPILog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old weather API logs")
    return deleted_count


@shared_task
def prefetch_weather_for_active_calls():
    """
    Prefetch weather data for all active wake-up calls to ensure fresh data.
    This task can be scheduled to run before peak wake-up times.
    """
    from wakeup_calls.models import WakeUpCall
    from .services import weather_service
    
    # Get unique zip codes from active wake-up calls
    zip_codes = WakeUpCall.objects.filter(
        status='active',
        include_weather=True
    ).values_list('weather_zip_code', 'user__zip_code').distinct()
    
    unique_zip_codes = set()
    for call_zip, user_zip in zip_codes:
        if call_zip:
            unique_zip_codes.add(call_zip)
        elif user_zip:
            unique_zip_codes.add(user_zip)
    
    fetched_count = 0
    for zip_code in unique_zip_codes:
        try:
            weather_data = weather_service.get_weather(zip_code, force_refresh=True)
            if weather_data:
                fetched_count += 1
                logger.debug(f"Prefetched weather data for {zip_code}")
        except Exception as e:
            logger.error(f"Error prefetching weather for {zip_code}: {e}")
    
    logger.info(f"Prefetched weather data for {fetched_count} zip codes")
    return fetched_count
