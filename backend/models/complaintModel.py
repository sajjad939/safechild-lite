from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class IncidentType(str, Enum):
    """Enumeration of incident types"""
    PHYSICAL_ABUSE = "physical_abuse"
    VERBAL_ABUSE = "verbal_abuse"
    BULLYING = "bullying"
    INAPPROPRIATE_TOUCHING = "inappropriate_touching"
    HARASSMENT = "harassment"
    NEGLECT = "neglect"
    CYBER_BULLYING = "cyber_bullying"
    SEXUAL_HARASSMENT = "sexual_harassment"
    EMOTIONAL_ABUSE = "emotional_abuse"
    OTHER = "other"

class ComplaintStatus(str, Enum):
    """Enumeration of complaint statuses"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INVESTIGATION = "investigation"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

class PriorityLevel(str, Enum):
    """Enumeration of priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class ChildGender(str, Enum):
    """Enumeration of child gender options"""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class LegalActionType(str, Enum):
    """Enumeration of legal action types"""
    LEGAL_ACTION = "legal_action"
    MEDIATION = "mediation"
    RESTRAINING_ORDER = "restraining_order"
    COMPENSATION = "compensation"
    INVESTIGATION = "investigation"
    DISCIPLINARY_ACTION = "disciplinary_action"

class ComplaintData(BaseModel):
    """Data model for complaint information"""
    
    # Basic complaint information
    complaint_id: Optional[str] = Field(None, description="Unique complaint identifier")
    status: ComplaintStatus = Field(default=ComplaintStatus.DRAFT, description="Current status of the complaint")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Priority level of the complaint")
    created_at: Optional[datetime] = Field(None, description="When the complaint was created")
    updated_at: Optional[datetime] = Field(None, description="When the complaint was last updated")
    
    # Child information
    child_name: str = Field(..., min_length=1, max_length=100, description="Name of the child involved")
    child_age: int = Field(..., ge=0, le=18, description="Age of the child")
    child_gender: Optional[ChildGender] = Field(None, description="Gender of the child")
    child_school: Optional[str] = Field(None, max_length=200, description="School or institution the child attends")
    child_grade: Optional[str] = Field(None, max_length=20, description="Grade level of the child")
    child_contact: Optional[str] = Field(None, max_length=50, description="Contact information for the child")
    
    # Incident information
    incident_type: IncidentType = Field(..., description="Type of incident that occurred")
    incident_date: str = Field(..., description="Date when the incident occurred")
    incident_time: str = Field(..., description="Time when the incident occurred")
    location: str = Field(..., min_length=1, max_length=500, description="Location where the incident occurred")
    incident_description: str = Field(..., min_length=10, max_length=5000, description="Detailed description of the incident")
    
    # Guardian information
    guardian_name: str = Field(..., min_length=1, max_length=100, description="Name of the guardian/parent")
    guardian_phone: str = Field(..., min_length=10, max_length=20, description="Phone number of the guardian")
    guardian_email: Optional[str] = Field(None, max_length=100, description="Email address of the guardian")
    guardian_address: Optional[str] = Field(None, max_length=500, description="Address of the guardian")
    guardian_relationship: Optional[str] = Field(None, max_length=50, description="Relationship to the child")
    
    # Additional incident details
    witnesses: Optional[str] = Field(None, max_length=1000, description="Information about any witnesses")
    evidence: Optional[str] = Field(None, max_length=1000, description="Available evidence or documentation")
    previous_incidents: Optional[str] = Field(None, max_length=1000, description="Information about previous similar incidents")
    
    # Legal preferences
    wants_legal_action: bool = Field(default=False, description="Whether legal action is desired")
    wants_mediation: bool = Field(default=False, description="Whether mediation is desired")
    wants_restraining_order: bool = Field(default=False, description="Whether a restraining order is desired")
    wants_compensation: bool = Field(default=False, description="Whether compensation is desired")
    additional_requests: Optional[str] = Field(None, max_length=1000, description="Any additional requests or concerns")
    
    # Generated content
    complaint_text: Optional[str] = Field(None, description="Generated complaint draft text")
    generated_at: Optional[datetime] = Field(None, description="When the complaint draft was generated")
    
    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorizing the complaint")
    notes: Optional[str] = Field(None, max_length=2000, description="Internal notes about the complaint")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Person assigned to handle the complaint")
    
    # Validation methods
    @validator('incident_date')
    def validate_incident_date(cls, v):
        """Validate incident date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('incident_date must be in YYYY-MM-DD format')
    
    @validator('incident_time')
    def validate_incident_time(cls, v):
        """Validate incident time format"""
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('incident_time must be in HH:MM format')
    
    @validator('guardian_phone')
    def validate_guardian_phone(cls, v):
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError('Phone number must contain at least 10 digits')
        return v
    
    @validator('guardian_email')
    def validate_guardian_email(cls, v):
        """Validate email format if provided"""
        if v is not None:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('child_age')
    def validate_child_age(cls, v):
        """Validate child age"""
        if v < 0 or v > 18:
            raise ValueError('Child age must be between 0 and 18')
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ComplaintUpdate(BaseModel):
    """Model for updating complaint information"""
    status: Optional[ComplaintStatus] = None
    priority: Optional[PriorityLevel] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True

class ComplaintSummary(BaseModel):
    """Summary model for complaint listing"""
    complaint_id: str
    child_name: str
    incident_type: IncidentType
    incident_date: str
    status: ComplaintStatus
    priority: PriorityLevel
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ComplaintStatistics(BaseModel):
    """Model for complaint statistics"""
    total_complaints: int
    complaints_by_status: Dict[str, int]
    complaints_by_type: Dict[str, int]
    complaints_by_priority: Dict[str, int]
    complaints_by_month: Dict[str, int]
    average_resolution_time_days: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ComplaintSearch(BaseModel):
    """Model for complaint search parameters"""
    query: Optional[str] = None
    incident_type: Optional[IncidentType] = None
    status: Optional[ComplaintStatus] = None
    priority: Optional[PriorityLevel] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    child_name: Optional[str] = None
    guardian_name: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    class Config:
        use_enum_values = True
