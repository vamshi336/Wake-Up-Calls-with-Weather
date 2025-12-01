"""
Celery tasks for wake-up call processing.
"""

import logging
from datetime import datetime, timedelta
from typing import List
from celery import shared_task
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from .models import WakeUpCall, WakeUpCallExecution
from notifications.services import twilio_service
from weather.services import weather_service

logger = logging.getLogger(__name__)


@shared_task
def process_scheduled_wakeup_calls():
    """
    Process all wake-up calls that are scheduled to execute now.
    This task runs every minute via Celery Beat.
    """
    current_time = timezone.now()
    logger.info(f"Processing scheduled wake-up calls at {current_time}")
    
    # Find wake-up calls that should execute now
    # We look for calls scheduled within the next minute to account for timing variations
    end_time = current_time + timedelta(minutes=1)
    
    scheduled_calls = WakeUpCall.objects.filter(
        status='active',
        next_execution__lte=end_time,
        next_execution__gte=current_time - timedelta(minutes=1)
    ).select_related('user')
    
    processed_count = 0
    
    for wakeup_call in scheduled_calls:
        try:
            # Check if this call should execute today based on frequency
            if wakeup_call.should_execute_today():
                # Create execution record
                execution = WakeUpCallExecution.objects.create(
                    wakeup_call=wakeup_call,
                    scheduled_for=wakeup_call.next_execution,
                    status='pending'
                )
                
                # Execute the wake-up call asynchronously
                execute_wakeup_call.delay(execution.id)
                processed_count += 1
                
                logger.info(f"Scheduled execution for wake-up call {wakeup_call.id}")
            
            # Update next execution time
            update_next_execution_time(wakeup_call)
            
        except Exception as e:
            logger.error(f"Error processing wake-up call {wakeup_call.id}: {e}")
    
    logger.info(f"Processed {processed_count} wake-up calls")
    return processed_count


@shared_task
def execute_wakeup_call(execution_id: int):
    """
    Execute a specific wake-up call.
    
    Args:
        execution_id: ID of the WakeUpCallExecution to process
    """
    try:
        execution = WakeUpCallExecution.objects.select_related(
            'wakeup_call', 'wakeup_call__user'
        ).get(id=execution_id)
    except WakeUpCallExecution.DoesNotExist:
        logger.error(f"WakeUpCallExecution {execution_id} not found")
        return
    
    wakeup_call = execution.wakeup_call
    user = wakeup_call.user
    
    logger.info(f"Executing wake-up call {wakeup_call.id} for user {user.email}")
    
    # Update execution status
    execution.status = 'in_progress'
    execution.executed_at = timezone.now()
    execution.save()
    
    try:
        # Get weather information if requested
        weather_message = ""
        if wakeup_call.include_weather:
            zip_code = wakeup_call.get_weather_zip_code()
            if zip_code:
                weather_message = weather_service.get_formatted_weather_announcement(zip_code)
                execution.weather_data = weather_service.get_weather(zip_code)
            else:
                weather_message = "Weather information is not available because no zip code is configured."
        
        # Prepare the message
        greeting = "Good morning! This is your wake-up call from Vamshi."
        custom_msg = wakeup_call.custom_message or ""
        
        if wakeup_call.contact_method == 'sms':
            # Send SMS
            full_message = f"{greeting} {weather_message} {custom_msg}".strip()
            
            result = twilio_service.send_sms(
                to_phone=str(wakeup_call.phone_number),
                message=full_message,
                user=user,
                is_demo=wakeup_call.is_demo
            )
            
            if result['success']:
                execution.status = 'completed'
                execution.twilio_sid = result['sid']
                execution.twilio_status = result['status']
                logger.info(f"SMS wake-up call sent successfully: {result['sid']}")
            else:
                execution.status = 'failed'
                execution.error_message = result.get('error', 'Unknown error')
                logger.error(f"Failed to send SMS wake-up call: {result.get('error')}")
        
        elif wakeup_call.contact_method == 'call':
            # Make phone call
            # Generate TwiML URL for the call content
            twiml_url = generate_twiml_url(execution.id)
            
            result = twilio_service.make_call(
                to_phone=str(wakeup_call.phone_number),
                twiml_url=twiml_url,
                user=user,
                is_demo=wakeup_call.is_demo
            )
            
            if result['success']:
                execution.status = 'completed'
                execution.twilio_sid = result['sid']
                execution.twilio_status = result['status']
                logger.info(f"Voice wake-up call initiated successfully: {result['sid']}")
            else:
                # Voice call failed, fall back to SMS for local development
                logger.warning(f"Voice call failed, falling back to SMS: {result.get('error')}")
                
                full_message = f"{greeting} {weather_message} {custom_msg}".strip()
                
                sms_result = twilio_service.send_sms(
                    to_phone=str(wakeup_call.phone_number),
                    message=full_message,
                    user=user,
                    is_demo=wakeup_call.is_demo
                )
                
                if sms_result['success']:
                    execution.status = 'completed'
                    execution.twilio_sid = sms_result['sid']
                    execution.twilio_status = sms_result['status']
                    execution.error_message = f"Voice call failed, SMS sent instead: {result.get('error')}"
                    logger.info(f"Fallback SMS sent successfully: {sms_result['sid']}")
                else:
                    execution.status = 'failed'
                    execution.error_message = f"Voice call failed: {result.get('error')}. SMS fallback also failed: {sms_result.get('error')}"
                    logger.error(f"Both voice call and SMS fallback failed")
        
        # Update last executed time
        wakeup_call.last_executed = timezone.now()
        wakeup_call.save()
        
    except Exception as e:
        execution.status = 'failed'
        execution.error_message = str(e)
        logger.error(f"Error executing wake-up call {wakeup_call.id}: {e}")
    
    execution.save()


