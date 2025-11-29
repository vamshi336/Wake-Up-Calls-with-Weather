"""
API views for the wakeup_calls app.
"""

import logging
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from twilio.twiml.voice_response import VoiceResponse
from .models import WakeUpCall, WakeUpCallExecution
from .serializers import (
    WakeUpCallSerializer, WakeUpCallListSerializer, WakeUpCallExecutionSerializer,
    WakeUpCallStatusUpdateSerializer, WakeUpCallScheduleUpdateSerializer,
    WakeUpCallContactMethodUpdateSerializer
)
from .tasks import update_next_execution_time, execute_wakeup_call
from weather.services import weather_service
from django.utils import timezone

logger = logging.getLogger(__name__)


class WakeUpCallListCreateView(generics.ListCreateAPIView):
    """API view for listing and creating wake-up calls."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WakeUpCallListSerializer
        return WakeUpCallSerializer
    
    def get_queryset(self):
        return WakeUpCall.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        wakeup_call = serializer.save(user=self.request.user)
        # Calculate next execution time
        update_next_execution_time(wakeup_call)


class WakeUpCallDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting wake-up calls.
    
    Supports:
    - GET /api/wakeup-calls/{id}/     - Retrieve wake-up call
    - PUT /api/wakeup-calls/{id}/     - Full update
    - PATCH /api/wakeup-calls/{id}/   - Partial update (recommended)
    - DELETE /api/wakeup-calls/{id}/  - Delete wake-up call
    
    Examples:
    - PATCH /api/wakeup-calls/23/ {"status": "cancelled"}
    - PATCH /api/wakeup-calls/23/ {"scheduled_time": "07:00:00"}
    - PATCH /api/wakeup-calls/23/ {"contact_method": "sms"}
    """
    
    serializer_class = WakeUpCallSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WakeUpCall.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Override to provide better response messages for common updates."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_status = instance.status
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Perform the update
        updated_instance = serializer.save()
        
        # Create a helpful response message
        response_data = serializer.data
        
        # Add helpful message for status changes
        if 'status' in request.data and old_status != updated_instance.status:
            response_data['message'] = f'Wake-up call status updated from {old_status} to {updated_instance.status}'
        
        # Add helpful message for other common updates
        elif 'scheduled_time' in request.data:
            response_data['message'] = f'Wake-up call time updated to {updated_instance.scheduled_time}'
        elif 'contact_method' in request.data:
            response_data['message'] = f'Contact method updated to {updated_instance.contact_method}'
        
        return Response(response_data)


