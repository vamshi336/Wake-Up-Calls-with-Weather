"""
Web views for the user interface.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from wakeup_calls.models import WakeUpCall, WakeUpCallExecution
from wakeup_calls.tasks import update_next_execution_time
from notifications.models import NotificationLog
from notifications.services import twilio_service
from accounts.services import phone_verification_service
import json

User = get_user_model()


def home(request):
    """Home page view."""
    if request.user.is_authenticated:
        return redirect('web:user_dashboard')
    
    return render(request, 'web/home.html')


def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        # Handle registration form
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        zip_code = request.POST.get('zip_code', '')
        
        # Use email as username if username is empty
        if not username:
            username = email
            
        # Basic validation
        if not all([email, password, password_confirm]):
            messages.error(request, 'Email and password are required.')
            return render(request, 'web/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'web/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'web/register.html')
        
        # Create user
        try:
            # Set username to email for consistency with email-based login
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number or None,
                zip_code=zip_code or None,
                timezone=request.POST.get('timezone', 'UTC')  # User-selected timezone
            )
            
            # Log the user in automatically after registration
            login(request, user)
            
            # Enhanced welcome message
            name = user.first_name if user.first_name else user.email.split('@')[0]
            messages.success(
                request, 
                f'🎉 Welcome to Vamshi Wake-up Calls, {name}! Your account has been created and you are now logged in.'
            )
            
            # Add helpful next steps message
            if not user.phone_number:
                messages.info(
                    request,
                    '📱 Next step: Add and verify your phone number to start receiving wake-up calls!'
                )
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'User {user.email} registered and logged in successfully. Redirecting to dashboard.')
            
            return redirect('web:user_dashboard')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Registration error: {str(e)}')
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'web/register.html')


def login_view(request):
    """User login view."""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'web/login.html')
        
        user = authenticate(request, username=email, password=password)
        
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('web:user_dashboard')
        else:
            # Debug: Check if user exists
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                existing_user = User.objects.get(email=email)
                messages.error(request, 'Invalid password. Please check your password.')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    
    return render(request, 'web/login.html')


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('web:home')


# Old dashboard function removed - now using dashboard_views.main_dashboard


@login_required
def wakeup_calls_list(request):
    """List all user's wake-up calls."""
    wakeup_calls = WakeUpCall.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'wakeup_calls': wakeup_calls,
    }
    
    return render(request, 'web/wakeup_calls_list.html', context)


@login_required
def wakeup_call_detail(request, pk):
    """View details of a specific wake-up call."""
    wakeup_call = get_object_or_404(WakeUpCall, pk=pk, user=request.user)
    
    # Get executions for this call
    executions = WakeUpCallExecution.objects.filter(
        wakeup_call=wakeup_call
    ).order_by('-executed_at')[:10]
    
    context = {
        'wakeup_call': wakeup_call,
        'executions': executions,
    }
    
    return render(request, 'web/wakeup_call_detail.html', context)


@login_required
def create_wakeup_call(request):
    """Create a new wake-up call."""
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        contact_method = request.POST.get('contact_method')
        scheduled_time = request.POST.get('scheduled_time')
        frequency = request.POST.get('frequency')
        include_weather = request.POST.get('include_weather') == 'on'
        custom_message = request.POST.get('custom_message', '')
        
        # Basic validation
        if not all([name, phone_number, contact_method, scheduled_time, frequency]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'web/create_wakeup_call.html')
        
        try:
            # Create wake-up call
            wakeup_call = WakeUpCall.objects.create(
                user=request.user,
                name=name,
                phone_number=phone_number,
                contact_method=contact_method,
                scheduled_time=scheduled_time,
                frequency=frequency,
                include_weather=include_weather,
                weather_zip_code=request.user.zip_code,
                custom_message=custom_message,
                is_demo=False  # Real wake-up calls
            )
            
            messages.success(request, f'Wake-up call "{name}" created successfully!')
            return redirect('web:wakeup_call_detail', pk=wakeup_call.pk)
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'web/create_wakeup_call.html')


@login_required
def profile_view(request):
    """User profile view."""
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone_number = request.POST.get('phone_number') or None
        user.zip_code = request.POST.get('zip_code', '')
        user.timezone = request.POST.get('timezone', 'UTC')
        
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('web:profile')
    
    return render(request, 'web/profile.html')