def update_next_execution_time(wakeup_call: WakeUpCall):
    """
    Update the next execution time for a wake-up call based on its frequency.
    
    Args:
        wakeup_call: WakeUpCall instance to update
    """
    from zoneinfo import ZoneInfo
    current_time = timezone.now()
    scheduled_time = wakeup_call.scheduled_time
    user_tz_str = getattr(wakeup_call.user, 'timezone', 'UTC')
    try:
        user_tz = ZoneInfo(user_tz_str)
    except Exception:
        user_tz = ZoneInfo('UTC')

    def local_to_utc(date, time):
        local_dt = datetime.combine(date, time)
        local_dt = local_dt.replace(tzinfo=user_tz)
        return local_dt.astimezone(ZoneInfo('UTC'))

    if wakeup_call.frequency == 'once':
        # One-time call, mark as completed
        wakeup_call.status = 'completed'
        wakeup_call.next_execution = None

    elif wakeup_call.frequency == 'daily':
        # Daily calls
        next_date = current_time.astimezone(user_tz).date() + timedelta(days=1)
        wakeup_call.next_execution = local_to_utc(next_date, scheduled_time)

    elif wakeup_call.frequency == 'weekly':
        # Weekly calls
        next_date = current_time.astimezone(user_tz).date() + timedelta(days=7)
        wakeup_call.next_execution = local_to_utc(next_date, scheduled_time)

    elif wakeup_call.frequency in ['weekdays', 'weekends', 'custom']:
        # Find next valid day
        next_date = current_time.astimezone(user_tz).date() + timedelta(days=1)
        max_days_ahead = 7  # Don't look more than a week ahead

        for _ in range(max_days_ahead):
            temp_call = WakeUpCall(
                frequency=wakeup_call.frequency,
                monday=wakeup_call.monday,
                tuesday=wakeup_call.tuesday,
                wednesday=wakeup_call.wednesday,
                thursday=wakeup_call.thursday,
                friday=wakeup_call.friday,
                saturday=wakeup_call.saturday,
                sunday=wakeup_call.sunday,
                start_date=next_date
            )

            if temp_call.should_execute_today():
                wakeup_call.next_execution = local_to_utc(next_date, scheduled_time)
                break

            next_date += timedelta(days=1)
        else:
            # No valid day found in the next week
            logger.warning(f"No valid execution day found for wake-up call {wakeup_call.id}")
            wakeup_call.next_execution = None
    
    # Check if we've passed the end date
    if wakeup_call.end_date and wakeup_call.next_execution:
        if wakeup_call.next_execution.date() > wakeup_call.end_date:
            wakeup_call.status = 'completed'
            wakeup_call.next_execution = None
    
    wakeup_call.save()


@shared_task
def schedule_snooze_call(execution_id: int, snooze_time_iso: str):
    """
    Schedule a snooze call for 10 minutes later.
    
    Args:
        execution_id: ID of the original WakeUpCallExecution
        snooze_time_iso: ISO format datetime string for when to execute snooze
    """
    try:
        from datetime import datetime
        
        # Get the original execution
        original_execution = WakeUpCallExecution.objects.get(id=execution_id)
        wakeup_call = original_execution.wakeup_call
        
        # Parse the snooze time
        snooze_time = datetime.fromisoformat(snooze_time_iso.replace('Z', '+00:00'))
        if snooze_time.tzinfo is None:
            snooze_time = timezone.make_aware(snooze_time)
        
        # Create a new execution for the snooze
        snooze_execution = WakeUpCallExecution.objects.create(
            wakeup_call=wakeup_call,
            scheduled_for=snooze_time,
            status='pending',
            is_snooze=True  # We'll need to add this field
        )
        
        # Schedule the snooze call to execute at the specified time
        # Calculate delay in seconds
        delay_seconds = (snooze_time - timezone.now()).total_seconds()
        
        if delay_seconds > 0:
            # Schedule the execution
            execute_wakeup_call.apply_async(
                args=[snooze_execution.id],
                countdown=delay_seconds
            )
            
            logger.info(f"Snooze call scheduled for execution {snooze_execution.id} in {delay_seconds} seconds")
        else:
            # If somehow the time has passed, execute immediately
            execute_wakeup_call.delay(snooze_execution.id)
            logger.warning(f"Snooze time has passed, executing immediately: {snooze_execution.id}")
            
    except Exception as e:
        logger.error(f"Error scheduling snooze call for execution {execution_id}: {e}")


def generate_twiml_url(execution_id: int) -> str:
    """
    Generate the TwiML URL for a wake-up call execution.
    
    Args:
        execution_id: ID of the WakeUpCallExecution
        
    Returns:
        Full URL to the TwiML endpoint
    """
    # This would be the full URL to your TwiML endpoint
    # For now, we'll use a placeholder that would be replaced with actual domain
    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    return f"{base_url}{reverse('wakeup_calls:twiml', kwargs={'execution_id': execution_id})}"


@shared_task
def schedule_next_wakeup_calls():
    """
    Calculate and schedule next execution times for all active wake-up calls.
    This is useful for initial setup or after system maintenance.
    """
    active_calls = WakeUpCall.objects.filter(status='active')
    updated_count = 0
    
    for wakeup_call in active_calls:
        try:
            if not wakeup_call.next_execution:
                update_next_execution_time(wakeup_call)
                updated_count += 1
        except Exception as e:
            logger.error(f"Error scheduling next execution for wake-up call {wakeup_call.id}: {e}")
    
    logger.info(f"Scheduled next execution for {updated_count} wake-up calls")
    return updated_count
