from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re

class UserRole(str, Enum):
    """Enumeration of user roles"""
    CHILD = "child"
    PARENT = "parent"
    GUARDIAN = "guardian"
    TEACHER = "teacher"
    ADMINISTRATOR = "administrator"
    COUNSELOR = "counselor"
    LAW_ENFORCEMENT = "law_enforcement"
    HEALTHCARE_PROVIDER = "healthcare_provider"
    VOLUNTEER = "volunteer"
    ADMIN = "admin"

class UserStatus(str, Enum):
    """Enumeration of user statuses"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"

class NotificationPreference(str, Enum):
    """Enumeration of notification preferences"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    NONE = "none"

class UserData(BaseModel):
    """Data model for user information"""
    
    # Basic user information
    user_id: Optional[str] = Field(None, description="Unique user identifier")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username for login")
    email: EmailStr = Field(..., description="User's email address")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20, description="User's phone number")
    
    # Personal information
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User's last name")
    date_of_birth: Optional[str] = Field(None, description="User's date of birth")
    gender: Optional[str] = Field(None, max_length=20, description="User's gender")
    
    # Role and status
    role: UserRole = Field(..., description="User's role in the system")
    status: UserStatus = Field(default=UserStatus.PENDING, description="Current status of the user account")
    is_verified: bool = Field(default=False, description="Whether the user's identity has been verified")
    
    # Contact and location
    address: Optional[str] = Field(None, max_length=500, description="User's address")
    city: Optional[str] = Field(None, max_length=100, description="User's city")
    state: Optional[str] = Field(None, max_length=100, description="User's state/province")
    country: Optional[str] = Field(None, max_length=100, description="User's country")
    postal_code: Optional[str] = Field(None, max_length=20, description="User's postal code")
    
    # Emergency contacts
    emergency_contacts: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, 
        description="List of emergency contacts"
    )
    
    # Preferences and settings
    notification_preferences: List[NotificationPreference] = Field(
        default_factory=lambda: [NotificationPreference.EMAIL],
        description="User's notification preferences"
    )
    language_preference: str = Field(default="en", max_length=10, description="Preferred language")
    timezone: str = Field(default="UTC", max_length=50, description="User's timezone")
    
    # Security and access
    password_hash: Optional[str] = Field(None, description="Hashed password (not exposed in API)")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_attempts: int = Field(default=0, description="Number of failed login attempts")
    account_locked_until: Optional[datetime] = Field(None, description="Account lockout until timestamp")
    
    # Profile information
    profile_picture: Optional[str] = Field(None, description="URL to profile picture")
    bio: Optional[str] = Field(None, max_length=500, description="User's biography or description")
    interests: Optional[List[str]] = Field(default_factory=list, description="User's interests")
    
    # System metadata
    created_at: Optional[datetime] = Field(None, description="When the user account was created")
    updated_at: Optional[datetime] = Field(None, description="When the user account was last updated")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # Permissions and access control
    permissions: Optional[List[str]] = Field(default_factory=list, description="User's permissions")
    access_level: Optional[str] = Field(None, description="User's access level")
    
    # Validation methods
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if v is not None:
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth format"""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('date_of_birth must be in YYYY-MM-DD format')
        return v
    
    @validator('emergency_contacts')
    def validate_emergency_contacts(cls, v):
        """Validate emergency contacts structure"""
        if v is not None:
            for contact in v:
                if not isinstance(contact, dict):
                    raise ValueError('Emergency contacts must be a list of dictionaries')
                required_fields = ['name', 'phone', 'relationship']
                for field in required_fields:
                    if field not in contact:
                        raise ValueError(f'Emergency contact missing required field: {field}')
        return v
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    """Model for creating new users"""
    username: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=8, description="User's password")
    first_name: str
    last_name: str
    role: UserRole
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    language_preference: str = "en"
    timezone: str = "UTC"
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserUpdate(BaseModel):
    """Model for updating user information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    notification_preferences: Optional[List[NotificationPreference]] = None
    language_preference: Optional[str] = None
    timezone: Optional[str] = None
    emergency_contacts: Optional[List[Dict[str, Any]]] = None

class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str

class UserPasswordChange(BaseModel):
    """Model for changing user password"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserProfile(BaseModel):
    """Model for user profile display"""
    user_id: str
    username: Optional[str]
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    is_verified: bool
    profile_picture: Optional[str]
    bio: Optional[str]
    interests: List[str]
    created_at: datetime
    last_activity: Optional[datetime]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserSummary(BaseModel):
    """Summary model for user listing"""
    user_id: str
    username: Optional[str]
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    is_verified: bool
    created_at: datetime
    last_activity: Optional[datetime]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EmergencyContact(BaseModel):
    """Model for emergency contact information"""
    name: str = Field(..., min_length=1, max_length=100, description="Contact's full name")
    phone: str = Field(..., min_length=10, max_length=20, description="Contact's phone number")
    relationship: str = Field(..., min_length=1, max_length=50, description="Relationship to the user")
    email: Optional[str] = Field(None, description="Contact's email address")
    address: Optional[str] = Field(None, max_length=500, description="Contact's address")
    is_primary: bool = Field(default=False, description="Whether this is the primary emergency contact")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError('Phone number must contain at least 10 digits')
        return v

class UserSearch(BaseModel):
    """Model for user search parameters"""
    query: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    is_verified: Optional[bool] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    class Config:
        use_enum_values = True
