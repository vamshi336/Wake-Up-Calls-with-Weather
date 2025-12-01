"""
API views for the accounts app.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer,
    PhoneVerificationRequestSerializer, PhoneVerificationCodeSerializer,
    PasswordChangeSerializer
)
from .services import phone_verification_service

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """API view for user registration."""
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create auth token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """API view for user login."""
    
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    user = authenticate(username=email, password=password)
    
    if user:
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        })
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_view(request):
    """API view for user logout."""
    
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout successful'
        })
    except:
        return Response({
            'error': 'Error logging out'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API view for user profile management."""
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['POST'])
def request_phone_verification(request):
    """API view to request phone number verification."""
    
    serializer = PhoneVerificationRequestSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        
        result = phone_verification_service.send_verification_code(
            user=request.user,
            phone_number=phone_number
        )
        
        if result['success']:
            return Response({
                'message': result['message'],
                'expires_in_minutes': result['expires_in_minutes']
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_phone_code(request):
    """API view to verify phone number with code."""
    
    serializer = PhoneVerificationCodeSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['verification_code']
        
        result = phone_verification_service.verify_code(
            user=request.user,
            phone_number=phone_number,
            code=code
        )
        
        if result['success']:
            return Response({
                'message': result['message']
            })
        else:
            return Response({
                'error': result['error'],
                'remaining_attempts': result.get('remaining_attempts')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_verification_code(request):
    """API view to resend phone verification code."""
    
    serializer = PhoneVerificationRequestSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        
        result = phone_verification_service.resend_verification_code(
            user=request.user,
            phone_number=phone_number
        )
        
        if result['success']:
            return Response({
                'message': result['message'],
                'expires_in_minutes': result['expires_in_minutes']
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def phone_verification_status(request):
    """API view to get phone verification status."""
    
    phone_number = request.query_params.get('phone_number')
    if not phone_number:
        return Response({
            'error': 'Phone number parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    result = phone_verification_service.get_verification_status(
        user=request.user,
        phone_number=phone_number
    )
    
    return Response(result)


@api_view(['POST'])
def change_password(request):
    """API view to change user password."""
    
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Delete all existing tokens to force re-login
        Token.objects.filter(user=user).delete()
        
        return Response({
            'message': 'Password changed successfully. Please log in again.'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)