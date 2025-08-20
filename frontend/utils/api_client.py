import requests
import streamlit as st
import logging
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class APIClient:
    """Client for communicating with SafeChild backend API"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SafeChild-Frontend/1.0'
        })
    
    def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def chat_with_bot(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message to chatbot"""
        try:
            payload = {
                "message": message,
                "session_id": session_id
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chatbot",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def submit_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit complaint to backend"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/complaint",
                json=complaint_data,
                timeout=60  # Longer timeout for complaint generation
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Complaint submission failed: {e}")
            return {"success": False, "error": str(e)}
    
    def trigger_emergency(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger emergency alert"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/emergency",
                json=emergency_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Emergency trigger failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_awareness_content(self, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get awareness content with optional filters"""
        try:
            params = filters or {}
            
            response = self.session.get(
                f"{self.base_url}/api/awareness/content",
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Awareness content request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def convert_text_to_speech(self, text: str, language: str = "en", speed: str = "normal") -> Dict[str, Any]:
        """Convert text to speech"""
        try:
            payload = {
                "text": text,
                "language": language,
                "speed": speed
            }
            
            response = self.session.post(
                f"{self.base_url}/api/tts",
                json=payload,
                timeout=60  # Longer timeout for TTS
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"TTS request failed: {e}")
            return {"success": False, "error": str(e)}