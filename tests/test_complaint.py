import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def valid_payload():
    return {
        "child_name": "Alex Doe",
        "child_age": 10,
        "child_gender": "male",
        "child_school": "Sunrise Elementary",
        "child_grade": "5",
        "incident_date": "2024-05-01",
        "incident_time": "13:30",
        "location": "Playground",
        "incident_type": "bullying",
        "incident_description": "Child was pushed and called names by peers.",
        "guardian_name": "Jane Doe",
        "guardian_phone": "+15551234567"
    }

def test_complaint_health():
    res = client.get("/api/complaint/health")
    assert res.status_code == 200

def test_submit_complaint_and_download_pdf():
    res = client.post("/api/complaint", json=valid_payload())
    assert res.status_code == 200
    data = res.json()
    comp_id = data["complaint_id"]

    res_dl = client.get(f"/api/complaint/{comp_id}/download/pdf")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"].startswith("application/pdf")

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
from api.complaint import ComplaintAPI, ComplaintRequest, ComplaintResponse
from services.gptService import GPTService
from services.pdfService import PDFService
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

# Test client
client = TestClient(app)

class TestComplaintAPI:
    """Test class for ComplaintAPI"""
    
    @pytest.fixture
    def complaint_api(self):
        """Create a ComplaintAPI instance for testing"""
        return ComplaintAPI()
    
    @pytest.fixture
    def mock_gpt_service(self):
        """Create a mock GPT service"""
        mock_service = Mock(spec=GPTService)
        mock_service.generate_complaint_draft = AsyncMock(return_value="Test complaint draft")
        return mock_service
    
    @pytest.fixture
    def mock_pdf_service(self):
        """Create a mock PDF service"""
        mock_service = Mock(spec=PDFService)
        mock_service.generate_complaint_pdf = AsyncMock(return_value=b"test_pdf_content")
        mock_service.generate_complaint_word = AsyncMock(return_value=b"test_word_content")
        return mock_service
    
    def test_complaint_api_initialization(self, complaint_api):
        """Test ComplaintAPI initialization"""
        assert complaint_api is not None
        assert hasattr(complaint_api, 'gpt_service')
        assert hasattr(complaint_api, 'pdf_service')
        assert hasattr(complaint_api, 'text_cleaner')
        assert hasattr(complaint_api, 'time_utils')
        assert hasattr(complaint_api, 'complaints')
        assert hasattr(complaint_api, 'complaint_templates')
    
    def test_create_complaint_id(self, complaint_api):
        """Test complaint ID generation"""
        complaint_id = complaint_api.create_complaint_id()
        
        assert complaint_id is not None
        assert complaint_id.startswith("COMP_")
        assert len(complaint_id) > 10
        assert "_" in complaint_id
    
    def test_validate_complaint_data_valid(self, complaint_api):
        """Test validation of valid complaint data"""
        valid_data = ComplaintRequest(
            child_name="Test Child",
            child_age=10,
            incident_date="2023-01-01",
            incident_time="14:30",
            location="School playground",
            incident_description="Detailed description of the incident",
            guardian_name="Test Guardian",
            guardian_phone="123-456-7890"
        )
        
        errors = complaint_api.validate_complaint_data(valid_data)
        assert len(errors) == 0
    
    def test_validate_complaint_data_invalid(self, complaint_api):
        """Test validation of invalid complaint data"""
        invalid_data = ComplaintRequest(
            child_name="",  # Empty name
            child_age=25,   # Invalid age
            incident_date="2023-01-01",
            incident_time="14:30",
            location="",    # Empty location
            incident_description="",  # Empty description
            guardian_name="",  # Empty guardian name
            guardian_phone=""   # Empty phone
        )
        
        errors = complaint_api.validate_complaint_data(invalid_data)
        assert len(errors) > 0
        assert "Child's name is required" in errors
        assert "Child's age must be between 1 and 18" in errors
        assert "Location is required" in errors
        assert "Incident description is required" in errors
        assert "Guardian's name is required" in errors
        assert "Guardian's phone number is required" in errors
    
    def test_get_complaint_template(self, complaint_api):
        """Test getting complaint templates"""
        # Test existing template
        template = complaint_api.get_complaint_template("physical_abuse")
        assert template is not None
        assert len(template) > 0
        assert "OFFICIAL COMPLAINT" in template
        
        # Test non-existing template (should return default)
        template = complaint_api.get_complaint_template("non_existent")
        assert template is not None
        assert len(template) > 0
        assert "OFFICIAL COMPLAINT" in template
    
    def test_generate_from_template(self, complaint_api):
        """Test generating complaint from template"""
        test_data = ComplaintRequest(
            child_name="Test Child",
            child_age=10,
            incident_date="2023-01-01",
            incident_time="14:30",
            location="School",
            incident_description="Test incident",
            guardian_name="Test Guardian",
            guardian_phone="123-456-7890"
        )
        
        complaint_text = complaint_api.generate_from_template(test_data)
        
        assert complaint_text is not None
        assert len(complaint_text) > 0
        assert "Test Child" in complaint_text
        assert "10" in complaint_text
        assert "School" in complaint_text
        assert "Test incident" in complaint_text
        assert "Test Guardian" in complaint_text
        assert "123-456-7890" in complaint_text
    
    def test_create_complaint_prompt(self, complaint_api):
        """Test creating complaint prompt"""
        test_data = ComplaintRequest(
            child_name="Test Child",
            child_age=10,
            incident_date="2023-01-01",
            incident_time="14:30",
            location="School",
            incident_description="Test incident",
            guardian_name="Test Guardian",
            guardian_phone="123-456-7890"
        )
        
        prompt = complaint_api.create_complaint_prompt(test_data)
        
        assert prompt is not None
        assert len(prompt) > 0
        assert "Test Child" in prompt
        assert "10" in prompt
        assert "School" in prompt
        assert "Test incident" in prompt
        assert "Test Guardian" in prompt
        assert "123-456-7890" in prompt
        assert "Generate a professional" in prompt

