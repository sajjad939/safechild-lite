import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_emergency_health():
    res = client.get("/api/emergency/health")
    assert res.status_code == 200

def test_trigger_emergency_minimal():
    payload = {
        "location": "School Gate",
        "description": "Child reported feeling unsafe",
        "contacts": [
            {"name": "Parent A", "phone": "+15557654321", "relationship": "Parent"}
        ]
    }
    res = client.post("/api/emergency", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("active", "created")
    assert data["alert_id"]

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import the application and components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
from api.emergency import EmergencyAPI, EmergencyRequest, EmergencyResponse, EmergencyContact
from services.smsService import SMSService
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

# Test client
client = TestClient(app)

class TestEmergencyAPI:
    """Test class for EmergencyAPI"""
    
    @pytest.fixture
    def emergency_api(self):
        """Create an EmergencyAPI instance for testing"""
        return EmergencyAPI()
    
    @pytest.fixture
    def mock_sms_service(self):
        """Create a mock SMS service"""
        mock_service = Mock(spec=SMSService)
        mock_service.send_emergency_sms = AsyncMock(return_value=True)
        return mock_service
    
    def test_emergency_api_initialization(self, emergency_api):
        """Test EmergencyAPI initialization"""
        assert emergency_api is not None
        assert hasattr(emergency_api, 'sms_service')
        assert hasattr(emergency_api, 'text_cleaner')
        assert hasattr(emergency_api, 'time_utils')
        assert hasattr(emergency_api, 'emergency_alerts')
        assert hasattr(emergency_api, 'emergency_levels')
        assert hasattr(emergency_api, 'critical_keywords')
        assert hasattr(emergency_api, 'high_keywords')
    
    def test_create_alert_id(self, emergency_api):
        """Test emergency alert ID generation"""
        alert_id = emergency_api.create_alert_id()
        
        assert alert_id is not None
        assert alert_id.startswith("EMG_")
        assert len(alert_id) > 10
        assert "_" in alert_id
    
    def test_determine_emergency_level(self, emergency_api):
        """Test emergency level determination"""
        # Test critical level
        critical_description = "Someone hurt me and I'm bleeding"
        level = emergency_api.determine_emergency_level(critical_description)
        assert level == "critical"
        
        # Test high level
        high_description = "I'm feeling scared and someone is following me"
        level = emergency_api.determine_emergency_level(high_description)
        assert level == "high"
        
        # Test medium level
        medium_description = "I got lost at the mall"
        level = emergency_api.determine_emergency_level(medium_description)
        assert level == "medium"
        
        # Test low level
        low_description = "I'm worried about my homework"
        level = emergency_api.determine_emergency_level(low_description)
        assert level == "low"
    
    def test_generate_next_steps(self, emergency_api):
        """Test generating next steps based on emergency level"""
        # Test critical level steps
        critical_steps = emergency_api.generate_next_steps("critical", "Critical emergency")
        assert "Call 911 immediately" in critical_steps
        assert "Stay on the line" in critical_steps
        
        # Test high level steps
        high_steps = emergency_api.generate_next_steps("high", "High risk situation")
        assert "Contact emergency services" in high_steps
        assert "Notify all emergency contacts" in high_steps
        
        # Test medium level steps
        medium_steps = emergency_api.generate_next_steps("medium", "Medium concern")
        assert "Contact emergency contacts" in medium_steps
        assert "Monitor situation closely" in medium_steps
        
        # Test low level steps
        low_steps = emergency_api.generate_next_steps("low", "Low concern")
        assert "Inform emergency contacts" in low_steps
        assert "Monitor situation" in low_steps
    
    def test_validate_emergency_data_valid(self, emergency_api):
        """Test validation of valid emergency data"""
        valid_data = EmergencyRequest(
            location="123 Main St, City",
            description="I'm feeling unsafe",
            contacts=[
                EmergencyContact(
                    name="Parent",
                    phone="123-456-7890",
                    relationship="parent"
                )
            ]
        )
        
        errors = emergency_api.validate_emergency_data(valid_data)
        assert len(errors) == 0
    
    def test_validate_emergency_data_invalid(self, emergency_api):
        """Test validation of invalid emergency data"""
        invalid_data = EmergencyRequest(
            location="",  # Empty location
            description="",  # Empty description
            contacts=[]  # Empty contacts
        )
        
        errors = emergency_api.validate_emergency_data(invalid_data)
        assert len(errors) > 0
        assert "Location is required" in errors
        assert "Emergency description is required" in errors
        assert "At least one emergency contact is required" in errors
    
    def test_validate_emergency_data_invalid_contacts(self, emergency_api):
        """Test validation of emergency data with invalid contacts"""
        invalid_data = EmergencyRequest(
            location="123 Main St",
            description="Test emergency",
            contacts=[
                EmergencyContact(
                    name="",  # Empty name
                    phone="",  # Empty phone
                    relationship="parent"
                )
            ]
        )
        
        errors = emergency_api.validate_emergency_data(invalid_data)
        assert len(errors) > 0
        assert "Contact name is required" in errors
        assert "Contact phone number is required" in errors
    
    def test_create_emergency_message(self, emergency_api):
        """Test creating emergency SMS message"""
        # Create a test alert
        alert = Mock()
        alert.location = "123 Main St"
        alert.emergency_level = "high"
        alert.description = "Test emergency"
        alert.timestamp = "2023-01-01T14:30:00Z"
        
        # Create a test contact
        contact = EmergencyContact(
            name="Test Contact",
            phone="123-456-7890",
            relationship="parent"
        )
        
        message = emergency_api.create_emergency_message(alert, contact)
        
        assert message is not None
        assert len(message) > 0
        assert "EMERGENCY ALERT" in message
        assert "Test Contact" in message
        assert "123 Main St" in message
        assert "HIGH" in message
        assert "Test emergency" in message

class TestEmergencyEndpoints:
    """Test class for emergency API endpoints"""
    
    def test_emergency_health_check(self):
        """Test emergency health check endpoint"""
        response = client.get("/api/emergency/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "emergency"
        assert "timestamp" in data
        assert "active_alerts" in data
        assert "total_alerts" in data
    
    def test_trigger_emergency(self):
        """Test triggering an emergency alert"""
        emergency_data = {
            "location": "123 Main St, City",
            "description": "I'm feeling unsafe and need help",
            "contacts": [
                {
                    "name": "Parent",
                    "phone": "123-456-7890",
                    "relationship": "parent"
                }
            ]
        }
        
        response = client.post("/api/emergency/", json=emergency_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "alert_id" in data
        assert "status" in data
        assert "timestamp" in data
        assert "contacts_notified" in data
        assert "emergency_level" in data
        assert "next_steps" in data
    
    def test_get_emergency_alert(self):
        """Test getting an emergency alert by ID"""
        # First trigger an emergency
        emergency_data = {
            "location": "123 Main St",
            "description": "Test emergency",
            "contacts": [
                {
                    "name": "Parent",
                    "phone": "123-456-7890",
                    "relationship": "parent"
                }
            ]
        }
        
        trigger_response = client.post("/api/emergency/", json=emergency_data)
        alert_id = trigger_response.json()["alert_id"]
        
        # Get the alert
        response = client.get(f"/api/emergency/{alert_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["alert_id"] == alert_id
        assert "location" in data
        assert "description" in data
        assert "contacts" in data
        assert "status" in data
    
    def test_get_all_emergency_alerts(self):
        """Test getting all emergency alerts"""
        response = client.get("/api/emergency/")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
    
    def test_get_alert_status(self):
        """Test getting emergency alert status"""
        # First trigger an emergency
        emergency_data = {
            "location": "123 Main St",
            "description": "Test emergency",
            "contacts": [
                {
                    "name": "Parent",
                    "phone": "123-456-7890",
                    "relationship": "parent"
                }
            ]
        }
        
        trigger_response = client.post("/api/emergency/", json=emergency_data)
        alert_id = trigger_response.json()["alert_id"]
        
        # Get alert status
        response = client.get(f"/api/emergency/{alert_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["alert_id"] == alert_id
        assert "status" in data
        assert "emergency_level" in data
        assert "timestamp" in data
        assert "contacts_notified" in data
    
    def test_update_alert_status(self):
        """Test updating emergency alert status"""
        # First trigger an emergency
        emergency_data = {
            "location": "123 Main St",
            "description": "Test emergency",
            "contacts": [
                {
                    "name": "Parent",
                    "phone": "123-456-7890",
                    "relationship": "parent"
                }
            ]
        }
        
        trigger_response = client.post("/api/emergency/", json=emergency_data)
        alert_id = trigger_response.json()["alert_id"]
        
        # Update status
        response = client.put(f"/api/emergency/{alert_id}/status?status=resolved")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "resolved"
    
    def test_get_emergency_statistics(self):
        """Test getting emergency alert statistics"""
        response = client.get("/api/emergency/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_alerts" in data
        assert "active_alerts" in data
        assert "resolved_alerts" in data
        assert "level_distribution" in data
        assert "last_24_hours" in data
    
    def test_delete_emergency_alert(self):
        """Test deleting an emergency alert"""
        # First trigger an emergency
        emergency_data = {
            "location": "123 Main St",
            "description": "Test emergency",
            "contacts": [
                {
                    "name": "Parent",
                    "phone": "123-456-7890",
                    "relationship": "parent"
                }
            ]
        }
        
        trigger_response = client.post("/api/emergency/", json=emergency_data)
        alert_id = trigger_response.json()["alert_id"]
        
        # Delete the alert
        response = client.delete(f"/api/emergency/{alert_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]
    
    def test_emergency_invalid_id(self):
        """Test accessing invalid emergency alert ID"""
        response = client.get("/api/emergency/invalid_id")
        assert response.status_code == 404
        
        response = client.get("/api/emergency/invalid_id/status")
        assert response.status_code == 404
        
        response = client.put("/api/emergency/invalid_id/status?status=resolved")
        assert response.status_code == 404
        
        response = client.delete("/api/emergency/invalid_id")
        assert response.status_code == 404

class TestEmergencyValidation:
    """Test class for emergency input validation"""
    
    def test_empty_required_fields(self):
        """Test validation of empty required fields"""
        emergency_data = {
            "location": "",
            "description": "",
            "contacts": []
        }
        
        response = client.post("/api/emergency/", json=emergency_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Validation errors" in data["detail"]
    
    def test_invalid_contacts(self):
        """Test validation of invalid contacts"""
        emergency_data = {
            "location": "123 Main St",
            "description": "Test emergency",
            "contacts": [
                {
                    "name": "",
                    "phone": "",
                    "relationship": "parent"
                }
            ]
        }
        
        response = client.post("/api/emergency/", json=emergency_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Validation errors" in data["detail"]
    
    def test_missing_contacts(self):
        """Test validation of missing contacts"""
        emergency_data = {
            "location": "123 Main St",
            "description": "Test emergency",
            "contacts": []
        }
        
        response = client.post("/api/emergency/", json=emergency_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Validation errors" in data["detail"]
        assert "At least one emergency contact is required" in data["detail"]

class TestEmergencyIntegration:
    """Test class for emergency integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_emergency_flow(self):
        """Test a complete emergency flow"""
        # Trigger emergency
        emergency_data = {
            "location": "123 Main St, City",
            "description": "I'm feeling unsafe and someone is following me",
            "contacts": [
                {
                    "name": "Parent",
                    "phone": "123-456-7890",
                    "relationship": "parent"
                },
                {
                    "name": "Guardian",
                    "phone": "098-765-4321",
                    "relationship": "guardian"
                }
            ]
        }
        
        response = client.post("/api/emergency/", json=emergency_data)
        assert response.status_code == 200
        
        data = response.json()
        alert_id = data["alert_id"]
        
        # Verify emergency was created
        assert data["status"] == "active"
        assert data["emergency_level"] in ["high", "critical"]
        assert len(data["contacts_notified"]) == 2
        assert len(data["next_steps"]) > 0
        
        # Get alert details
        get_response = client.get(f"/api/emergency/{alert_id}")
        assert get_response.status_code == 200
        
        # Get alert status
        status_response = client.get(f"/api/emergency/{alert_id}/status")
        assert status_response.status_code == 200
        
        # Update status
        update_response = client.put(f"/api/emergency/{alert_id}/status?status=resolved")
        assert update_response.status_code == 200
        
        # Get statistics
        stats_response = client.get("/api/emergency/statistics")
        assert stats_response.status_code == 200
        
        # Clean up
        delete_response = client.delete(f"/api/emergency/{alert_id}")
        assert delete_response.status_code == 200
    
    def test_emergency_level_detection(self):
        """Test automatic emergency level detection"""
        test_cases = [
            {
                "description": "I'm bleeding and in pain",
                "expected_level": "critical"
            },
            {
                "description": "Someone is following me and I'm scared",
                "expected_level": "high"
            },
            {
                "description": "I got lost at the mall",
                "expected_level": "medium"
            },
            {
                "description": "I'm worried about my homework",
                "expected_level": "low"
            }
        ]
        
        for test_case in test_cases:
            emergency_data = {
                "location": "123 Main St",
                "description": test_case["description"],
                "contacts": [
                    {
                        "name": "Parent",
                        "phone": "123-456-7890",
                        "relationship": "parent"
                    }
                ]
            }
            
            response = client.post("/api/emergency/", json=emergency_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["emergency_level"] == test_case["expected_level"]
            
            # Clean up
            alert_id = data["alert_id"]
            client.delete(f"/api/emergency/{alert_id}")

# Run tests
if __name__ == "__main__":
    pytest.main([__file__])
