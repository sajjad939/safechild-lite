import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Union
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeUtils:
    """Utility class for time-related operations"""
    
    def __init__(self, default_timezone: str = "UTC"):
        self.default_timezone = default_timezone
        self.supported_timezones = self.get_supported_timezones()
        
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
    
    def get_supported_timezones(self) -> Dict[str, str]:
        """Get list of supported timezones"""
        try:
            # Common timezones for the application
            common_timezones = {
                "UTC": "UTC",
                "US/Eastern": "Eastern Time",
                "US/Central": "Central Time", 
                "US/Mountain": "Mountain Time",
                "US/Pacific": "Pacific Time",
                "Europe/London": "London",
                "Europe/Paris": "Paris",
                "Europe/Berlin": "Berlin",
                "Asia/Tokyo": "Tokyo",
                "Asia/Shanghai": "Shanghai",
                "Australia/Sydney": "Sydney"
            }
            
            # Add pytz timezones if available
            if pytz:
                for tz_name in pytz.all_timezones:
                    if tz_name not in common_timezones:
                        common_timezones[tz_name] = tz_name
            
            return common_timezones
            
        except Exception as e:
            logger.error(f"Error getting supported timezones: {str(e)}")
            return {"UTC": "UTC"}
    
    def get_current_timestamp(self, timezone_name: Optional[str] = None, 
                            format_type: str = "iso") -> str:
        """Get current timestamp in specified format and timezone"""
        try:
            # Get current time
            if timezone_name and timezone_name in self.supported_timezones:
                tz = pytz.timezone(timezone_name)
                current_time = datetime.now(tz)
            else:
                current_time = datetime.now(timezone.utc)
            
            # Format timestamp
            if format_type in self.time_formats:
                return current_time.strftime(self.time_formats[format_type])
            else:
                return current_time.isoformat()
                
        except Exception as e:
            logger.error(f"Error getting current timestamp: {str(e)}")
            return datetime.now().isoformat()
    
    def get_current_datetime(self, timezone_name: Optional[str] = None) -> datetime:
        """Get current datetime object in specified timezone"""
        try:
            if timezone_name and timezone_name in self.supported_timezones:
                tz = pytz.timezone(timezone_name)
                return datetime.now(tz)
            else:
                return datetime.now(timezone.utc)
                
        except Exception as e:
            logger.error(f"Error getting current datetime: {str(e)}")
            return datetime.now()
    
    def parse_timestamp(self, timestamp: str, format_type: str = "auto") -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp:
            return None
        
        try:
            # Auto-detect format
            if format_type == "auto":
                # Try common formats
                for fmt_name, fmt_str in self.time_formats.items():
                    try:
                        return datetime.strptime(timestamp, fmt_str)
                    except ValueError:
                        continue
                
                # Try ISO format
                try:
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    pass
                
                # Try parsing with dateutil if available
                try:
                    from dateutil import parser
                    return parser.parse(timestamp)
                except ImportError:
                    pass
                
                logger.warning(f"Could not parse timestamp: {timestamp}")
                return None
            
            # Use specified format
            elif format_type in self.time_formats:
                return datetime.strptime(timestamp, self.time_formats[format_type])
            else:
                return datetime.strptime(timestamp, format_type)
                
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp}: {str(e)}")
            return None
    
    def format_timestamp(self, dt: datetime, format_type: str = "iso", 
                        timezone_name: Optional[str] = None) -> str:
        """Format datetime object to string"""
        try:
            # Convert timezone if specified
            if timezone_name and timezone_name in self.supported_timezones:
                tz = pytz.timezone(timezone_name)
                if dt.tzinfo is None:
                    dt = pytz.utc.localize(dt)
                dt = dt.astimezone(tz)
            
            # Format timestamp
            if format_type in self.time_formats:
                return dt.strftime(self.time_formats[format_type])
            else:
                return dt.strftime(format_type)
                
        except Exception as e:
            logger.error(f"Error formatting timestamp: {str(e)}")
            return dt.isoformat()
    
    def get_time_difference(self, start_time: Union[str, datetime], 
                           end_time: Union[str, datetime] = None,
                           unit: str = "seconds") -> float:
        """Calculate time difference between two timestamps"""
        try:
            # Parse timestamps if they're strings
            if isinstance(start_time, str):
                start_dt = self.parse_timestamp(start_time)
                if not start_dt:
                    return 0.0
            else:
                start_dt = start_time
            
            if isinstance(end_time, str):
                end_dt = self.parse_timestamp(end_time)
                if not end_dt:
                    end_dt = self.get_current_datetime()
            else:
                end_dt = end_time or self.get_current_datetime()
            
            # Calculate difference
            time_diff = end_dt - start_dt
            
            # Convert to requested unit
            if unit == "seconds":
                return time_diff.total_seconds()
            elif unit == "minutes":
                return time_diff.total_seconds() / 60
            elif unit == "hours":
                return time_diff.total_seconds() / 3600
            elif unit == "days":
                return time_diff.days
            else:
                return time_diff.total_seconds()
                
        except Exception as e:
            logger.error(f"Error calculating time difference: {str(e)}")
            return 0.0
    
    def is_within_24_hours(self, timestamp: Union[str, datetime]) -> bool:
        """Check if timestamp is within the last 24 hours"""
        try:
            if isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return False
            else:
                dt = timestamp
            
            current_time = self.get_current_datetime()
            time_diff = current_time - dt
            
            return time_diff.total_seconds() <= 86400  # 24 hours in seconds
            
        except Exception as e:
            logger.error(f"Error checking if within 24 hours: {str(e)}")
            return False
    
    def is_within_week(self, timestamp: Union[str, datetime]) -> bool:
        """Check if timestamp is within the last week"""
        try:
            if isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return False
            else:
                dt = timestamp
            
            current_time = self.get_current_datetime()
            week_ago = current_time - timedelta(days=7)
            
            return dt >= week_ago
            
        except Exception as e:
            logger.error(f"Error checking if within week: {str(e)}")
            return False
    
    def is_within_month(self, timestamp: Union[str, datetime]) -> bool:
        """Check if timestamp is within the last month"""
        try:
            if isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return False
            else:
                dt = timestamp
            
            current_time = self.get_current_datetime()
            month_ago = current_time - timedelta(days=30)
            
            return dt >= month_ago
            
        except Exception as e:
            logger.error(f"Error checking if within month: {str(e)}")
            return False
    
    def add_time(self, timestamp: Union[str, datetime], 
                 days: int = 0, hours: int = 0, minutes: int = 0, 
                 seconds: int = 0) -> datetime:
        """Add time to timestamp"""
        try:
            if isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return self.get_current_datetime()
            else:
                dt = timestamp
            
            # Add specified time
            result = dt + timedelta(
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding time: {str(e)}")
            return self.get_current_datetime()
    
    def subtract_time(self, timestamp: Union[str, datetime], 
                      days: int = 0, hours: int = 0, minutes: int = 0, 
                      seconds: int = 0) -> datetime:
        """Subtract time from timestamp"""
        try:
            if isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return self.get_current_datetime()
            else:
                dt = timestamp
            
            # Subtract specified time
            result = dt - timedelta(
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error subtracting time: {str(e)}")
            return self.get_current_datetime()
    
    def get_relative_time(self, timestamp: Union[str, datetime]) -> str:
        """Get human-readable relative time (e.g., '2 hours ago')"""
        try:
            if isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return "unknown time"
            else:
                dt = timestamp
            
            current_time = self.get_current_datetime()
            time_diff = current_time - dt
            
            # Convert to seconds
            seconds = time_diff.total_seconds()
            
            if seconds < 0:
                return "in the future"
            elif seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif seconds < 2592000:  # 30 days
                days = int(seconds / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
            elif seconds < 31536000:  # 365 days
                months = int(seconds / 2592000)
                return f"{months} month{'s' if months != 1 else ''} ago"
            else:
                years = int(seconds / 31536000)
                return f"{years} year{'s' if years != 1 else ''} ago"
                
        except Exception as e:
            logger.error(f"Error getting relative time: {str(e)}")
            return "unknown time"
    
    def get_timezone_info(self, timezone_name: str) -> Dict[str, Any]:
        """Get information about a specific timezone"""
        try:
            if timezone_name not in self.supported_timezones:
                return {"error": "Timezone not supported"}
            
            tz = pytz.timezone(timezone_name)
            current_time = datetime.now(tz)
            
            return {
                "timezone": timezone_name,
                "current_time": current_time.strftime(self.time_formats["datetime"]),
                "utc_offset": current_time.strftime("%z"),
                "dst_active": bool(current_time.dst()),
                "timezone_name": self.supported_timezones[timezone_name]
            }
            
        except Exception as e:
            logger.error(f"Error getting timezone info: {str(e)}")
            return {"error": str(e)}
    
    def convert_timezone(self, timestamp: Union[str, datetime], 
                        from_timezone: str, to_timezone: str) -> Optional[datetime]:
        """Convert timestamp between timezones"""
        try:
            # Parse timestamp if it's a string
            if isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return None
            else:
                dt = timestamp
            
            # Get timezone objects
            from_tz = pytz.timezone(from_timezone)
            to_tz = pytz.timezone(to_timezone)
            
            # Localize datetime if it doesn't have timezone info
            if dt.tzinfo is None:
                dt = from_tz.localize(dt)
            
            # Convert timezone
            converted_dt = dt.astimezone(to_tz)
            
            return converted_dt
            
        except Exception as e:
            logger.error(f"Error converting timezone: {str(e)}")
            return None
    
    def get_business_hours(self, timezone_name: str = "UTC") -> Dict[str, Any]:
        """Get business hours for a timezone"""
        try:
            # Default business hours (9 AM - 5 PM)
            business_hours = {
                "start": "09:00",
                "end": "17:00",
                "timezone": timezone_name,
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "weekend": False
            }
            
            # Customize based on timezone if needed
            if timezone_name in ["US/Eastern", "US/Central", "US/Mountain", "US/Pacific"]:
                business_hours["start"] = "08:00"
                business_hours["end"] = "18:00"
            
            return business_hours
            
        except Exception as e:
            logger.error(f"Error getting business hours: {str(e)}")
            return {
                "start": "09:00",
                "end": "17:00",
                "timezone": "UTC",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "weekend": False
            }
    
    def is_business_hours(self, timestamp: Union[str, datetime] = None, 
                          timezone_name: str = "UTC") -> bool:
        """Check if timestamp is during business hours"""
        try:
            if timestamp is None:
                dt = self.get_current_datetime(timezone_name)
            elif isinstance(timestamp, str):
                dt = self.parse_timestamp(timestamp)
                if not dt:
                    return False
            else:
                dt = timestamp
            
            # Get business hours
            business_hours = self.get_business_hours(timezone_name)
            
            # Check if it's a business day
            day_name = dt.strftime("%A")
            if day_name not in business_hours["days"]:
                return False
            
            # Check if it's during business hours
            current_time = dt.strftime("%H:%M")
            return business_hours["start"] <= current_time <= business_hours["end"]
            
        except Exception as e:
            logger.error(f"Error checking business hours: {str(e)}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration"""
        return {
            "service": "time_utils",
            "status": "active",
            "default_timezone": self.default_timezone,
            "supported_timezones": len(self.supported_timezones),
            "time_formats": list(self.time_formats.keys()),
            "current_time": self.get_current_timestamp(),
            "timestamp": self.get_current_timestamp()
        }
