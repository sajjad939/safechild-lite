import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_chatbot_health():
    res = client.get("/api/chatbot/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data

def test_chatbot_chat_roundtrip():
    payload = {"message": "Hello", "session_id": "test-session"}
    res = client.post("/api/chatbot", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data.get("session_id") == "test-session"
    assert "response" in data

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
from api.chatbot import ChatbotAPI, ChatbotRequest, ChatbotResponse
from services.gptService import GPTService
from services.ttsService import TTSService
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

# Test client
client = TestClient(app)

class TestChatbotAPI:
    """Test class for ChatbotAPI"""
    
    @pytest.fixture
    def chatbot_api(self):
        """Create a ChatbotAPI instance for testing"""
        return ChatbotAPI()
    
    @pytest.fixture
    def mock_gpt_service(self):
        """Create a mock GPT service"""
        mock_service = Mock(spec=GPTService)
        mock_service.generate_response = AsyncMock(return_value="Test response")
        mock_service.analyze_safety_concerns.return_value = {
            "safety_score": 0.1,
            "concern_types": [],
            "urgency_level": "low",
            "recommended_actions": []
        }
        return mock_service
    
    @pytest.fixture
    def mock_tts_service(self):
        """Create a mock TTS service"""
        mock_service = Mock(spec=TTSService)
        mock_service.text_to_speech = AsyncMock(return_value={
            "audio_data": "base64_audio_data",
            "text": "Test text",
            "language": "en"
        })
        return mock_service
    
    def test_chatbot_api_initialization(self, chatbot_api):
        """Test ChatbotAPI initialization"""
        assert chatbot_api is not None
        assert hasattr(chatbot_api, 'chat_sessions')
        assert hasattr(chatbot_api, 'gpt_service')
        assert hasattr(chatbot_api, 'tts_service')
        assert hasattr(chatbot_api, 'text_cleaner')
        assert hasattr(chatbot_api, 'time_utils')
    
    def test_create_chat_session(self, chatbot_api):
        """Test chat session creation"""
        session = chatbot_api.create_chat_session()
        
        assert session is not None
        assert 'chat_id' in session
        assert 'created_at' in session
        assert 'messages' in session
        assert 'safety_context' in session
        assert session['messages'] == []
        assert session['safety_context']['safety_score'] == 0.0
    
    def test_get_chat_session(self, chatbot_api):
        """Test getting chat session"""
        # Create a session first
        session = chatbot_api.create_chat_session()
        chat_id = session['chat_id']
        
        # Get the session
        retrieved_session = chatbot_api.get_chat_session(chat_id)
        
        assert retrieved_session is not None
        assert retrieved_session['chat_id'] == chat_id
    
    def test_get_nonexistent_chat_session(self, chatbot_api):
        """Test getting non-existent chat session"""
        with pytest.raises(HTTPException) as exc_info:
            chatbot_api.get_chat_session("nonexistent_id")
        
        assert exc_info.value.status_code == 404
        assert "Chat session not found" in str(exc_info.value.detail)
    
    def test_update_chat_session(self, chatbot_api):
        """Test updating chat session"""
        # Create a session
        session = chatbot_api.create_chat_session()
        chat_id = session['chat_id']
        
        # Update with a message
        message = {
            "role": "user",
            "content": "Hello, I need help",
            "timestamp": "2023-01-01T00:00:00Z"
        }
        
        updated_session = chatbot_api.update_chat_session(chat_id, message)
        
        assert updated_session is not None
        assert len(updated_session['messages']) == 1
        assert updated_session['messages'][0]['content'] == "Hello, I need help"
    
    def test_update_safety_context(self, chatbot_api):
        """Test updating safety context"""
        # Create a session
        session = chatbot_api.create_chat_session()
        chat_id = session['chat_id']
        
        # Update safety context
        safety_update = {
            "safety_score": 0.8,
            "concern_types": ["high_risk"],
            "urgency_level": "high"
        }
        
        updated_session = chatbot_api.update_safety_context(chat_id, safety_update)
        
        assert updated_session is not None
        assert updated_session['safety_context']['safety_score'] == 0.8
        assert updated_session['safety_context']['concern_types'] == ["high_risk"]
        assert updated_session['safety_context']['urgency_level'] == "high"
    
    def test_analyze_safety_score(self, chatbot_api):
        """Test safety score analysis"""
        # Test low risk message
        low_risk_score = chatbot_api.analyze_safety_score("Hello, how are you?")
        assert low_risk_score < 0.3
        
        # Test medium risk message
        medium_risk_score = chatbot_api.analyze_safety_score("I'm feeling scared and worried")
        assert 0.3 <= medium_risk_score <= 0.7
        
        # Test high risk message
        high_risk_score = chatbot_api.analyze_safety_score("Someone hurt me and I'm bleeding")
        assert high_risk_score > 0.7
    
    def test_generate_suggested_actions(self, chatbot_api):
        """Test generating suggested actions"""
        # Test low risk actions
        low_risk_actions = chatbot_api.generate_suggested_actions(0.1)
        assert "Continue conversation" in low_risk_actions
        
        # Test high risk actions
        high_risk_actions = chatbot_api.generate_suggested_actions(0.8)
        assert "Contact trusted adult" in high_risk_actions
        assert "Emergency services" in high_risk_actions
    
    def test_should_trigger_emergency(self, chatbot_api):
        """Test emergency trigger logic"""
        # Test low risk - should not trigger
        assert not chatbot_api.should_trigger_emergency(0.1)
        
        # Test medium risk - should not trigger
        assert not chatbot_api.should_trigger_emergency(0.5)
        
        # Test high risk - should trigger
        assert chatbot_api.should_trigger_emergency(0.8)
        
        # Test critical risk - should trigger
        assert chatbot_api.should_trigger_emergency(0.95)

class TestChatbotEndpoints:
    """Test class for chatbot API endpoints"""
    
    def test_chatbot_health_check(self):
        """Test chatbot health check endpoint"""
        response = client.get("/api/chatbot/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chatbot"
        assert "timestamp" in data
    
    def test_chatbot_post_message(self):
        """Test posting a message to chatbot"""
        message_data = {
            "message": "Hello, I need help with safety",
            "chat_id": None,
            "user_context": {
                "age_group": "10-12",
                "emotional_state": "calm"
            }
        }
        
        response = client.post("/api/chatbot/", json=message_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "chat_id" in data
        assert "safety_score" in data
        assert "suggested_actions" in data
    
    def test_chatbot_get_history(self):
        """Test getting chat history"""
        # First create a chat session
        message_data = {
            "message": "Test message",
            "chat_id": None
        }
        
        create_response = client.post("/api/chatbot/", json=message_data)
        chat_id = create_response.json()["chat_id"]
        
        # Get chat history
        response = client.get(f"/api/chatbot/{chat_id}/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "chat_id" in data
        assert "messages" in data
        assert "created_at" in data
    
    def test_chatbot_get_stats(self):
        """Test getting chat statistics"""
        # First create a chat session
        message_data = {
            "message": "Test message",
            "chat_id": None
        }
        
        create_response = client.post("/api/chatbot/", json=message_data)
        chat_id = create_response.json()["chat_id"]
        
        # Get chat stats
        response = client.get(f"/api/chatbot/{chat_id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "chat_id" in data
        assert "message_count" in data
        assert "safety_score" in data
        assert "created_at" in data
    
    def test_chatbot_delete_session(self):
        """Test deleting a chat session"""
        # First create a chat session
        message_data = {
            "message": "Test message",
            "chat_id": None
        }
        
        create_response = client.post("/api/chatbot/", json=message_data)
        chat_id = create_response.json()["chat_id"]
        
        # Delete the session
        response = client.delete(f"/api/chatbot/{chat_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]
    
    def test_chatbot_invalid_chat_id(self):
        """Test accessing invalid chat ID"""
        response = client.get("/api/chatbot/invalid_id/history")
        assert response.status_code == 404
        
        response = client.get("/api/chatbot/invalid_id/stats")
        assert response.status_code == 404
        
        response = client.delete("/api/chatbot/invalid_id")
        assert response.status_code == 404

class TestChatbotIntegration:
    """Test class for chatbot integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test a complete conversation flow"""
        # This would test the full integration between components
        # For now, we'll test the basic flow
        
        # Test message processing
        message_data = {
            "message": "I'm feeling scared about something that happened at school",
            "chat_id": None,
            "user_context": {
                "age_group": "8-10",
                "emotional_state": "scared"
            }
        }
        
        response = client.post("/api/chatbot/", json=message_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["safety_score"] > 0.3  # Should detect some concern
        assert "Tell a trusted adult" in str(data["suggested_actions"])
    
    def test_emergency_keyword_detection(self):
        """Test detection of emergency keywords"""
        emergency_messages = [
            "Someone hurt me",
            "I'm bleeding",
            "I'm in pain",
            "Someone touched me inappropriately",
            "I'm scared and don't know what to do"
        ]
        
        for message in emergency_messages:
            message_data = {
                "message": message,
                "chat_id": None
            }
            
            response = client.post("/api/chatbot/", json=message_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["safety_score"] > 0.5  # Should detect high concern
            assert len(data["suggested_actions"]) > 0
    
    def test_safe_conversation_flow(self):
        """Test safe conversation flow"""
        safe_messages = [
            "Hello, how are you?",
            "Can you teach me about safety?",
            "What should I do if I get lost?",
            "How can I stay safe online?",
            "What are good touch and bad touch?"
        ]
        
        for message in safe_messages:
            message_data = {
                "message": message,
                "chat_id": None
            }
            
            response = client.post("/api/chatbot/", json=message_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["safety_score"] < 0.3  # Should be low concern
            assert "response" in data
            assert len(data["response"]) > 0

class TestChatbotValidation:
    """Test class for chatbot input validation"""
    
    def test_empty_message(self):
        """Test empty message validation"""
        message_data = {
            "message": "",
            "chat_id": None
        }
        
        response = client.post("/api/chatbot/", json=message_data)
        assert response.status_code == 422  # Validation error
    
    def test_very_long_message(self):
        """Test very long message validation"""
        long_message = "A" * 10001  # Exceeds max length
        
        message_data = {
            "message": long_message,
            "chat_id": None
        }
        
        response = client.post("/api/chatbot/", json=message_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_user_context(self):
        """Test invalid user context validation"""
        message_data = {
            "message": "Hello",
            "chat_id": None,
            "user_context": {
                "age_group": "invalid_age",
                "emotional_state": "invalid_state"
            }
        }
        
        response = client.post("/api/chatbot/", json=message_data)
        # Should still work but with default values
        assert response.status_code == 200

# Run tests
if __name__ == "__main__":
    pytest.main([__file__])
