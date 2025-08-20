import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.7
    
    # AI Provider
    ai_provider: str = "openai"
    aiml_base_url: str = "http://localhost:8001"
    aiml_api_key: str = ""
    aiml_model: str = "default"
    
    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # TTS
    tts_default_language: str = "en"
    tts_default_slow: bool = False
    tts_audio_format: str = "mp3"
    tts_cache_dir: str = "temp/audio_cache"
    tts_max_cache_size_mb: int = 100
    tts_cache_ttl_hours: int = 24
    
    # PDF
    pdf_templates_dir: str = "templates/documents"
    pdf_output_dir: str = "temp/documents"
    pdf_default_page_size: str = "A4"
    pdf_default_font_size: int = 12
    pdf_default_margin: float = 1.0
    
    # SMS
    sms_max_length: int = 160
    sms_default_country: str = "+1"
    sms_retry_attempts: int = 3
    sms_retry_delay_seconds: int = 5
    sms_max_per_hour: int = 100
    sms_max_per_day: int = 1000
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:8501",
        "http://localhost:3000",
        "https://safechild-lite.vercel.app"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()