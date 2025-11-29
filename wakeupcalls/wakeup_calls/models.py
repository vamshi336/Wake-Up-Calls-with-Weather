from django.db import models
from django.conf import settings
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class WakeUpCall(models.Model):
    """Model representing a scheduled wake-up call."""
    
    CONTACT_METHOD_CHOICES = [
        ('call', 'Phone Call'),
        ('sms', 'Text Message'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    FREQUENCY_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('weekdays', 'Weekdays Only'),
        ('weekends', 'Weekends Only'),
        ('custom', 'Custom'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wakeup_calls')
    name = models.CharField(max_length=100, help_text="Name for this wake-up call")
    phone_number = PhoneNumberField(help_text="Phone number to call/text")
    contact_method = models.CharField(max_length=10, choices=CONTACT_METHOD_CHOICES, default='call')
    
    # Scheduling
    scheduled_time = models.TimeField(help_text="Time to make the wake-up call")
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='once')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    
    # Custom frequency (for weekly patterns)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    # Settings
    include_weather = models.BooleanField(default=True)
    weather_zip_code = models.CharField(max_length=10, blank=True, null=True)
    custom_message = models.TextField(blank=True, null=True, help_text="Custom message to include")
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_demo = models.BooleanField(default=False, help_text="Demo calls won't actually be made")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_executed = models.DateTimeField(blank=True, null=True)
    next_execution = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['next_execution', 'scheduled_time']
    
    def __str__(self):
        return f"{self.name} - {self.user.email} - {self.scheduled_time}"
    
    def get_weather_zip_code(self):
        """Get the zip code to use for weather (call-specific or user default)."""
        return self.weather_zip_code or self.user.zip_code
    
    def should_execute_today(self):
        """Check if this wake-up call should execute today based on frequency."""
        today = timezone.now().date()
        weekday = today.weekday()  # 0=Monday, 6=Sunday
        
        if self.frequency == 'once':
            return today == self.start_date
        elif self.frequency == 'daily':
            return True
        elif self.frequency == 'weekly':
            return (today - self.start_date).days % 7 == 0
        elif self.frequency == 'weekdays':
            return weekday < 5  # Monday-Friday
        elif self.frequency == 'weekends':
            return weekday >= 5  # Saturday-Sunday
        elif self.frequency == 'custom':
            day_mapping = [
                self.monday, self.tuesday, self.wednesday, self.thursday,
                self.friday, self.saturday, self.sunday
            ]
            return day_mapping[weekday]
        
        return False


class WakeUpCallExecution(models.Model):
    """Model to track individual executions of wake-up calls."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    wakeup_call = models.ForeignKey(WakeUpCall, on_delete=models.CASCADE, related_name='executions')
    scheduled_for = models.DateTimeField()
    executed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Twilio response data
    twilio_sid = models.CharField(max_length=100, blank=True, null=True)
    twilio_status = models.CharField(max_length=50, blank=True, null=True)
    
    # Weather data included
    weather_data = models.JSONField(blank=True, null=True)
    
    # Error information
    error_message = models.TextField(blank=True, null=True)
    
    # User interaction (for calls)
    user_response = models.CharField(max_length=20, blank=True, null=True)
    interaction_data = models.JSONField(blank=True, null=True)
    
    # Snooze tracking
    is_snooze = models.BooleanField(default=False, help_text="True if this is a snooze call")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_for']
    
    def __str__(self):
        return f"{self.wakeup_call.name} - {self.scheduled_for} - {self.status}"
