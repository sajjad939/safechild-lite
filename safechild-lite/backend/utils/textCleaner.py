import re
import logging
import html
from typing import Optional, List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextCleaner:
    """Utility class for cleaning and sanitizing text input"""
    
    def __init__(self):
        # Common patterns to clean
        self.sensitive_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
            r'\b\d{5}(?:-\d{4})?\b',  # ZIP codes
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
        ]
        
        # Inappropriate content patterns
        self.inappropriate_patterns = [
            r'\b(?:fuck|shit|bitch|ass|damn|hell)\b',  # Profanity
            r'\b(?:kill|murder|suicide|death|die)\b',  # Harmful content
            r'\b(?:hate|racist|sexist|discriminatory)\b',  # Hate speech
        ]
        
        # HTML/script patterns
        self.html_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'<[^>]+>',  # Any HTML tags
            r'javascript:',  # JavaScript protocol
            r'data:',  # Data URLs
        ]
        
        # Special characters that might cause issues
        self.special_chars = {
            '"': '"',
            '"': '"',
            ''': ''',
            ''': ''',
            '–': '-',
            '—': '-',
            '…': '...',
            '®': '(R)',
            '©': '(C)',
            '™': '(TM)',
        }
    
    def clean_text(self, text: str, remove_sensitive: bool = True, 
                   remove_inappropriate: bool = True, remove_html: bool = True,
                   normalize_whitespace: bool = True) -> str:
        """Clean text based on specified options"""
        if not text or not isinstance(text, str):
            return ""
        
        cleaned_text = text
        
        try:
            # Remove HTML and scripts
            if remove_html:
                cleaned_text = self.remove_html_content(cleaned_text)
            
            # Remove sensitive information
            if remove_sensitive:
                cleaned_text = self.remove_sensitive_info(cleaned_text)
            
            # Remove inappropriate content
            if remove_inappropriate:
                cleaned_text = self.remove_inappropriate_content(cleaned_text)
            
            # Normalize whitespace
            if normalize_whitespace:
                cleaned_text = self.normalize_whitespace(cleaned_text)
            
            # Decode HTML entities
            cleaned_text = html.unescape(cleaned_text)
            
            # Replace special characters
            cleaned_text = self.replace_special_chars(cleaned_text)
            
            # Final trim
            cleaned_text = cleaned_text.strip()
            
            logger.info(f"Text cleaned successfully. Original length: {len(text)}, Cleaned length: {len(cleaned_text)}")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text.strip() if text else ""
    
    def remove_html_content(self, text: str) -> str:
        """Remove HTML tags and scripts from text"""
        for pattern in self.html_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        return text
    
    def remove_sensitive_info(self, text: str) -> str:
        """Remove sensitive information like phone numbers, emails, etc."""
        for pattern in self.sensitive_patterns:
            text = re.sub(pattern, '[REDACTED]', text)
        return text
    
    def remove_inappropriate_content(self, text: str) -> str:
        """Remove or replace inappropriate content"""
        for pattern in self.inappropriate_patterns:
            text = re.sub(pattern, '[INAPPROPRIATE]', text, flags=re.IGNORECASE)
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters"""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Replace multiple newlines with single newline
        text = re.sub(r'\n+', '\n', text)
        # Replace multiple tabs with single space
        text = re.sub(r'\t+', ' ', text)
        return text
    
    def replace_special_chars(self, text: str) -> str:
        """Replace special Unicode characters with ASCII equivalents"""
        for special_char, replacement in self.special_chars.items():
            text = text.replace(special_char, replacement)
        return text
    
    def sanitize_for_database(self, text: str) -> str:
        """Sanitize text for database storage"""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remove excessive whitespace
        text = self.normalize_whitespace(text)
        
        # Truncate if too long (prevent potential issues)
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length] + "..."
            logger.warning(f"Text truncated to {max_length} characters")
        
        return text.strip()
    
    def sanitize_for_display(self, text: str) -> str:
        """Sanitize text for safe display"""
        if not text:
            return ""
        
        # Remove HTML and scripts
        text = self.remove_html_content(text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize whitespace
        text = self.normalize_whitespace(text)
        
        return text.strip()
    
    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        try:
            # Clean the text first
            cleaned_text = self.clean_text(text, remove_sensitive=False, remove_inappropriate=False)
            
            # Split into words and filter
            words = re.findall(r'\b[a-zA-Z]+\b', cleaned_text.lower())
            
            # Filter by length and common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
            }
            
            keywords = [
                word for word in words
                if len(word) >= min_length and word not in stop_words
            ]
            
            # Count frequency and return unique keywords
            keyword_count = {}
            for keyword in keywords:
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
            
            # Sort by frequency and return top keywords
            sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
            return [keyword for keyword, count in sorted_keywords[:20]]  # Top 20 keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def detect_language(self, text: str) -> str:
        """Simple language detection based on common words"""
        if not text:
            return "unknown"
        
        try:
            # Common words in different languages
            language_patterns = {
                'english': [r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b'],
                'spanish': [r'\b(el|la|los|las|y|o|pero|en|a|de|con|por)\b'],
                'french': [r'\b(le|la|les|et|ou|mais|dans|à|de|avec|par)\b'],
                'german': [r'\b(der|die|das|und|oder|aber|in|an|zu|für|von|mit)\b'],
            }
            
            text_lower = text.lower()
            scores = {}
            
            for language, patterns in language_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, text_lower))
                    score += matches
                scores[language] = score
            
            # Return language with highest score
            if scores:
                detected_language = max(scores, key=scores.get)
                if scores[detected_language] > 0:
                    return detected_language
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return "unknown"
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """Get comprehensive text statistics"""
        if not text:
            return {
                "length": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "average_word_length": 0,
                "reading_time_minutes": 0,
                "language": "unknown"
            }
        
        try:
            # Basic statistics
            length = len(text)
            word_count = len(text.split())
            sentence_count = len(re.findall(r'[.!?]+', text))
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            # Calculate average word length
            words = text.split()
            if words:
                total_word_length = sum(len(word) for word in words)
                average_word_length = total_word_length / len(words)
            else:
                average_word_length = 0
            
            # Estimate reading time (average 200 words per minute)
            reading_time_minutes = word_count / 200 if word_count > 0 else 0
            
            # Detect language
            language = self.detect_language(text)
            
            return {
                "length": length,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "average_word_length": round(average_word_length, 2),
                "reading_time_minutes": round(reading_time_minutes, 2),
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error getting text statistics: {str(e)}")
            return {
                "length": len(text) if text else 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "average_word_length": 0,
                "reading_time_minutes": 0,
                "language": "unknown"
            }
    
    def validate_text_input(self, text: str, max_length: int = 10000, 
                           min_length: int = 1, allow_html: bool = False) -> Dict[str, Any]:
        """Validate text input based on specified criteria"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        try:
            if not text:
                validation_result["valid"] = False
                validation_result["errors"].append("Text cannot be empty")
                return validation_result
            
            # Check length
            if len(text) > max_length:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Text too long (max {max_length} characters)")
            
            if len(text) < min_length:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Text too short (min {min_length} characters)")
            
            # Check for HTML if not allowed
            if not allow_html and re.search(r'<[^>]+>', text):
                validation_result["valid"] = False
                validation_result["errors"].append("HTML tags not allowed")
            
            # Check for potentially harmful content
            if re.search(r'javascript:|data:|vbscript:', text, re.IGNORECASE):
                validation_result["valid"] = False
                validation_result["errors"].append("Potentially harmful content detected")
            
            # Get statistics
            validation_result["statistics"] = self.get_text_statistics(text)
            
            # Add warnings for long text
            if len(text) > 5000:
                validation_result["warnings"].append("Text is very long, consider breaking it into smaller sections")
            
            # Add warnings for mixed case
            if text.isupper() and len(text) > 10:
                validation_result["warnings"].append("Text is in all caps, consider using normal case")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating text input: {str(e)}")
            validation_result["valid"] = False
            validation_result["errors"].append("Validation error occurred")
            return validation_result
