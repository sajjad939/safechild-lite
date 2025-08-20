import re
import html
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class TextCleaner:
    """Utility class for cleaning and sanitizing text input"""
    
    def __init__(self):
        # Sensitive patterns to redact
        self.sensitive_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
            r'\b\d{5}(?:-\d{4})?\b',  # ZIP codes
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
        ]
        
        # HTML/script patterns
        self.html_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'<[^>]+>',  # Any HTML tags
            r'javascript:',  # JavaScript protocol
            r'data:',  # Data URLs
        ]
        
        # Special characters replacement
        self.special_chars = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-',
            '…': '...',
        }
    
    def clean_text(self, text: str, remove_sensitive: bool = False, 
                   remove_html: bool = True, normalize_whitespace: bool = True) -> str:
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
            
            # Normalize whitespace
            if normalize_whitespace:
                cleaned_text = self.normalize_whitespace(cleaned_text)
            
            # Decode HTML entities
            cleaned_text = html.unescape(cleaned_text)
            
            # Replace special characters
            cleaned_text = self.replace_special_chars(cleaned_text)
            
            # Final trim
            cleaned_text = cleaned_text.strip()
            
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
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters"""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Replace multiple newlines with single newline
        text = re.sub(r'\n+', '\n', text)
        return text
    
    def replace_special_chars(self, text: str) -> str:
        """Replace special Unicode characters with ASCII equivalents"""
        for special_char, replacement in self.special_chars.items():
            text = text.replace(special_char, replacement)
        return text