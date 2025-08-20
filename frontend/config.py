import os
import streamlit as st

class FrontendConfig:
    """Frontend configuration management"""
    
    def __init__(self):
        # Backend URL configuration
        self.backend_url = self._get_backend_url()
        
        # UI Configuration
        self.page_title = "SafeChild-Lite"
        self.page_icon = "🛡️"
        self.layout = "wide"
        
        # Theme configuration
        self.primary_color = "#4CAF50"
        self.background_color = "#FFFFFF"
        self.secondary_color = "#2196F3"
        self.text_color = "#333333"
        
        # Feature flags
        self.enable_audio = True
        self.enable_emergency = True
        self.enable_complaints = True
        self.enable_awareness = True
        
        # API timeouts
        self.api_timeout = 30
        self.health_check_timeout = 5
    
    def _get_backend_url(self) -> str:
        """Get backend URL from various sources"""
        # Try Streamlit secrets first
        try:
            if hasattr(st, 'secrets') and 'BACKEND_URL' in st.secrets:
                return st.secrets['BACKEND_URL']
        except:
            pass
        
        # Try environment variable
        backend_url = os.getenv('BACKEND_URL')
        if backend_url:
            return backend_url
        
        # Default to localhost
        return "http://localhost:8000"
    
    def get_page_config(self) -> dict:
        """Get Streamlit page configuration"""
        return {
            "page_title": self.page_title,
            "page_icon": self.page_icon,
            "layout": self.layout,
            "initial_sidebar_state": "expanded"
        }

# Global config instance
config = FrontendConfig()