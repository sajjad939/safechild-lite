import os
import io
import logging
import asyncio
from typing import Dict, Any, Optional, BinaryIO
from gtts import gTTS
from gtts.lang import tts_langs
import tempfile
import uuid
from pathlib import Path

from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

logger = logging.getLogger(__name__)

class TTSService:
    """Service for Text-to-Speech conversion using gTTS"""
    
    def __init__(self):
        self.text_cleaner = TextCleaner()
        self.time_utils = TimeUtils()
        
        # Default TTS settings
        self.default_language = os.getenv("TTS_DEFAULT_LANGUAGE", "en")
        self.default_slow = os.getenv("TTS_DEFAULT_SLOW", "false").lower() == "true"
        self.audio_format = os.getenv("TTS_AUDIO_FORMAT", "mp3")
        self.audio_quality = os.getenv("TTS_AUDIO_QUALITY", "high")
        
        # Supported languages
        self.supported_languages = self._get_supported_languages()
        
        # Audio cache directory
        self.cache_dir = Path(os.getenv("TTS_CACHE_DIR", "temp/audio_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache settings
        self.max_cache_size = int(os.getenv("TTS_MAX_CACHE_SIZE_MB", "100")) * 1024 * 1024  # Convert to bytes
        self.cache_ttl_hours = int(os.getenv("TTS_CACHE_TTL_HOURS", "24"))
        
        logger.info(f"TTS Service initialized with language: {self.default_language}")
    
    async def convert_text_to_speech(
        self, 
        text: str, 
        language: Optional[str] = None, 
        slow: Optional[bool] = None,
        audio_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert text to speech and return audio data"""
        try:
            # Clean and validate input text
            cleaned_text = self.text_cleaner.clean_text(text)
            if not cleaned_text:
                return {
                    "success": False,
                    "error": "Invalid or empty text input",
                    "audio_data": None
                }
            
            # Set parameters
            lang = language or self.default_language
            slow_speech = slow if slow is not None else self.default_slow
            format_type = audio_format or self.audio_format
            
            # Validate language
            if lang not in self.supported_languages:
                return {
                    "success": False,
                    "error": f"Unsupported language: {lang}",
                    "supported_languages": list(self.supported_languages.keys()),
                    "audio_data": None
                }
            
            # Check cache first
            cache_key = self._generate_cache_key(cleaned_text, lang, slow_speech, format_type)
            cached_audio = await self._get_cached_audio(cache_key)
            if cached_audio:
                return {
                    "success": True,
                    "audio_data": cached_audio,
                    "cached": True,
                    "language": lang,
                    "slow": slow_speech,
                    "format": format_type,
                    "timestamp": self.time_utils.get_current_timestamp()
                }
            
            # Convert text to speech
            audio_data = await self._generate_speech(cleaned_text, lang, slow_speech, format_type)
            if not audio_data:
                return {
                    "success": False,
                    "error": "Failed to generate speech audio",
                    "audio_data": None
                }
            
            # Cache the audio
            await self._cache_audio(cache_key, audio_data)
            
            # Clean up old cache files
            await self._cleanup_cache()
            
            return {
                "success": True,
                "audio_data": audio_data,
                "cached": False,
                "language": lang,
                "slow": slow_speech,
                "format": format_type,
                "timestamp": self.time_utils.get_current_timestamp(),
                "text_length": len(cleaned_text),
                "audio_size": len(audio_data)
            }
            
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return {
                "success": False,
                "error": f"TTS conversion failed: {str(e)}",
                "audio_data": None
            }
    
    async def convert_safety_message(
        self, 
        message: str, 
        urgency_level: str = "normal",
        target_age: str = "child"
    ) -> Dict[str, Any]:
        """Convert safety message to speech with appropriate settings"""
        try:
            # Adjust speech parameters based on urgency and target age
            slow = False
            language = self.default_language
            
            if urgency_level == "high":
                slow = True  # Slower speech for urgent messages
            elif urgency_level == "emergency":
                slow = False  # Normal speed for emergency (clarity)
            
            if target_age == "child":
                slow = True  # Slower speech for children
            elif target_age == "toddler":
                slow = True
                # Could add language selection for very young children
            
            # Clean message text
            cleaned_message = self.text_cleaner.clean_text(message)
            if not cleaned_message:
                return {
                    "success": False,
                    "error": "Invalid safety message",
                    "audio_data": None
                }
            
            # Convert to speech
            result = await self.convert_text_to_speech(
                cleaned_message, 
                language=language, 
                slow=slow
            )
            
            if result["success"]:
                result["urgency_level"] = urgency_level
                result["target_age"] = target_age
                result["message_type"] = "safety"
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting safety message: {e}")
            return {
                "success": False,
                "error": f"Safety message conversion failed: {str(e)}",
                "audio_data": None
            }
    
    async def batch_convert(
        self, 
        texts: list, 
        language: Optional[str] = None,
        slow: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Convert multiple texts to speech in batch"""
        try:
            if not texts or len(texts) > 10:  # Limit batch size
                return {
                    "success": False,
                    "error": "Invalid batch size. Must be between 1 and 10 texts.",
                    "results": []
                }
            
            results = []
            for i, text in enumerate(texts):
                result = await self.convert_text_to_speech(
                    text, 
                    language=language, 
                    slow=slow
                )
                result["index"] = i
                results.append(result)
                
                # Small delay between conversions to avoid overwhelming the service
                await asyncio.sleep(0.1)
            
            success_count = sum(1 for r in results if r["success"])
            
            return {
                "success": success_count > 0,
                "total_texts": len(texts),
                "successful_conversions": success_count,
                "failed_conversions": len(texts) - success_count,
                "results": results,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error in batch TTS conversion: {e}")
            return {
                "success": False,
                "error": f"Batch conversion failed: {str(e)}",
                "results": []
            }
    
    async def get_available_languages(self) -> Dict[str, Any]:
        """Get list of available languages and their details"""
        try:
            return {
                "success": True,
                "languages": self.supported_languages,
                "default_language": self.default_language,
                "total_languages": len(self.supported_languages),
                "timestamp": self.time_utils.get_current_timestamp()
            }
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            return {
                "success": False,
                "error": f"Failed to get languages: {str(e)}",
                "languages": {}
            }
    
    async def get_audio_info(self, audio_data: bytes) -> Dict[str, Any]:
        """Get information about audio data"""
        try:
            if not audio_data:
                return {
                    "success": False,
                    "error": "No audio data provided"
                }
            
            # Basic audio information
            audio_size = len(audio_data)
            duration_estimate = self._estimate_audio_duration(audio_size)
            
            return {
                "success": True,
                "audio_size_bytes": audio_size,
                "audio_size_mb": round(audio_size / (1024 * 1024), 2),
                "estimated_duration_seconds": duration_estimate,
                "format": self.audio_format,
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {
                "success": False,
                "error": f"Failed to get audio info: {str(e)}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check TTS service health"""
        try:
            # Test TTS conversion with a simple text
            test_result = await self.convert_text_to_speech("Hello", language="en", slow=False)
            
            return {
                "status": "healthy" if test_result["success"] else "unhealthy",
                "service": "TTS",
                "default_language": self.default_language,
                "supported_languages_count": len(self.supported_languages),
                "cache_directory": str(self.cache_dir),
                "cache_size_mb": round(self._get_cache_size() / (1024 * 1024), 2),
                "test_conversion": test_result["success"],
                "timestamp": self.time_utils.get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"TTS service health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "TTS",
                "error": str(e),
                "timestamp": self.time_utils.get_current_timestamp()
            }
    
    def _get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages for TTS"""
        try:
            return tts_langs()
        except Exception as e:
            logger.warning(f"Could not get TTS languages: {e}")
            # Fallback to common languages
            return {
                "en": "English",
                "es": "Spanish",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese",
                "ru": "Russian",
                "ja": "Japanese",
                "ko": "Korean",
                "zh": "Chinese"
            }
    
    def _generate_cache_key(
        self, 
        text: str, 
        language: str, 
        slow: bool, 
        format_type: str
    ) -> str:
        """Generate cache key for audio data"""
        import hashlib
        
        # Create a unique key based on text content and parameters
        key_string = f"{text}_{language}_{slow}_{format_type}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """Get cached audio data if available and not expired"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.{self.audio_format}"
            
            if not cache_file.exists():
                return None
            
            # Check if cache is expired
            if self._is_cache_expired(cache_file):
                cache_file.unlink()  # Remove expired cache
                return None
            
            # Read cached audio
            with open(cache_file, "rb") as f:
                return f.read()
                
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    async def _cache_audio(self, cache_key: str, audio_data: bytes):
        """Cache audio data to file"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.{self.audio_format}"
            
            with open(cache_file, "wb") as f:
                f.write(audio_data)
            
            logger.debug(f"Cached audio: {cache_key}")
            
        except Exception as e:
            logger.warning(f"Error caching audio: {e}")
    
    async def _cleanup_cache(self):
        """Clean up old cache files"""
        try:
            current_time = self.time_utils.get_current_timestamp()
            
            for cache_file in self.cache_dir.glob(f"*.{self.audio_format}"):
                if self._is_cache_expired(cache_file):
                    cache_file.unlink()
                    logger.debug(f"Removed expired cache: {cache_file}")
            
            # Check cache size and remove oldest files if needed
            await self._enforce_cache_size_limit()
            
        except Exception as e:
            logger.warning(f"Error cleaning up cache: {e}")
    
    def _is_cache_expired(self, cache_file: Path) -> bool:
        """Check if cache file is expired"""
        try:
            current_time = datetime.now().timestamp()
            file_age = current_time - cache_file.stat().st_mtime
            return file_age > (self.cache_ttl_hours * 3600)  # Convert hours to seconds
        except Exception:
            return True  # Consider expired if we can't check
    
    async def _enforce_cache_size_limit(self):
        """Enforce cache size limit by removing oldest files"""
        try:
            current_size = self._get_cache_size()
            
            if current_size <= self.max_cache_size:
                return
            
            # Get all cache files sorted by modification time (oldest first)
            cache_files = sorted(
                self.cache_dir.glob(f"*.{self.audio_format}"),
                key=lambda x: x.stat().st_mtime
            )
            
            # Remove oldest files until we're under the limit
            for cache_file in cache_files:
                if current_size <= self.max_cache_size:
                    break
                
                file_size = cache_file.stat().st_size
                cache_file.unlink()
                current_size -= file_size
                logger.debug(f"Removed old cache file: {cache_file}")
                
        except Exception as e:
            logger.warning(f"Error enforcing cache size limit: {e}")
    
    def _get_cache_size(self) -> int:
        """Get total size of cache directory in bytes"""
        try:
            total_size = 0
            for cache_file in self.cache_dir.glob(f"*.{self.audio_format}"):
                total_size += cache_file.stat().st_size
            return total_size
        except Exception:
            return 0
    
    async def _generate_speech(
        self, 
        text: str, 
        language: str, 
        slow: bool, 
        format_type: str
    ) -> Optional[bytes]:
        """Generate speech audio using gTTS"""
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=f".{format_type}", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=slow)
            tts.save(temp_path)
            
            # Read audio data
            with open(temp_path, "rb") as f:
                audio_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
    
    def _estimate_audio_duration(self, audio_size_bytes: int) -> float:
        """Estimate audio duration based on file size"""
        # Rough estimation: 1MB ≈ 1 minute of audio for MP3
        # This is a very rough estimate and may vary significantly
        estimated_mb = audio_size_bytes / (1024 * 1024)
        estimated_minutes = estimated_mb
        return round(estimated_minutes * 60, 1)  # Convert to seconds
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get TTS service usage statistics"""
        return {
            "default_language": self.default_language,
            "supported_languages_count": len(self.supported_languages),
            "cache_directory": str(self.cache_dir),
            "max_cache_size_mb": round(self.max_cache_size / (1024 * 1024), 2),
            "cache_ttl_hours": self.cache_ttl_hours,
            "audio_format": self.audio_format,
            "default_slow": self.default_slow
        }
