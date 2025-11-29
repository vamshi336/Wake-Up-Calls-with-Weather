"""
Twilio service for handling phone calls and SMS messages.
"""

import logging
from typing import Optional, Dict, Any
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from .models import NotificationLog
import requests
import base64

logger = logging.getLogger(__name__)


class TwilioService:
    """Service class for Twilio integration."""
    
    def __init__(self):
        self.client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        else:
            logger.warning("Twilio credentials not configured")
    
    def send_sms(self, to_phone: str, message: str, user=None, is_demo: bool = False) -> Dict[str, Any]:
        """
        Send an SMS message via Twilio.
        
        Args:
            to_phone: Recipient phone number
            message: Message content
            user: User object (optional)
            is_demo: Whether this is a demo message (won't actually send)
            
        Returns:
            Dict with success status and message details
        """
        # Create notification log entry
        notification_log = NotificationLog.objects.create(
            user=user,
            notification_type='wakeup_sms',
            recipient_phone=to_phone,
            message_content=message,
            is_demo=is_demo,
            status='pending'
        )
        
        if is_demo or settings.DEMO_MODE:
            logger.info(f"DEMO SMS to {to_phone}: {message}")
            notification_log.status = 'sent'
            notification_log.twilio_sid = f'demo_sms_{notification_log.id}'
            notification_log.save()
            
            return {
                'success': True,
                'sid': notification_log.twilio_sid,
                'status': 'sent',
                'message': 'Demo SMS logged successfully'
            }
        
        if not self.client:
            error_msg = "Twilio client not configured"
            logger.error(error_msg)
            notification_log.status = 'failed'
            notification_log.twilio_error_message = error_msg
            notification_log.save()
            
            return {
                'success': False,
                'error': error_msg
            }
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_phone
            )
            
            # Update notification log
            notification_log.twilio_sid = message_obj.sid
            notification_log.twilio_status = message_obj.status
            notification_log.status = 'sent'
            notification_log.save()
            
            logger.info(f"SMS sent successfully to {to_phone}, SID: {message_obj.sid}")
            
            return {
                'success': True,
                'sid': message_obj.sid,
                'status': message_obj.status,
                'message': 'SMS sent successfully'
            }
            
        except TwilioException as e:
            error_msg = f"Twilio error: {str(e)}"
            logger.error(f"Failed to send SMS to {to_phone}: {error_msg}")
            
            notification_log.status = 'failed'
            notification_log.twilio_error_message = error_msg
            notification_log.save()
            
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to send SMS to {to_phone}: {error_msg}")
            
            notification_log.status = 'failed'
            notification_log.twilio_error_message = error_msg
            notification_log.save()
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def make_call(self, to_phone: str, twiml_url: str, user=None, is_demo: bool = False) -> Dict[str, Any]:
        """
        Make a phone call via Twilio.
        
        Args:
            to_phone: Recipient phone number
            twiml_url: URL that returns TwiML for the call
            user: User object (optional)
            is_demo: Whether this is a demo call (won't actually make)
            
        Returns:
            Dict with success status and call details
        """
        # Create notification log entry
        notification_log = NotificationLog.objects.create(
            user=user,
            notification_type='wakeup_call',
            recipient_phone=to_phone,
            is_demo=is_demo,
            status='pending'
        )
        
        if is_demo or settings.DEMO_MODE:
            logger.info(f"DEMO CALL to {to_phone} with TwiML URL: {twiml_url}")
            notification_log.status = 'sent'
            notification_log.twilio_sid = f'demo_call_{notification_log.id}'
            notification_log.save()
            
            return {
                'success': True,
                'sid': notification_log.twilio_sid,
                'status': 'initiated',
                'message': 'Demo call logged successfully'
            }
        
        if not self.client:
            error_msg = "Twilio client not configured"
            logger.error(error_msg)
            notification_log.status = 'failed'
            notification_log.twilio_error_message = error_msg
            notification_log.save()
            
            return {
                'success': False,
                'error': error_msg
            }
        
        try:
            call = self.client.calls.create(
                url=twiml_url,
                to=to_phone,
                from_=settings.TWILIO_PHONE_NUMBER,
                method='POST'
            )
            
            # Update notification log
            notification_log.twilio_sid = call.sid
            notification_log.twilio_status = call.status
            notification_log.status = 'sent'
            notification_log.save()
            
            logger.info(f"Call initiated successfully to {to_phone}, SID: {call.sid}")
            
            return {
                'success': True,
                'sid': call.sid,
                'status': call.status,
                'message': 'Call initiated successfully'
            }
            
        except TwilioException as e:
            error_msg = f"Twilio error: {str(e)}"
            logger.error(f"Failed to make call to {to_phone}: {error_msg}")
            
            notification_log.status = 'failed'
            notification_log.twilio_error_message = error_msg
            notification_log.save()
            
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to make call to {to_phone}: {error_msg}")
            
            notification_log.status = 'failed'
            notification_log.twilio_error_message = error_msg
            notification_log.save()
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def send_verification_sms(self, to_phone: str, verification_code: str, user=None) -> Dict[str, Any]:
        """
        Send a phone verification SMS.
        
        Args:
            to_phone: Phone number to verify
            verification_code: 6-digit verification code
            user: User object (optional)
            
        Returns:
            Dict with success status and message details
        """
        message = f"Your Vamshi Wake-up Calls verification code is: {verification_code}. This code expires in 10 minutes."
        
        # Create notification log entry
        notification_log = NotificationLog.objects.create(
            user=user,
            notification_type='verification_sms',
            recipient_phone=to_phone,
            message_content=message,
            status='pending'
        )
        
        if settings.DEMO_MODE:
            logger.info(f"DEMO VERIFICATION SMS to {to_phone}: {verification_code}")
            notification_log.status = 'sent'
            notification_log.twilio_sid = f'demo_verification_{notification_log.id}'
            notification_log.save()
            
            return {
                'success': True,
                'sid': notification_log.twilio_sid,
                'status': 'sent',
                'message': 'Demo verification SMS logged successfully'
            }
        
        return self.send_sms(to_phone, message, user, is_demo=False)
    
    def auto_verify_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Automatically verify a phone number in Twilio for trial accounts.
        This uses Twilio's Verification API to add numbers to verified list.
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not configured'
            }
        
        try:
            # Use Twilio's Verification Service to verify the number
            # This will send a verification code to the number
            verification = self.client.verify \
                .services(settings.TWILIO_VERIFY_SERVICE_SID if hasattr(settings, 'TWILIO_VERIFY_SERVICE_SID') else None) \
                .verifications \
                .create(to=phone_number, channel='sms')
            
            logger.info(f"Verification initiated for {phone_number}: {verification.sid}")
            
            return {
                'success': True,
                'verification_sid': verification.sid,
                'status': verification.status,
                'message': f'Verification code sent to {phone_number}'
            }
            
        except TwilioException as e:
            # If verification service fails, try adding to verified caller IDs
            return self._add_to_verified_caller_ids(phone_number)
        except Exception as e:
            logger.error(f"Error auto-verifying {phone_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _add_to_verified_caller_ids(self, phone_number: str) -> Dict[str, Any]:
        """
        Add phone number to Twilio verified caller IDs using REST API.
        This is for trial accounts to bypass verification restrictions.
        """
        try:
            # Create verification via Twilio REST API
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/OutgoingCallerIds.json"
            
            auth = base64.b64encode(f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'PhoneNumber': phone_number,
                'FriendlyName': f'Auto-verified {phone_number}'
            }
            
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Successfully added {phone_number} to verified caller IDs")
                return {
                    'success': True,
                    'caller_id_sid': result.get('sid'),
                    'message': f'Phone number {phone_number} added to verified list'
                }
            else:
                logger.error(f"Failed to add {phone_number} to verified caller IDs: {response.text}")
                return {
                    'success': False,
                    'error': f'Twilio API error: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Error adding {phone_number} to verified caller IDs: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_if_number_verified(self, phone_number: str) -> bool:
        """
        Check if a phone number is already verified in Twilio.
        """
        if not self.client:
            return False
        
        try:
            # Get list of verified caller IDs
            caller_ids = self.client.outgoing_caller_ids.list()
            
            for caller_id in caller_ids:
                if caller_id.phone_number == phone_number:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking verification status for {phone_number}: {e}")
            return False


# Global service instance
twilio_service = TwilioService()
