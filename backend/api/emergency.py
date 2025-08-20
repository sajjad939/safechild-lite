from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime
import uuid

# Import services
from backend.services.smsService import SMSService
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emergency", tags=["emergency"])

class EmergencyContact(BaseModel):
    name: str
    phone: str
    relationship: str

class EmergencyRequest(BaseModel):
    location: str
    description: str
    contacts: List[EmergencyContact]
    timestamp: Optional[str] = None
    user_id: Optional[str] = None
    emergency_type: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None

class EmergencyResponse(BaseModel):
    alert_id: str
    status: str
    timestamp: str
    contacts_notified: List[Dict[str, Any]]
    emergency_level: str
    next_steps: List[str]

class EmergencyAlert(BaseModel):
    alert_id: str
    user_id: str
    location: str
    description: str
    contacts: List[EmergencyContact]
    timestamp: str
    status: str
    emergency_level: str
    contacts_notified: List[Dict[str, Any]]
    next_steps: List[str]

class EmergencyAPI:
    def __init__(self):
        self.sms_service = SMSService()
        self.text_cleaner = TextCleaner()
        self.time_utils = TimeUtils()
        
        # In-memory emergency alerts (in production, use a database)
        self.emergency_alerts: Dict[str, EmergencyAlert] = {}
        
        # Emergency level definitions
        self.emergency_levels = {
            "critical": {
                "level": "critical",
                "description": "Immediate danger to life or safety",
                "response_time": "immediate",
                "authorities_notified": True,
                "sms_priority": "high"
            },
            "high": {
                "level": "high",
                "description": "Significant safety concern",
                "response_time": "within_15_minutes",
                "authorities_notified": False,
                "sms_priority": "high"
            },
            "medium": {
                "level": "medium",
                "description": "Moderate safety concern",
                "response_time": "within_1_hour",
                "authorities_notified": False,
                "sms_priority": "normal"
            },
            "low": {
                "level": "low",
                "description": "Minor safety concern",
                "response_time": "within_24_hours",
                "authorities_notified": False,
                "sms_priority": "normal"
            }
        }
        
        # Emergency keywords for automatic level detection
        self.critical_keywords = [
            "hurt", "pain", "bleeding", "unconscious", "not breathing",
            "choking", "fire", "explosion", "weapon", "gun", "knife",
            "attack", "assault", "kidnapping", "missing", "lost"
        ]
        
        self.high_keywords = [
            "scared", "afraid", "threat", "danger", "bully", "harassment",
            "abuse", "touch", "private", "secret", "follow", "stranger"
        ]
    
    def create_alert_id(self) -> str:
        """Generate unique emergency alert ID"""
        return f"EMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"
    
    def determine_emergency_level(self, description: str, emergency_type: Optional[str] = None) -> str:
        """Determine emergency level based on description and type"""
        description_lower = description.lower()
        
        # Check for critical keywords
        if any(keyword in description_lower for keyword in self.critical_keywords):
            return "critical"
        
        # Check for high keywords
        if any(keyword in description_lower for keyword in self.high_keywords):
            return "high"
        
        # Check emergency type
        if emergency_type:
            type_lower = emergency_type.lower()
            if any(word in type_lower for word in ["immediate", "danger", "medical", "abuse"]):
                return "high"
            elif any(word in type_lower for word in ["lost", "missing", "bullying"]):
                return "medium"
        
        # Default to medium if uncertain
        return "medium"
    
    def generate_next_steps(self, emergency_level: str, description: str) -> List[str]:
        """Generate next steps based on emergency level"""
        steps = []
        
        if emergency_level == "critical":
            steps.extend([
                "🚨 Call 911 immediately",
                "📱 Stay on the line with emergency services",
                "📍 Provide exact location details",
                "👥 Keep all emergency contacts informed",
                "📋 Document everything that happens"
            ])
        elif emergency_level == "high":
            steps.extend([
                "📞 Contact emergency services if needed",
                "👥 Notify all emergency contacts",
                "📱 Keep phone charged and accessible",
                "📍 Stay in safe location",
                "📋 Document incident details"
            ])
        elif emergency_level == "medium":
            steps.extend([
                "👥 Contact emergency contacts",
                "📱 Monitor situation closely",
                "📍 Note location and time",
                "📋 Document what happened",
                "🔄 Follow up with authorities if needed"
            ])
        else:  # low
            steps.extend([
                "👥 Inform emergency contacts",
                "📱 Monitor situation",
                "📋 Document incident",
                "🔄 Follow up as needed"
            ])
        
        return steps
    
    def validate_emergency_data(self, data: EmergencyRequest) -> List[str]:
        """Validate emergency request data"""
        errors = []
        
        if not data.location.strip():
            errors.append("Location is required")
        
        if not data.description.strip():
            errors.append("Emergency description is required")
        
        if not data.contacts:
            errors.append("At least one emergency contact is required")
        else:
            for contact in data.contacts:
                if not contact.name.strip():
                    errors.append("Contact name is required")
                if not contact.phone.strip():
                    errors.append("Contact phone number is required")
        
        return errors
    
    async def send_emergency_notifications(self, alert: EmergencyAlert) -> List[Dict[str, Any]]:
        """Send emergency notifications to all contacts"""
        try:
            recipients = [c.phone for c in alert.contacts if c.phone]
            alert_data = {
                "child_name": alert.user_id or "Child",
                "location": alert.location,
                "contact_number": recipients[0] if recipients else "",
                "priority": alert.emergency_level,
                "description": alert.description,
                "incident_type": alert.emergency_level,
                "status": alert.status,
                "update_type": "emergency"
            }
            result = await self.sms_service.send_emergency_alert(alert_data, recipients, alert_type="sos_alert")
            mapped = []
            for idx, c in enumerate(alert.contacts):
                item = {
                    "name": c.name,
                    "phone": c.phone,
                    "relationship": c.relationship,
                    "status": "sent" if idx < len(result.get("results", [])) and result["results"][idx].get("success") else "failed",
                    "timestamp": self.time_utils.get_current_timestamp()
                }
                mapped.append(item)
            return mapped
        except Exception as e:
            logger.error(f"Failed to send emergency notifications: {str(e)}")
            return []
    
    def create_emergency_message(self, alert: EmergencyAlert, contact: EmergencyContact) -> str:
        """Create emergency SMS message"""
        level_info = self.emergency_levels.get(alert.emergency_level, {})
        
        message = f"""
🚨 EMERGENCY ALERT 🚨

{contact.name}, there is an emergency situation that requires immediate attention.

📍 Location: {alert.location}
🚨 Level: {alert.emergency_level.upper()}
📝 Description: {alert.description}
⏰ Time: {alert.timestamp}

{level_info.get('description', 'Safety concern detected')}

Please respond immediately and take appropriate action.

SafeChild-Lite Emergency System
        """.strip()
        
        return message
    
    async def process_emergency(self, request: EmergencyRequest) -> EmergencyResponse:
        """Process emergency alert and send notifications"""
        try:
            # Validate data
            errors = self.validate_emergency_data(request)
            if errors:
                raise HTTPException(status_code=400, detail=f"Validation errors: {', '.join(errors)}")
            
            # Create alert ID
            alert_id = self.create_alert_id()
            
            # Determine emergency level
            emergency_level = self.determine_emergency_level(
                request.description, 
                request.timestamp
            )
            
            # Generate next steps
            next_steps = self.generate_next_steps(emergency_level, request.description)
            
            # Create emergency alert
            alert = EmergencyAlert(
                alert_id=alert_id,
                user_id=request.user_id or "anonymous",
                location=request.location,
                description=request.description,
                contacts=request.contacts,
                timestamp=request.timestamp or self.time_utils.get_current_timestamp(),
                status="active",
                emergency_level=emergency_level,
                contacts_notified=[],
                next_steps=next_steps
            )
            
            # Store alert
            self.emergency_alerts[alert_id] = alert
            
            # Send notifications
            contacts_notified = await self.send_emergency_notifications(alert)
            
            # Update alert with notification results
            alert.contacts_notified = contacts_notified
            self.emergency_alerts[alert_id] = alert
            
            logger.info(f"Emergency alert processed: {alert_id}, level: {emergency_level}")
            
            # Create response
            response = EmergencyResponse(
                alert_id=alert_id,
                status="active",
                timestamp=alert.timestamp,
                contacts_notified=contacts_notified,
                emergency_level=emergency_level,
                next_steps=next_steps
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing emergency: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def get_emergency_alert(self, alert_id: str) -> EmergencyAlert:
        """Get emergency alert by ID"""
        alert = self.emergency_alerts.get(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Emergency alert not found")
        
        return alert
    
    def get_all_alerts(self) -> List[EmergencyAlert]:
        """Get all emergency alerts"""
        return list(self.emergency_alerts.values())
    
    def update_alert_status(self, alert_id: str, status: str) -> EmergencyAlert:
        """Update emergency alert status"""
        alert = self.emergency_alerts.get(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Emergency alert not found")
        
        alert.status = status
        alert.updated_at = self.time_utils.get_current_timestamp()
        
        return alert
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get emergency alert statistics"""
        total_alerts = len(self.emergency_alerts)
        active_alerts = len([a for a in self.emergency_alerts.values() if a.status == "active"])
        
        level_counts = {}
        for alert in self.emergency_alerts.values():
            level = alert.emergency_level
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": total_alerts - active_alerts,
            "level_distribution": level_counts,
            "last_24_hours": len([
                a for a in self.emergency_alerts.values() 
                if self.time_utils.is_within_24_hours(a.timestamp)
            ])
        }

# Initialize API
emergency_api = EmergencyAPI()

@router.post("/", response_model=EmergencyResponse)
async def trigger_emergency(request: EmergencyRequest):
    """Trigger emergency alert"""
    return await emergency_api.process_emergency(request)

@router.post("")
async def trigger_emergency_root(request: EmergencyRequest):
    """Trigger emergency alert (root alias)"""
    return await emergency_api.process_emergency(request)

@router.get("/{alert_id}")
async def get_emergency_alert(alert_id: str):
    """Get emergency alert by ID"""
    return emergency_api.get_emergency_alert(alert_id)

@router.get("/")
async def get_all_emergency_alerts():
    """Get all emergency alerts"""
    return {"alerts": emergency_api.get_all_alerts()}

@router.get("/{alert_id}/status")
async def get_alert_status(alert_id: str):
    """Get emergency alert status"""
    alert = emergency_api.get_emergency_alert(alert_id)
    return {
        "alert_id": alert.alert_id,
        "status": alert.status,
        "emergency_level": alert.emergency_level,
        "timestamp": alert.timestamp,
        "contacts_notified": alert.contacts_notified
    }

@router.put("/{alert_id}/status")
async def update_alert_status(alert_id: str, status: str):
    """Update emergency alert status"""
    return emergency_api.update_alert_status(alert_id, status)

@router.get("/statistics")
async def get_emergency_statistics():
    """Get emergency alert statistics"""
    return emergency_api.get_alert_statistics()

@router.delete("/{alert_id}")
async def delete_emergency_alert(alert_id: str):
    """Delete emergency alert"""
    if alert_id in emergency_api.emergency_alerts:
        del emergency_api.emergency_alerts[alert_id]
        return {"message": "Emergency alert deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Emergency alert not found")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "emergency",
        "timestamp": TimeUtils().get_current_timestamp(),
        "active_alerts": len([a for a in emergency_api.emergency_alerts.values() if a.status == "active"]),
        "total_alerts": len(emergency_api.emergency_alerts)
    }
