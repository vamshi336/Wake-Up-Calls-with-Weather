"""
Template tags for timezone handling.
"""

from django import template
from django.utils import timezone
import pytz

register = template.Library()


@register.filter
def user_timezone(datetime_obj, user_timezone='UTC'):
    """
    Convert a datetime object to the user's timezone.
    Usage: {{ some_datetime|user_timezone:user.timezone }}
    """
    if not datetime_obj:
        return None
    
    if not user_timezone:
        user_timezone = 'UTC'
    
    try:
        user_tz = pytz.timezone(user_timezone)
        if timezone.is_aware(datetime_obj):
            return datetime_obj.astimezone(user_tz)
        else:
            # If datetime is naive, assume it's in UTC
            utc_dt = pytz.UTC.localize(datetime_obj)
            return utc_dt.astimezone(user_tz)
    except Exception:
        return datetime_obj


@register.filter
def format_user_time(datetime_obj, user_timezone='UTC'):
    """
    Format datetime in user's timezone with a friendly format.
    Usage: {{ some_datetime|format_user_time:user.timezone }}
    """
    converted_dt = user_timezone(datetime_obj, user_timezone)
    if not converted_dt:
        return 'Not scheduled'
    
    return converted_dt.strftime('%b %d, %Y at %I:%M %p')


@register.filter
def timezone_name(timezone_str):
    """
    Get a friendly name for a timezone.
    Usage: {{ user.timezone|timezone_name }}
    """
    timezone_names = {
        'Asia/Kolkata': 'India Standard Time (IST)',
        'America/New_York': 'Eastern Time (ET)',
        'America/Chicago': 'Central Time (CT)', 
        'America/Denver': 'Mountain Time (MT)',
        'America/Los_Angeles': 'Pacific Time (PT)',
        'Europe/London': 'London Time (GMT/BST)',
        'Europe/Paris': 'Paris Time (CET/CEST)',
        'Asia/Dubai': 'Dubai Time (GST)',
        'Asia/Singapore': 'Singapore Time (SGT)',
        'Asia/Tokyo': 'Tokyo Time (JST)',
        'Australia/Sydney': 'Sydney Time (AEST/AEDT)',
        'UTC': 'UTC (Coordinated Universal Time)'
    }
    
    return timezone_names.get(timezone_str, timezone_str)