@login_required
@require_POST
def change_password_web(request):
    """Web view to change password from HTML form."""
    old_password = request.POST.get('old_password')
    new_password = request.POST.get('new_password')
    new_password_confirm = request.POST.get('new_password_confirm')
    
    # Validation
    if not all([old_password, new_password, new_password_confirm]):
        messages.error(request, 'All password fields are required.')
        return redirect('web:profile')
    
    if new_password != new_password_confirm:
        messages.error(request, 'New passwords do not match.')
        return redirect('web:profile')
    
    if len(new_password) < 8:
        messages.error(request, 'New password must be at least 8 characters long.')
        return redirect('web:profile')
    
    # Check old password
    user = request.user
    if not user.check_password(old_password):
        messages.error(request, 'Current password is incorrect.')
        return redirect('web:profile')
    
    # Set new password
    try:
        user.set_password(new_password)
        user.save()
        
        # Update session with new password hash to keep user logged in
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Password changed successfully!')
    except Exception as e:
        messages.error(request, f'Error changing password: {str(e)}')
    
    return redirect('web:profile')


@login_required
def verify_phone(request):
    """Phone verification view."""
    if request.method == 'POST':
        action = request.POST.get('action')
        phone_number = request.POST.get('phone_number')
        
        if action == 'send_code':
            if phone_number:
                result = phone_verification_service.send_verification_code(
                    user=request.user,
                    phone_number=phone_number
                )
                
                if result['success']:
                    messages.success(request, result['message'])
                else:
                    messages.error(request, result['error'])
            else:
                messages.error(request, 'Phone number is required.')
        
        elif action == 'verify_code':
            verification_code = request.POST.get('verification_code')
            
            if phone_number and verification_code:
                result = phone_verification_service.verify_code(
                    user=request.user,
                    phone_number=phone_number,
                    code=verification_code
                )
                
                if result['success']:
                    messages.success(request, result['message'])
                    return redirect('web:profile')
                else:
                    messages.error(request, result['error'])
            else:
                messages.error(request, 'Phone number and verification code are required.')
    
    return render(request, 'web/verify_phone.html')


@login_required
@require_POST
def update_wakeup_call_status(request, call_id):
    """Update wake-up call status via AJAX."""
    try:
        # Get the wake-up call
        wakeup_call = get_object_or_404(WakeUpCall, id=call_id, user=request.user)
        
        # Get the new status from POST data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            new_status = data.get('status')
        else:
            new_status = request.POST.get('status')
        
        # Validate status
        valid_statuses = ['active', 'paused', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=400)
        
        # Update the status
        old_status = wakeup_call.status
        wakeup_call.status = new_status
        wakeup_call.save()
        
        # Update next execution time if status changed to active
        if old_status != 'active' and new_status == 'active':
            update_next_execution_time(wakeup_call)
        elif new_status in ['paused', 'cancelled']:
            wakeup_call.next_execution = None
            wakeup_call.save()
        
        # Return success response
        status_messages = {
            'active': 'Wake-up call activated successfully!',
            'paused': 'Wake-up call paused successfully!',
            'cancelled': 'Wake-up call cancelled successfully!'
        }
        
        return JsonResponse({
            'success': True,
            'message': status_messages.get(new_status, 'Status updated successfully!'),
            'status': new_status,
            'next_execution': wakeup_call.next_execution.isoformat() if wakeup_call.next_execution else None
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def auto_verify_phone_number(request):
    """
    Bypass phone verification for development/trial accounts.
    For production, this should be replaced with proper Twilio verification.
    """
    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return JsonResponse({
                'success': False,
                'error': 'Phone number is required'
            }, status=400)
        
        # Validate phone number format
        if not phone_number.startswith('+'):
            return JsonResponse({
                'success': False,
                'error': 'Phone number must include country code (e.g., +1 for US, +91 for India)'
            }, status=400)
        
        # For trial accounts, we'll bypass Twilio verification
        # and mark the number as verified in our system
        user = request.user
        user.phone_number = phone_number
        user.phone_verified = True
        user.save()
        
        # Create a verification record for logging
        from accounts.models import PhoneVerification
        from django.utils import timezone
        
        PhoneVerification.objects.create(
            user=user,
            phone_number=phone_number,
            verification_code='BYPASS',
            is_verified=True,
            attempts=0,
            expires_at=timezone.now() + timezone.timedelta(days=365)  # Long expiry for bypass
        )
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Phone number {phone_number} verified for development/testing!',
            'note': 'This is a development bypass. For production, upgrade your Twilio account.',
            'bypass_mode': True
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)