class TestComplaintEndpoints:
    """Test class for complaint API endpoints"""
    
    def test_complaint_health_check(self):
        """Test complaint health check endpoint"""
        response = client.get("/api/complaint/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "complaint"
        assert "timestamp" in data
        assert "total_complaints" in data
    
    def test_submit_complaint(self):
        """Test submitting a complaint"""
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School playground",
            "incident_type": "bullying",
            "incident_description": "Detailed description of the bullying incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        response = client.post("/api/complaint/", json=complaint_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "complaint_id" in data
        assert "status" in data
        assert "complaint_text" in data
        assert "submission_timestamp" in data
        assert "generated_at" in data
        assert "download_urls" in data
    
    def test_get_complaint(self):
        """Test getting a complaint by ID"""
        # First submit a complaint
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "bullying",
            "incident_description": "Test incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        submit_response = client.post("/api/complaint/", json=complaint_data)
        complaint_id = submit_response.json()["complaint_id"]
        
        # Get the complaint
        response = client.get(f"/api/complaint/{complaint_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["complaint_id"] == complaint_id
        assert "status" in data
        assert "complaint_text" in data
    
    def test_get_all_complaints(self):
        """Test getting all complaints"""
        response = client.get("/api/complaint/")
        assert response.status_code == 200
        
        data = response.json()
        assert "complaints" in data
        assert isinstance(data["complaints"], list)
    
    def test_download_pdf(self):
        """Test downloading complaint as PDF"""
        # First submit a complaint
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "bullying",
            "incident_description": "Test incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        submit_response = client.post("/api/complaint/", json=complaint_data)
        complaint_id = submit_response.json()["complaint_id"]
        
        # Download PDF
        response = client.get(f"/api/complaint/{complaint_id}/pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "complaint_" in response.headers["content-disposition"]
    
    def test_download_word(self):
        """Test downloading complaint as Word document"""
        # First submit a complaint
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "bullying",
            "incident_description": "Test incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        submit_response = client.post("/api/complaint/", json=complaint_data)
        complaint_id = submit_response.json()["complaint_id"]
        
        # Download Word document
        response = client.get(f"/api/complaint/{complaint_id}/word")
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
        assert "complaint_" in response.headers["content-disposition"]
    
    def test_update_complaint_status(self):
        """Test updating complaint status"""
        # First submit a complaint
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "bullying",
            "incident_description": "Test incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        submit_response = client.post("/api/complaint/", json=complaint_data)
        complaint_id = submit_response.json()["complaint_id"]
        
        # Update status
        response = client.put(f"/api/complaint/{complaint_id}/status?status=under_review")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "under_review"
    
    def test_delete_complaint(self):
        """Test deleting a complaint"""
        # First submit a complaint
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "bullying",
            "incident_description": "Test incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        submit_response = client.post("/api/complaint/", json=complaint_data)
        complaint_id = submit_response.json()["complaint_id"]
        
        # Delete the complaint
        response = client.delete(f"/api/complaint/{complaint_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]
    
    def test_complaint_invalid_id(self):
        """Test accessing invalid complaint ID"""
        response = client.get("/api/complaint/invalid_id")
        assert response.status_code == 404
        
        response = client.get("/api/complaint/invalid_id/pdf")
        assert response.status_code == 404
        
        response = client.get("/api/complaint/invalid_id/word")
        assert response.status_code == 404
        
        response = client.put("/api/complaint/invalid_id/status?status=under_review")
        assert response.status_code == 404
        
        response = client.delete("/api/complaint/invalid_id")
        assert response.status_code == 404

class TestComplaintValidation:
    """Test class for complaint input validation"""
    
    def test_empty_required_fields(self):
        """Test validation of empty required fields"""
        complaint_data = {
            "child_name": "",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "",
            "incident_type": "bullying",
            "incident_description": "",
            "guardian_name": "",
            "guardian_phone": ""
        }
        
        response = client.post("/api/complaint/", json=complaint_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Validation errors" in data["detail"]
    
    def test_invalid_child_age(self):
        """Test validation of invalid child age"""
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 25,  # Invalid age
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "bullying",
            "incident_description": "Test incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        response = client.post("/api/complaint/", json=complaint_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Validation errors" in data["detail"]
        assert "Child's age must be between 1 and 18" in data["detail"]
    
    def test_invalid_incident_type(self):
        """Test validation of invalid incident type"""
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "invalid_type",  # Invalid type
            "incident_description": "Test incident",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        response = client.post("/api/complaint/", json=complaint_data)
        assert response.status_code == 422  # Pydantic validation error
    
    def test_short_incident_description(self):
        """Test validation of short incident description"""
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School",
            "incident_type": "bullying",
            "incident_description": "Short",  # Too short
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890"
        }
        
        response = client.post("/api/complaint/", json=complaint_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Validation errors" in data["detail"]
        assert "Incident description is required" in data["detail"]

class TestComplaintIntegration:
    """Test class for complaint integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_complaint_flow(self):
        """Test a complete complaint flow"""
        # Submit complaint
        complaint_data = {
            "child_name": "Test Child",
            "child_age": 10,
            "incident_date": "2023-01-01",
            "incident_time": "14:30",
            "location": "School playground",
            "incident_type": "bullying",
            "incident_description": "Detailed description of the bullying incident that occurred during recess",
            "guardian_name": "Test Guardian",
            "guardian_phone": "123-456-7890",
            "wants_legal_action": True,
            "wants_mediation": False
        }
        
        response = client.post("/api/complaint/", json=complaint_data)
        assert response.status_code == 200
        
        data = response.json()
        complaint_id = data["complaint_id"]
        
        # Verify complaint was created
        assert data["status"] == "Draft Generated"
        assert len(data["complaint_text"]) > 0
        assert "download_urls" in data
        
        # Get complaint details
        get_response = client.get(f"/api/complaint/{complaint_id}")
        assert get_response.status_code == 200
        
        # Update status
        update_response = client.put(f"/api/complaint/{complaint_id}/status?status=under_review")
        assert update_response.status_code == 200
        
        # Download documents
        pdf_response = client.get(f"/api/complaint/{complaint_id}/pdf")
        assert pdf_response.status_code == 200
        
        word_response = client.get(f"/api/complaint/{complaint_id}/word")
        assert word_response.status_code == 200
        
        # Clean up
        delete_response = client.delete(f"/api/complaint/{complaint_id}")
        assert delete_response.status_code == 200

# Run tests
if __name__ == "__main__":
    pytest.main([__file__])