@api_view(['POST'])
def update_wakeup_call_status(request, pk):
    """
    DEPRECATED: Use PATCH /api/wakeup-calls/{id}/ instead.
    
    This endpoint is maintained for backward compatibility but will be removed.
    Use: PATCH /api/wakeup-calls/{id}/ {"status": "cancelled"}
    """
    
    wakeup_call = get_object_or_404(WakeUpCall, pk=pk, user=request.user)
    serializer = WakeUpCallStatusUpdateSerializer(data=request.data)
    
    if serializer.is_valid():
        new_status = serializer.validated_data['status']
        old_status = wakeup_call.status
        
        wakeup_call.status = new_status
        wakeup_call.save()
        
        # Recalculate next execution if reactivating
        if old_status != 'active' and new_status == 'active':
            update_next_execution_time(wakeup_call)
        
        return Response({
            'message': f'Wake-up call status updated to {new_status}',
            'status': new_status,
            'deprecated': True,
            'use_instead': f'PATCH /api/wakeup-calls/{pk}/ {{"status": "{new_status}"}}'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def update_wakeup_call_schedule(request, pk):
    """Web view to update wake-up call schedule from HTML form."""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    wakeup_call = get_object_or_404(WakeUpCall, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            # Get form data
            scheduled_time = request.POST.get('scheduled_time')
            frequency = request.POST.get('frequency')
            
            # Update the wake-up call
            if scheduled_time:
                from datetime import datetime
                wakeup_call.scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
            
            if frequency:
                wakeup_call.frequency = frequency
            
            wakeup_call.save()
            
            # Recalculate next execution time
            update_next_execution_time(wakeup_call)
            
            messages.success(request, f'Schedule updated successfully! Next execution: {wakeup_call.next_execution}')
            
        except Exception as e:
            messages.error(request, f'Error updating schedule: {str(e)}')
    
    return redirect('web:wakeup_call_detail', pk=pk)


@api_view(['POST'])
def update_wakeup_call_contact_method(request, pk):
    """Web view to update wake-up call contact method from HTML form."""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    wakeup_call = get_object_or_404(WakeUpCall, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            # Get form data
            contact_method = request.POST.get('contact_method')
            phone_number = request.POST.get('phone_number')
            
            # Update the wake-up call
            if contact_method:
                wakeup_call.contact_method = contact_method
            
            if phone_number:
                wakeup_call.phone_number = phone_number
            
            wakeup_call.save()
            
            method_name = 'Voice Call' if contact_method == 'call' else 'SMS Message'
            messages.success(request, f'Contact method updated to {method_name} at {phone_number}')
            
        except Exception as e:
            messages.error(request, f'Error updating contact method: {str(e)}')
    
    return redirect('web:wakeup_call_detail', pk=pk)


class WakeUpCallExecutionListView(generics.ListAPIView):
    """API view for listing wake-up call executions."""
    
    serializer_class = WakeUpCallExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        wakeup_call_id = self.kwargs.get('wakeup_call_id')
        if wakeup_call_id:
            # Get executions for a specific wake-up call
            return WakeUpCallExecution.objects.filter(
                wakeup_call_id=wakeup_call_id,
                wakeup_call__user=self.request.user
            ).order_by('-scheduled_for')
        else:
            # Get all executions for the user
            return WakeUpCallExecution.objects.filter(
                wakeup_call__user=self.request.user
            ).order_by('-scheduled_for')


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def twiml_wakeup_call(request, execution_id):
    """
    TwiML endpoint for wake-up call content.
    This endpoint generates the voice content for Twilio calls.
    """
    try:
        execution = get_object_or_404(WakeUpCallExecution, id=execution_id)
        wakeup_call = execution.wakeup_call
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Greeting (different for snooze calls)
        if getattr(execution, 'is_snooze', False):
            greeting = "Rise and shine! This is your snooze wake-up call from Vamshi."
        else:
            greeting = "Good morning! This is your wake-up call from Vamshi."
        response.say(greeting, voice='alice')
        
        # Add weather information if available
        if execution.weather_data:
            try:
                weather_message = weather_service.get_formatted_weather_announcement(
                    wakeup_call.get_weather_zip_code()
                )
                response.say(weather_message, voice='alice')
            except Exception as e:
                logger.error(f"Error generating weather announcement: {e}")
                response.say("Weather information is currently unavailable.", voice='alice')
        
        # Add custom message if provided
        if wakeup_call.custom_message:
            response.say(wakeup_call.custom_message, voice='alice')
        
        # Add interactive menu
        gather = response.gather(
            input='dtmf speech',
            timeout=10,
            num_digits=1,
            action=f'/api/wakeup-calls/twiml/{execution_id}/response/',
            method='POST'
        )
        
        gather.say(
            "Press 1 to snooze for 10 minutes, press 2 to cancel future calls, "
            "or say 'reschedule' to change your wake-up time. Press any other key to end this call.",
            voice='alice'
        )
        
        # If no input, end the call
        response.say("Have a great day!", voice='alice')
        
        return HttpResponse(str(response), content_type='text/xml')
        
    except Exception as e:
        logger.error(f"Error generating TwiML for execution {execution_id}: {e}")
        
        # Fallback TwiML
        response = VoiceResponse()
        response.say("Good morning! This is your wake-up call from Vamshi. Have a great day!", voice='alice')
        return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def twiml_wakeup_call_response(request, execution_id):
    """
    TwiML endpoint for handling user responses during wake-up calls.
    """
    try:
        execution = get_object_or_404(WakeUpCallExecution, id=execution_id)
        wakeup_call = execution.wakeup_call
        
        # Get user input
        digits = request.POST.get('Digits', '')
        speech_result = request.POST.get('SpeechResult', '').lower()
        
        response = VoiceResponse()
        
        # Store user response
        execution.user_response = digits or speech_result
        execution.interaction_data = dict(request.POST)
        execution.save()
        
        if digits == '1':
            # Snooze for 10 minutes
            response.say("Snoozing for 10 minutes. Sweet dreams!", voice='alice')
            
            # Schedule a snooze call in 10 minutes
            from .tasks import schedule_snooze_call
            snooze_time = timezone.now() + timedelta(minutes=10)
            schedule_snooze_call.delay(execution.id, snooze_time.isoformat())
            
            # Log the snooze action
            execution.user_response = f"{execution.user_response} (snoozed for 10 min)"
            execution.save()
            
            logger.info(f"Snooze scheduled for execution {execution.id} at {snooze_time}")
            
        elif digits == '2':
            # Cancel future calls
            response.say("All future wake-up calls have been cancelled.", voice='alice')
            wakeup_call.status = 'cancelled'
            wakeup_call.save()
            
        elif 'reschedule' in speech_result:
            # Reschedule request
            response.say(
                "To reschedule your wake-up calls, please use the Vamshi app or website. "
                "Your current schedule remains unchanged.",
                voice='alice'
            )
            
        else:
            # Default response
            response.say("Thank you! Have a wonderful day!", voice='alice')
        
        return HttpResponse(str(response), content_type='text/xml')
        
    except Exception as e:
        logger.error(f"Error handling TwiML response for execution {execution_id}: {e}")
        
        # Fallback response
        response = VoiceResponse()
        response.say("Thank you! Have a great day!", voice='alice')
        return HttpResponse(str(response), content_type='text/xml')


@api_view(['GET'])
def wakeup_call_stats(request):
    """API view to get wake-up call statistics for the user."""
    
    user_calls = WakeUpCall.objects.filter(user=request.user)
    user_executions = WakeUpCallExecution.objects.filter(wakeup_call__user=request.user)
    
    stats = {
        'total_wakeup_calls': user_calls.count(),
        'active_wakeup_calls': user_calls.filter(status='active').count(),
        'paused_wakeup_calls': user_calls.filter(status='paused').count(),
        'total_executions': user_executions.count(),
        'successful_executions': user_executions.filter(status='completed').count(),
        'failed_executions': user_executions.filter(status='failed').count(),
        'recent_executions': WakeUpCallExecutionSerializer(
            user_executions.order_by('-executed_at')[:5], many=True
        ).data
    }
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_wakeup_call_now(request, pk):
    """
    Test a wake-up call immediately - sends SMS/call right now for testing.
    """
    try:
        wakeup_call = get_object_or_404(WakeUpCall, pk=pk, user=request.user)
        
        # Create a test execution record
        now = timezone.now()
        execution = WakeUpCallExecution.objects.create(
            wakeup_call=wakeup_call,
            scheduled_for=now,  # Required field
            executed_at=now,
            status='pending'
        )
        
        # Queue the execution task immediately
        execute_wakeup_call.delay(execution.id)
        
        logger.info(f"Test execution queued for wake-up call {wakeup_call.id} by user {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Test wake-up call queued successfully! Check your phone in a few seconds.',
            'execution_id': execution.id,
            'phone_number': str(wakeup_call.phone_number),
            'contact_method': wakeup_call.contact_method
        }, status=status.HTTP_200_OK)
        
    except WakeUpCall.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Wake-up call not found or you do not have permission to test it.'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error testing wake-up call {pk}: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to queue test call: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_sms_now(request, pk):
    """
    Send a test SMS immediately - bypasses voice call for faster testing.
    """
    try:
        wakeup_call = get_object_or_404(WakeUpCall, pk=pk, user=request.user)
        
        # Import here to avoid circular imports
        from notifications.services import twilio_service
        from weather.services import weather_service
        
        # Get weather information if requested
        weather_message = ""
        if wakeup_call.include_weather:
            zip_code = wakeup_call.get_weather_zip_code()
            if zip_code:
                weather_message = weather_service.get_formatted_weather_announcement(zip_code)
            else:
                weather_message = "Weather information is not available."
        
        # Prepare the test message
        greeting = "🧪 TEST: Good morning! This is your wake-up call from Vamshi."
        custom_msg = wakeup_call.custom_message or ""
        full_message = f"{greeting} {weather_message} {custom_msg}".strip()
        
        # Send SMS directly
        result = twilio_service.send_sms(
            to_phone=str(wakeup_call.phone_number),
            message=full_message,
            user=request.user,
            is_demo=False  # Force real SMS for testing
        )
        
        if result['success']:
            # Create execution record
            now = timezone.now()
            execution = WakeUpCallExecution.objects.create(
                wakeup_call=wakeup_call,
                scheduled_for=now,  # Required field
                executed_at=now,
                status='completed',
                twilio_sid=result['sid'],
                twilio_status=result['status']
            )
            
            logger.info(f"Test SMS sent successfully for wake-up call {wakeup_call.id}: {result['sid']}")
            
            return Response({
                'success': True,
                'message': f'✅ Test SMS sent successfully! Check your phone.',
                'twilio_sid': result['sid'],
                'phone_number': str(wakeup_call.phone_number),
                'execution_id': execution.id
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Failed to send test SMS for wake-up call {wakeup_call.id}: {result.get('error')}")
            return Response({
                'success': False,
                'error': f"Failed to send SMS: {result.get('error', 'Unknown error')}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except WakeUpCall.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Wake-up call not found or you do not have permission to test it.'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error sending test SMS for wake-up call {pk}: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to send test SMS: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)