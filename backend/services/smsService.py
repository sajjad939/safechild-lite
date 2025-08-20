import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

# Twilio library
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    TWILIO_AVAILABLE = False
    logger.warning("Twilio library not available. SMS service will be disabled.")

from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

logger = logging.getLogger(__name__)

class SMSService:
    """Service for sending SMS notifications using Twilio"""
    
    def __init__(self):
        self.text_cleaner = TextCleaner()
        self.time_utils = TimeUtils()
        
        # Twilio configuration
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # SMS settings
        self.max_message_length = int(os.getenv("SMS_MAX_LENGTH", "160"))
        self.default_country_code = os.getenv("SMS_DEFAULT_COUNTRY", "+1")
        self.retry_attempts = int(os.getenv("SMS_RETRY_ATTEMPTS", "3"))
        self.retry_delay = int(os.getenv("SMS_RETRY_DELAY_SECONDS", "5"))
        
        # Rate limiting
        self.max_sms_per_hour = int(os.getenv("SMS_MAX_PER_HOUR", "100"))
        self.max_sms_per_day = int(os.getenv("SMS_MAX_PER_DAY", "1000"))
        
        # Initialize Twilio client
        self.client = None
        self.sms_sent_count = 0
        self.sms_sent_today = 0
        self.last_sms_reset = datetime.now()
        
        if self._validate_twilio_config():
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
        else:
            logger.warning("Twilio configuration incomplete. SMS service will use fallback methods.")
        
        # Emergency contact templates
        self.emergency_templates = {
            "sos_alert": {
                "template": "🚨 EMERGENCY ALERT: {child_name} needs immediate assistance at {location}. Contact: {contact_number}. Priority: {priority}",
                "max_length": 160
            },
            "safety_concern": {
                "template": "⚠️ SAFETY CONCERN: {description}. Location: {location}. Contact: {contact_number}",
                "max_length": 160
            },
            "incident_report": {
                "template": "📝 INCIDENT REPORT: {incident_type} reported at {location}. Status: {status}. Contact: {contact_number}",
                "max_length": 160
            },
            "status_update": {
                "template": "📊 STATUS UPDATE: {update_type} - {description}. Contact: {contact_number}",
                "max_length": 160
            }
        }
        
        # Fallback SMS methods (when Twilio is unavailable)
        self.fallback_methods = {
            "email": os.getenv("SMS_FALLBACK_EMAIL", ""),
            "webhook": os.getenv("SMS_FALLBACK_WEBHOOK", ""),
            "log": True
        }
    
    async def send_emergency_alert(
        self, 
        alert_data: Dict[str, Any], 
        recipients: List[str],
        alert_type: str = "sos_alert"
    ) -> Dict[str, Any]:
        """Send emergency alert SMS to multiple recipients"""
        try:
            if not recipients:
                return {
                    "success": False,
                    "error": "No recipients specified",
                    "sent_count": 0
                }
            
            # Validate alert data
            if not self._validate_alert_data(alert_data):
                return {
                    "success": False,
                    "error": "Invalid alert data",
                    "sent_count": 0
                }
            
            # Check rate limits
            if not self._check_rate_limits(len(recipients)):
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "sent_count": 0
                }
            
            # Prepare message
            message = self._prepare_emergency_message(alert_data, alert_type)
            if not message:
                return {
                    "success": False,
                    "error": "Failed to prepare emergency message",
                    "sent_count": 0
                }
            
            # Send SMS to all recipients
            results = []
            for recipient in recipients:
                result = await self._send_single_sms(recipient, message, alert_type)
                results.append(result)
                
                # Small delay between sends to avoid overwhelming the service
                await asyncio.sleep(0.5)
            
            # Count successful sends
            successful_sends = sum(1 for r in results if r["success"])
            
            # Update counters
            self.sms_sent_count += successful_sends
            self.sms_sent_today += successful_sends
            
            return {
                "success": successful_sends > 0,
                "sent_count": successful_sends,
                "total_recipients": len(recipients),
                "failed_count": len(recipients) - successful_sends,
                "results": results,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error sending emergency alert: {e}")
            return {
                "success": False,
                "error": f"Emergency alert failed: {str(e)}",
                "sent_count": 0
            }
    
    async def send_safety_notification(
        self, 
        notification_data: Dict[str, Any], 
        recipients: List[str],
        notification_type: str = "safety_concern"
    ) -> Dict[str, Any]:
        """Send safety notification SMS"""
        try:
            if not recipients:
                return {
                    "success": False,
                    "error": "No recipients specified",
                    "sent_count": 0
                }
            
            # Prepare message
            message = self._prepare_safety_message(notification_data, notification_type)
            if not message:
                return {
                    "success": False,
                    "error": "Failed to prepare safety message",
                    "sent_count": 0
                }
            
            # Send notifications
            results = []
            for recipient in recipients:
                result = await self._send_single_sms(recipient, message, notification_type)
                results.append(result)
                await asyncio.sleep(0.3)
            
            successful_sends = sum(1 for r in results if r["success"])
            
            # Update counters
            self.sms_sent_count += successful_sends
            self.sms_sent_today += successful_sends
            
            return {
                "success": successful_sends > 0,
                "sent_count": successful_sends,
                "total_recipients": len(recipients),
                "failed_count": len(recipients) - successful_sends,
                "results": results,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error sending safety notification: {e}")
            return {
                "success": False,
                "error": f"Safety notification failed: {str(e)}",
                "sent_count": 0
            }
    
    async def send_status_update(
        self, 
        update_data: Dict[str, Any], 
        recipients: List[str]
    ) -> Dict[str, Any]:
        """Send status update SMS"""
        try:
            if not recipients:
                return {
                    "success": False,
                    "error": "No recipients specified",
                    "sent_count": 0
                }
            
            # Prepare message
            message = self._prepare_status_message(update_data)
            if not message:
                return {
                    "success": False,
                    "error": "Failed to prepare status message",
                    "sent_count": 0
                }
            
            # Send updates
            results = []
            for recipient in recipients:
                result = await self._send_single_sms(recipient, message, "status_update")
                results.append(result)
                await asyncio.sleep(0.2)
            
            successful_sends = sum(1 for r in results if r["success"])
            
            # Update counters
            self.sms_sent_count += successful_sends
            self.sms_sent_today += successful_sends
            
            return {
                "success": successful_sends > 0,
                "sent_count": successful_sends,
                "total_recipients": len(recipients),
                "failed_count": len(recipients) - successful_sends,
                "results": results,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return {
                "success": False,
                "error": f"Status update failed: {str(e)}",
                "sent_count": 0
            }
    
    async def batch_send_sms(
        self, 
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send multiple SMS messages in batch"""
        try:
            if not messages or len(messages) > 50:  # Limit batch size
                return {
                    "success": False,
                    "error": "Invalid batch size. Must be between 1 and 50 messages.",
                    "results": []
                }
            
            # Check rate limits
            total_recipients = sum(len(msg.get("recipients", [])) for msg in messages)
            if not self._check_rate_limits(total_recipients):
                return {
                    "success": False,
                    "error": "Rate limit exceeded for batch send",
                    "results": []
                }
            
            results = []
            for i, message_data in enumerate(messages):
                msg_type = message_data.get("type", "general")
                recipients = message_data.get("recipients", [])
                content = message_data.get("content", "")
                
                if msg_type == "emergency":
                    result = await self.send_emergency_alert(
                        message_data.get("alert_data", {}),
                        recipients,
                        message_data.get("alert_type", "sos_alert")
                    )
                elif msg_type == "safety":
                    result = await self.send_safety_notification(
                        message_data.get("notification_data", {}),
                        recipients,
                        message_data.get("notification_type", "safety_concern")
                    )
                else:
                    result = await self._send_single_sms(
                        recipients[0] if recipients else "",
                        content,
                        "general"
                    )
                
                result["message_index"] = i
                result["message_type"] = msg_type
                results.append(result)
                
                # Delay between batch messages
                await asyncio.sleep(0.5)
            
            success_count = sum(1 for r in results if r["success"])
            
            return {
                "success": success_count > 0,
                "total_messages": len(messages),
                "successful_sends": success_count,
                "failed_sends": len(messages) - success_count,
                "results": results,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error in batch SMS send: {e}")
            return {
                "success": False,
                "error": f"Batch send failed: {str(e)}",
                "results": []
            }
    
    async def _send_single_sms(
        self, 
        recipient: str, 
        message: str, 
        message_type: str = "general"
    ) -> Dict[str, Any]:
        """Send a single SMS message"""
        try:
            # Validate recipient
            if not self._validate_phone_number(recipient):
                return {
                    "success": False,
                    "error": f"Invalid phone number: {recipient}",
                    "recipient": recipient
                }
            
            # Clean and validate message
            cleaned_message = self.text_cleaner.clean_text(message)
            if not cleaned_message:
                return {
                    "success": False,
                    "error": "Empty or invalid message content",
                    "recipient": recipient
                }
            
            # Truncate message if too long
            if len(cleaned_message) > self.max_message_length:
                cleaned_message = cleaned_message[:self.max_message_length-3] + "..."
            
            # Try Twilio first
            if self.client and self._validate_twilio_config():
                try:
                    twilio_result = await self._send_via_twilio(recipient, cleaned_message)
                    if twilio_result["success"]:
                        return twilio_result
                except Exception as e:
                    logger.warning(f"Twilio send failed, trying fallback: {e}")
            
            # Use fallback methods
            return await self._send_via_fallback(recipient, cleaned_message, message_type)
            
        except Exception as e:
            logger.error(f"Error sending single SMS: {e}")
            return {
                "success": False,
                "error": f"SMS send failed: {str(e)}",
                "recipient": recipient
            }
    
    async def _send_via_twilio(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send SMS via Twilio API"""
        try:
            # Format recipient number
            formatted_recipient = self._format_phone_number(recipient)
            
            # Send message
            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=formatted_recipient
            )
            
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "recipient": recipient,
                "provider": "twilio",
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except TwilioException as e:
            logger.error(f"Twilio API error: {e}")
            return {
                "success": False,
                "error": f"Twilio API error: {str(e)}",
                "recipient": recipient,
                "provider": "twilio"
            }
        except Exception as e:
            logger.error(f"Unexpected error in Twilio send: {e}")
            return {
                "success": False,
                "error": f"Twilio send error: {str(e)}",
                "recipient": recipient,
                "provider": "twilio"
            }
    
    async def _send_via_fallback(
        self, 
        recipient: str, 
        message: str, 
        message_type: str
    ) -> Dict[str, Any]:
        """Send SMS via fallback methods"""
        try:
            fallback_results = []
            
            # Log the message
            if self.fallback_methods.get("log"):
                logger.info(f"FALLBACK SMS - To: {recipient}, Type: {message_type}, Message: {message[:50]}...")
                fallback_results.append("log")
            
            # Send via email if configured
            if self.fallback_methods.get("email"):
                email_result = await self._send_via_email(recipient, message, message_type)
                if email_result["success"]:
                    fallback_results.append("email")
            
            # Send via webhook if configured
            if self.fallback_methods.get("webhook"):
                webhook_result = await self._send_via_webhook(recipient, message, message_type)
                if webhook_result["success"]:
                    fallback_results.append("webhook")
            
            if fallback_results:
                return {
                    "success": True,
                    "fallback_methods": fallback_results,
                    "recipient": recipient,
                    "provider": "fallback",
                    "timestamp": self.time_utils.get_current_timestamp()
                }
            else:
                return {
                    "success": False,
                    "error": "No fallback methods available",
                    "recipient": recipient,
                    "provider": "fallback"
                }
                
        except Exception as e:
            logger.error(f"Error in fallback SMS send: {e}")
            return {
                "success": False,
                "error": f"Fallback send failed: {str(e)}",
                "recipient": recipient,
                "provider": "fallback"
            }
    
    async def _send_via_email(self, recipient: str, message: str, message_type: str) -> Dict[str, Any]:
        """Send SMS via email fallback"""
        # This would implement email-based SMS fallback
        # For now, return a placeholder implementation
        return {
            "success": False,
            "error": "Email fallback not implemented",
            "method": "email"
        }
    
    async def _send_via_webhook(self, recipient: str, message: str, message_type: str) -> Dict[str, Any]:
        """Send SMS via webhook fallback"""
        # This would implement webhook-based SMS fallback
        # For now, return a placeholder implementation
        return {
            "success": False,
            "error": "Webhook fallback not implemented",
            "method": "webhook"
        }
    
    def _validate_twilio_config(self) -> bool:
        """Validate Twilio configuration"""
        return all([
            self.account_sid,
            self.auth_token,
            self.phone_number
        ])
    
    def _validate_alert_data(self, alert_data: Dict[str, Any]) -> bool:
        """Validate emergency alert data"""
        required_fields = ["location", "contact_number"]
        return all(field in alert_data for field in required_fields)
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        if not phone_number:
            return False
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Check if it's a reasonable length (7-15 digits)
        return 7 <= len(digits_only) <= 15
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number for Twilio"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if not present
        if not phone_number.startswith('+'):
            if len(digits_only) == 10:  # US number
                return f"+1{digits_only}"
            elif len(digits_only) == 11 and digits_only.startswith('1'):  # US number with country code
                return f"+{digits_only}"
            else:
                return f"+{digits_only}"
        
        return phone_number
    
    def _prepare_emergency_message(
        self, 
        alert_data: Dict[str, Any], 
        alert_type: str
    ) -> Optional[str]:
        """Prepare emergency message from template"""
        try:
            template_info = self.emergency_templates.get(alert_type)
            if not template_info:
                return None
            
            template = template_info["template"]
            
            # Fill template with alert data
            message = template.format(
                child_name=alert_data.get("child_name", "Child"),
                location=alert_data.get("location", "Unknown location"),
                contact_number=alert_data.get("contact_number", "Unknown"),
                priority=alert_data.get("priority", "High"),
                description=alert_data.get("description", "Safety concern"),
                incident_type=alert_data.get("incident_type", "Incident"),
                status=alert_data.get("status", "Reported"),
                update_type=alert_data.get("update_type", "Update")
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error preparing emergency message: {e}")
            return None
    
    def _prepare_safety_message(
        self, 
        notification_data: Dict[str, Any], 
        notification_type: str
    ) -> Optional[str]:
        """Prepare safety notification message"""
        try:
            template_info = self.emergency_templates.get(notification_type)
            if not template_info:
                return None
            
            template = template_info["template"]
            
            message = template.format(
                description=notification_data.get("description", "Safety notification"),
                location=notification_data.get("location", "Unknown location"),
                contact_number=notification_data.get("contact_number", "Unknown")
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error preparing safety message: {e}")
            return None
    
    def _prepare_status_message(self, update_data: Dict[str, Any]) -> Optional[str]:
        """Prepare status update message"""
        try:
            template_info = self.emergency_templates.get("status_update")
            if not template_info:
                return None
            
            template = template_info["template"]
            
            message = template.format(
                update_type=update_data.get("update_type", "Status update"),
                description=update_data.get("description", "No details provided"),
                contact_number=update_data.get("contact_number", "Unknown")
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error preparing status message: {e}")
            return None
    
    def _check_rate_limits(self, additional_sms: int) -> bool:
        """Check if sending additional SMS would exceed rate limits"""
        try:
            current_time = datetime.now()
            
            # Reset daily counter if it's a new day
            if current_time.date() > self.last_sms_reset.date():
                self.sms_sent_today = 0
                self.last_sms_reset = current_time
            
            # Check hourly limit
            if self.sms_sent_count >= self.max_sms_per_hour:
                return False
            
            # Check daily limit
            if self.sms_sent_today + additional_sms > self.max_sms_per_day:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return False  # Fail safe - don't send if we can't check limits
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SMS service health"""
        try:
            twilio_status = "unavailable"
            if self.client and self._validate_twilio_config():
                try:
                    # Test Twilio connection
                    account = self.client.api.accounts(self.account_sid).fetch()
                    twilio_status = "healthy"
                except Exception:
                    twilio_status = "unhealthy"
            
            return {
                "status": "healthy" if twilio_status == "healthy" or self.fallback_methods else "unhealthy",
                "service": "SMS Service",
                "twilio_status": twilio_status,
                "fallback_methods": list(self.fallback_methods.keys()),
                "rate_limits": {
                    "sms_sent_hour": self.sms_sent_count,
                    "sms_sent_today": self.sms_sent_today,
                    "max_per_hour": self.max_sms_per_hour,
                    "max_per_day": self.max_sms_per_day
                },
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"SMS service health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "SMS Service",
                "error": str(e),
                "timestamp": self.time_utils.get_current_timestamp()
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get SMS service usage statistics"""
        return {
            "twilio_configured": self._validate_twilio_config(),
            "fallback_methods": self.fallback_methods,
            "max_message_length": self.max_message_length,
            "default_country_code": self.default_country_code,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "max_sms_per_hour": self.max_sms_per_hour,
            "max_sms_per_day": self.max_sms_per_day,
            "sms_sent_count": self.sms_sent_count,
            "sms_sent_today": self.sms_sent_today
        }
    
    def reset_counters(self):
        """Reset SMS counters (useful for testing)"""
        self.sms_sent_count = 0
        self.sms_sent_today = 0
        self.last_sms_reset = datetime.now()
        logger.info("SMS counters reset")
