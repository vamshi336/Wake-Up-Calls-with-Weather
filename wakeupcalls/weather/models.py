from django.db import models
from django.utils import timezone


class WeatherCache(models.Model):
    """Model to cache weather data to reduce API calls."""
    
    zip_code = models.CharField(max_length=10, db_index=True)
    weather_data = models.JSONField()
    
    # Cache metadata
    cached_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-cached_at']
        indexes = [
            models.Index(fields=['zip_code', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Weather for {self.zip_code} - {self.cached_at}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def get_temperature_fahrenheit(self):
        """Extract temperature in Fahrenheit from cached data."""
        try:
            return self.weather_data.get('main', {}).get('temp')
        except (KeyError, AttributeError):
            return None
    
    def get_description(self):
        """Extract weather description from cached data."""
        try:
            weather = self.weather_data.get('weather', [])
            if weather:
                return weather[0].get('description', '').title()
        except (KeyError, AttributeError, IndexError):
            return None
    
    def get_formatted_weather(self):
        """Get a formatted weather string for announcements."""
        temp = self.get_temperature_fahrenheit()
        description = self.get_description()
        
        if temp and description:
            return f"The current weather is {description} with a temperature of {int(temp)} degrees Fahrenheit."
        elif temp:
            return f"The current temperature is {int(temp)} degrees Fahrenheit."
        elif description:
            return f"The current weather is {description}."
        else:
            return "Weather information is currently unavailable."


class WeatherAPILog(models.Model):
    """Model to log weather API requests for monitoring and debugging."""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('rate_limited', 'Rate Limited'),
    ]
    
    zip_code = models.CharField(max_length=10)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    response_data = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    response_time_ms = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Weather API {self.status} for {self.zip_code} - {self.created_at}"
