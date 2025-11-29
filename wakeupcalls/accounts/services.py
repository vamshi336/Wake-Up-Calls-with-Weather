"""
Phone verification service for user account management.
"""

import logging
import random
import string
from datetime import timedelta
from typing import Dict, Any, Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from notifications.services import twilio_service
from .models import PhoneVerification

User = get_user_model()
logger = logging.getLogger(__name__)


class PhoneVerificationService:
    """Service for handling phone number verification."""
    
    def __init__(self):
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
    
    def generate_verification_code(self) -> str:
        """Generate a random 6-digit verification code."""
        return ''.join(random.choices(string.digits, k=self.code_length))
    
    def send_verification_code(self, user: User, phone_number: str) -> Dict[str, Any]:
        """
        Send a verification code to the user's phone number.
        
        Args:
            user: User object
            phone_number: Phone number to verify
            
        Returns:
            Dict with success status and details
        """
        # Generate verification code
        verification_code = self.generate_verification_code()
        expires_at = timezone.now() + timedelta(minutes=self.code_expiry_minutes)
        
        # Create or update verification record
        verification, created = PhoneVerification.objects.get_or_create(
            user=user,
            phone_number=phone_number,
            defaults={
                'verification_code': verification_code,
                'expires_at': expires_at,
                'attempts': 0
            }
        )
        
        if not created:
            # Update existing verification
            verification.verification_code = verification_code
            verification.expires_at = expires_at
            verification.attempts = 0
            verification.is_verified = False
            verification.save()
        
        # Send SMS with verification code
        sms_result = twilio_service.send_verification_sms(
            to_phone=phone_number,
            verification_code=verification_code,
            user=user
        )
        
        if sms_result['success']:
            logger.info(f"Verification code sent to {phone_number} for user {user.email}")
            return {
                'success': True,
                'message': 'Verification code sent successfully',
                'expires_in_minutes': self.code_expiry_minutes
            }
        else:
            logger.error(f"Failed to send verification code to {phone_number}: {sms_result.get('error')}")
            return {
                'success': False,
                'error': sms_result.get('error', 'Failed to send verification code')
            }
    
    def verify_code(self, user: User, phone_number: str, code: str) -> Dict[str, Any]:
        """
        Verify a phone number using the provided code.
        
        Args:
            user: User object
            phone_number: Phone number being verified
            code: Verification code provided by user
            
        Returns:
            Dict with verification result
        """
        try:
            verification = PhoneVerification.objects.get(
                user=user,
                phone_number=phone_number,
                is_verified=False
            )
        except PhoneVerification.DoesNotExist:
            logger.warning(f"No verification record found for {phone_number} and user {user.email}")
            return {
                'success': False,
                'error': 'No verification code found. Please request a new code.'
            }
        
        # Check if code has expired
        if timezone.now() > verification.expires_at:
            logger.info(f"Verification code expired for {phone_number}")
            return {
                'success': False,
                'error': 'Verification code has expired. Please request a new code.'
            }
        
        # Check attempt limit
        if verification.attempts >= self.max_attempts:
            logger.warning(f"Max verification attempts exceeded for {phone_number}")
            return {
                'success': False,
                'error': 'Maximum verification attempts exceeded. Please request a new code.'
            }
        
        # Increment attempt counter
        verification.attempts += 1
        verification.save()
        
        # Verify the code
        if verification.verification_code == code:
            # Mark as verified
            verification.is_verified = True
            verification.save()
            
            # Update user's phone verification status
            user.phone_number = phone_number
            user.phone_verified = True
            user.save()
            
            logger.info(f"Phone number {phone_number} successfully verified for user {user.email}")
            
            return {
                'success': True,
                'message': 'Phone number verified successfully'
            }
        else:
            remaining_attempts = self.max_attempts - verification.attempts
            logger.info(f"Invalid verification code for {phone_number}. {remaining_attempts} attempts remaining.")
            
            return {
                'success': False,
                'error': f'Invalid verification code. {remaining_attempts} attempts remaining.',
                'remaining_attempts': remaining_attempts
            }
    
    def resend_verification_code(self, user: User, phone_number: str) -> Dict[str, Any]:
        """
        Resend verification code to the user's phone number.
        
        Args:
            user: User object
            phone_number: Phone number to verify
            
        Returns:
            Dict with success status and details
        """
        # Check if there's a recent verification attempt
        recent_verification = PhoneVerification.objects.filter(
            user=user,
            phone_number=phone_number,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).first()
        
        if recent_verification:
            return {
                'success': False,
                'error': 'Please wait at least 1 minute before requesting a new code.'
            }
        
        return self.send_verification_code(user, phone_number)
    
    def get_verification_status(self, user: User, phone_number: str) -> Dict[str, Any]:
        """
        Get the current verification status for a phone number.
        
        Args:
            user: User object
            phone_number: Phone number to check
            
        Returns:
            Dict with verification status details
        """
        try:
            verification = PhoneVerification.objects.filter(
                user=user,
                phone_number=phone_number
            ).order_by('-created_at').first()
            
            if not verification:
                return {
                    'is_verified': False,
                    'has_pending_verification': False
                }
            
            if verification.is_verified:
                return {
                    'is_verified': True,
                    'verified_at': verification.created_at
                }
            
            # Check if there's a pending verification
            if timezone.now() <= verification.expires_at:
                return {
                    'is_verified': False,
                    'has_pending_verification': True,
                    'expires_at': verification.expires_at,
                    'attempts_used': verification.attempts,
                    'max_attempts': self.max_attempts
                }
            else:
                return {
                    'is_verified': False,
                    'has_pending_verification': False,
                    'last_attempt_expired': True
                }
                
        except Exception as e:
            logger.error(f"Error getting verification status for {phone_number}: {e}")
            return {
                'is_verified': False,
                'has_pending_verification': False,
                'error': 'Unable to check verification status'
            }


# Global service instance
phone_verification_service = PhoneVerificationService()
