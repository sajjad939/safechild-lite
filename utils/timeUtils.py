import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class TimeUtils:
    """Utility class for time-related operations"""
    
    def __init__(self, default_timezone: str = "UTC"):
        self.default_timezone = default_timezone
        
        # Common time formats
        self.time_formats = {
            "iso": "%Y-%m-%dT%H:%M:%S.%fZ",
            "iso_short": "%Y-%m-%dT%H:%M:%SZ",
            "date": "%Y-%m-%d",
            "time": "%H:%M:%S",
            "datetime": "%Y-%m-%d %H:%M:%S",
            "readable": "%B %d, %Y at %I:%M %p",
            "short_date": "%m/%d/%Y",
            "filename": "%Y%m%d_%H%M%S"
        }
    
    def get_current_timestamp(self, format_type: str = "iso") -> str:
        """Get current timestamp in specified format"""
        try:
            current_time = datetime.now(timezone.utc)
            
            if format_type in self.time_formats:
                return current_time.strftime(self.time_formats[format_type])
            else:
                return current_time.isoformat()
                
        except Exception as e:
            logger.error(f"Error getting current timestamp: {str(e)}")
            return datetime.now().isoformat()
    
    def get_current_datetime(self) -> datetime:
        """Get current datetime object"""
        return datetime.now(timezone.utc)
    
    def format_timestamp(self, dt: datetime, format_type: str = "iso") -> str:
        """Format datetime object to string"""
        try:
            if format_type in self.time_formats:
                return dt.strftime(self.time_formats[format_type])
            else:
                return dt.strftime(format_type)
        except Exception as e:
            logger.error(f"Error formatting timestamp: {str(e)}")
            return dt.isoformat()
    
    def is_within_24_hours(self, timestamp: Union[str, float]) -> bool:
        """Check if timestamp is within the last 24 hours"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            
            current_time = self.get_current_datetime()
            time_diff = current_time - dt
            
            return time_diff.total_seconds() <= 86400
            
        except Exception as e:
            logger.error(f"Error checking if within 24 hours: {str(e)}")
            return False
    
    def get_relative_time(self, timestamp: Union[str, datetime, float]) -> str:
        """Get human-readable relative time"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, float):
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                dt = timestamp
            
            current_time = self.get_current_datetime()
            time_diff = current_time - dt
            seconds = time_diff.total_seconds()
            
            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
                
        except Exception as e:
            logger.error(f"Error getting relative time: {str(e)}")
            return "unknown time"