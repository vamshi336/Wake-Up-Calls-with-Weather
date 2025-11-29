"""
Weather service for fetching and caching weather data.
"""

import logging
import requests
from datetime import timedelta
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from .models import WeatherCache, WeatherAPILog

logger = logging.getLogger(__name__)


class WeatherService:
    """Service class for weather data integration."""
    
    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = "http://api.weatherapi.com/v1/current.json"
        self.cache_duration_hours = 1  # Cache weather data for 1 hour
    
    def get_weather(self, zip_code: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get weather data for a zip code, using cache when possible.
        
        Args:
            zip_code: ZIP code to get weather for
            force_refresh: Whether to bypass cache and fetch fresh data
            
        Returns:
            Weather data dict or None if unavailable
        """
        if not zip_code:
            logger.warning("No zip code provided for weather lookup")
            return None
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_weather = self._get_cached_weather(zip_code)
            if cached_weather:
                logger.debug(f"Using cached weather data for {zip_code}")
                return cached_weather.weather_data
        
        # Fetch fresh weather data
        return self._fetch_weather_data(zip_code)
    
    def get_formatted_weather_announcement(self, zip_code: str) -> str:
        """
        Get a formatted weather announcement string for wake-up calls.
        
        Args:
            zip_code: ZIP code to get weather for
            
        Returns:
            Formatted weather announcement string
        """
        weather_data = self.get_weather(zip_code)
        
        if not weather_data:
            return "Weather information is currently unavailable."
        
        try:
            current = weather_data.get('current', {})
            temp_f = current.get('temp_f')
            condition = current.get('condition', {}).get('text', '')
            
            if temp_f and condition:
                temp_f = int(temp_f)
                return f"Good morning! The current weather is {condition} with a temperature of {temp_f} degrees Fahrenheit."
            elif temp_f:
                temp_f = int(temp_f)
                return f"Good morning! The current temperature is {temp_f} degrees Fahrenheit."
            else:
                return "Good morning! Weather information is currently unavailable."
                
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Error parsing weather data for {zip_code}: {e}")
            return "Good morning! Weather information is currently unavailable."
    
    def _get_cached_weather(self, zip_code: str) -> Optional[WeatherCache]:
        """Get cached weather data if available and not expired."""
        try:
            cached = WeatherCache.objects.filter(
                zip_code=zip_code,
                expires_at__gt=timezone.now()
            ).first()
            
            return cached
        except Exception as e:
            logger.error(f"Error retrieving cached weather for {zip_code}: {e}")
            return None
    
    def _fetch_weather_data(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch fresh weather data from WeatherAPI.com.
        
        Args:
            zip_code: ZIP code to fetch weather for
            
        Returns:
            Weather data dict or None if fetch failed
        """
        if not self.api_key:
            logger.error("WeatherAPI.com API key not configured")
            return None
        
        # Prepare API request - WeatherAPI.com accepts zip codes in format "zipcode,country"
        params = {
            'key': self.api_key,
            'q': f"{zip_code},US",
            'aqi': 'no'
        }
        
        start_time = timezone.now()
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response_time_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                weather_data = response.json()
                
                # Log successful API call
                WeatherAPILog.objects.create(
                    zip_code=zip_code,
                    status='success',
                    response_data=weather_data,
                    response_time_ms=response_time_ms
                )
                
                # Cache the weather data
                self._cache_weather_data(zip_code, weather_data)
                
                logger.info(f"Successfully fetched weather data for {zip_code}")
                return weather_data
            
            elif response.status_code == 429:
                # Rate limited
                logger.warning(f"Rate limited when fetching weather for {zip_code}")
                WeatherAPILog.objects.create(
                    zip_code=zip_code,
                    status='rate_limited',
                    error_message="API rate limit exceeded",
                    response_time_ms=response_time_ms
                )
                
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(f"Weather API error for {zip_code}: {error_msg}")
                
                WeatherAPILog.objects.create(
                    zip_code=zip_code,
                    status='error',
                    error_message=error_msg,
                    response_time_ms=response_time_ms
                )
        
        except requests.exceptions.Timeout:
            error_msg = "API request timeout"
            logger.error(f"Weather API timeout for {zip_code}")
            
            WeatherAPILog.objects.create(
                zip_code=zip_code,
                status='error',
                error_message=error_msg
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request error: {str(e)}"
            logger.error(f"Weather API request error for {zip_code}: {error_msg}")
            
            WeatherAPILog.objects.create(
                zip_code=zip_code,
                status='error',
                error_message=error_msg
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error fetching weather for {zip_code}: {error_msg}")
            
            WeatherAPILog.objects.create(
                zip_code=zip_code,
                status='error',
                error_message=error_msg
            )
        
        return None
    
    def _cache_weather_data(self, zip_code: str, weather_data: Dict[str, Any]) -> None:
        """
        Cache weather data in the database.
        
        Args:
            zip_code: ZIP code the weather data is for
            weather_data: Weather data to cache
        """
        try:
            expires_at = timezone.now() + timedelta(hours=self.cache_duration_hours)
            
            # Delete old cache entries for this zip code
            WeatherCache.objects.filter(zip_code=zip_code).delete()
            
            # Create new cache entry
            WeatherCache.objects.create(
                zip_code=zip_code,
                weather_data=weather_data,
                expires_at=expires_at
            )
            
            logger.debug(f"Cached weather data for {zip_code}")
            
        except Exception as e:
            logger.error(f"Error caching weather data for {zip_code}: {e}")


# Global service instance
weather_service = WeatherService()
