"""
Serializers for the wakeup_calls app.
"""

from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import WakeUpCall, WakeUpCallExecution


class WakeUpCallSerializer(serializers.ModelSerializer):
    """Serializer for WakeUpCall model."""
    
    phone_number = PhoneNumberField()
    
    class Meta:
        model = WakeUpCall
        fields = [
            'id', 'name', 'phone_number', 'contact_method', 'scheduled_time',
            'frequency', 'start_date', 'end_date', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'include_weather', 'weather_zip_code', 'custom_message',
            'status', 'is_demo', 'created_at', 'updated_at',
            'last_executed', 'next_execution'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_executed', 'next_execution'
        ]
    
    def validate(self, attrs):
        # Validate frequency-specific fields
        frequency = attrs.get('frequency')
        
        if frequency == 'custom':
            # At least one day must be selected for custom frequency
            days = [
                attrs.get('monday', False),
                attrs.get('tuesday', False),
                attrs.get('wednesday', False),
                attrs.get('thursday', False),
                attrs.get('friday', False),
                attrs.get('saturday', False),
                attrs.get('sunday', False),
            ]
            if not any(days):
                raise serializers.ValidationError(
                    "At least one day must be selected for custom frequency"
                )
        
        # Validate end_date
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if end_date and start_date and end_date <= start_date:
            raise serializers.ValidationError(
                "End date must be after start date"
            )
        
        return attrs
    
    def create(self, validated_data):
        # Set the user to the current authenticated user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Enhanced update method with proper status change handling."""
        old_status = instance.status
        
        # Update the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle status changes
        new_status = validated_data.get('status', old_status)
        if old_status != new_status:
            self._handle_status_change(instance, old_status, new_status)
        
        # Recalculate next execution time if schedule changed
        schedule_fields = [
            'scheduled_time', 'frequency', 'start_date', 'end_date',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        ]
        if any(field in validated_data for field in schedule_fields):
            from .tasks import update_next_execution_time
            update_next_execution_time(instance)
        
        return instance
    
    def _handle_status_change(self, instance, old_status, new_status):
        """Handle status change logic."""
        # Recalculate next execution if reactivating
        if old_status != 'active' and new_status == 'active':
            from .tasks import update_next_execution_time
            update_next_execution_time(instance)


class WakeUpCallListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing wake-up calls."""
    
    class Meta:
        model = WakeUpCall
        fields = [
            'id', 'name', 'contact_method', 'scheduled_time', 'frequency',
            'status', 'next_execution', 'last_executed'
        ]


class WakeUpCallExecutionSerializer(serializers.ModelSerializer):
    """Serializer for WakeUpCallExecution model."""
    
    wakeup_call_name = serializers.CharField(source='wakeup_call.name', read_only=True)
    
    class Meta:
        model = WakeUpCallExecution
        fields = [
            'id', 'wakeup_call', 'wakeup_call_name', 'scheduled_for',
            'executed_at', 'status', 'twilio_sid', 'twilio_status',
            'weather_data', 'error_message', 'user_response',
            'interaction_data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'wakeup_call_name', 'executed_at', 'twilio_sid',
            'twilio_status', 'weather_data', 'error_message',
            'user_response', 'interaction_data', 'created_at', 'updated_at'
        ]


class WakeUpCallStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating wake-up call status."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES)


class WakeUpCallScheduleUpdateSerializer(serializers.Serializer):
    """Serializer for updating wake-up call schedule."""
    
    scheduled_time = serializers.TimeField()
    frequency = serializers.ChoiceField(choices=WakeUpCall.FREQUENCY_CHOICES)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    # Custom frequency days
    monday = serializers.BooleanField(required=False)
    tuesday = serializers.BooleanField(required=False)
    wednesday = serializers.BooleanField(required=False)
    thursday = serializers.BooleanField(required=False)
    friday = serializers.BooleanField(required=False)
    saturday = serializers.BooleanField(required=False)
    sunday = serializers.BooleanField(required=False)
    
    def validate(self, attrs):
        frequency = attrs.get('frequency')
        
        if frequency == 'custom':
            # Check if at least one day is selected
            days = [
                attrs.get('monday', False),
                attrs.get('tuesday', False),
                attrs.get('wednesday', False),
                attrs.get('thursday', False),
                attrs.get('friday', False),
                attrs.get('saturday', False),
                attrs.get('sunday', False),
            ]
            if not any(days):
                raise serializers.ValidationError(
                    "At least one day must be selected for custom frequency"
                )
        
        return attrs


class WakeUpCallContactMethodUpdateSerializer(serializers.Serializer):
    """Serializer for updating wake-up call contact method."""
    
    contact_method = serializers.ChoiceField(choices=WakeUpCall.CONTACT_METHOD_CHOICES)
    phone_number = PhoneNumberField(required=False)
    
    def validate(self, attrs):
        # If phone_number is provided, it should be different from current
        if 'phone_number' in attrs and not attrs['phone_number']:
            raise serializers.ValidationError("Phone number cannot be empty")
        return attrs
