#!/usr/bin/env python3
"""
SafeChild-Lite API Key Integration Examples
Demonstrates different methods for securely handling API keys
"""

import os
import json
import getpass
from pathlib import Path
from typing import Dict, Any, Optional

def example_1_environment_variables():
    """Example 1: Using Environment Variables (Recommended)"""
    print("🔐 Example 1: Environment Variables")
    print("=" * 40)
    
    # Method A: Load from .env file
    print("Method A: .env file (Recommended for development)")
    print("""
# In your .env file:
OPENAI_API_KEY=sk-your-actual-openai-key-here
TWILIO_ACCOUNT_SID=ACyour-actual-twilio-sid-here
TWILIO_AUTH_TOKEN=your-actual-twilio-token-here
TWILIO_PHONE_NUMBER=+1234567890

# In your Python code:
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

openai_key = os.getenv('OPENAI_API_KEY')
twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

# Validate keys
if not openai_key or openai_key.startswith('your_'):
    raise ValueError("OpenAI API key not configured")

if not all([twilio_sid, twilio_token, twilio_phone]):
    print("Warning: Twilio not configured - SMS features disabled")
""")
    
    # Method B: System environment variables
    print("\nMethod B: System Environment Variables (Production)")
    print("""
# Set in your system/container:
export OPENAI_API_KEY="sk-your-actual-openai-key-here"
export TWILIO_ACCOUNT_SID="ACyour-actual-twilio-sid-here"
export TWILIO_AUTH_TOKEN="your-actual-twilio-token-here"
export TWILIO_PHONE_NUMBER="+1234567890"

# Or in Docker:
docker run -e OPENAI_API_KEY="sk-..." -e TWILIO_ACCOUNT_SID="AC..." safechild-lite

# Or in Railway/Vercel/Heroku:
# Set environment variables in your deployment platform's dashboard
""")

def example_2_secure_input():
    """Example 2: Secure Interactive Input"""
    print("\n🔧 Example 2: Secure Interactive Input")
    print("=" * 40)
    
    print("""
import getpass
import os

def secure_api_setup():
    print("🔐 Secure API Key Setup")
    
    # OpenAI API Key
    while True:
        openai_key = getpass.getpass("Enter OpenAI API Key: ")
        if openai_key.startswith("sk-") and len(openai_key) > 20:
            os.environ['OPENAI_API_KEY'] = openai_key
            print("✅ OpenAI API key configured")
            break
        else:
            print("❌ Invalid OpenAI API key format")
    
    # Twilio Configuration (Optional)
    setup_twilio = input("Setup Twilio for SMS? (y/N): ").lower().startswith('y')
    if setup_twilio:
        twilio_sid = getpass.getpass("Enter Twilio Account SID: ")
        twilio_token = getpass.getpass("Enter Twilio Auth Token: ")
        twilio_phone = input("Enter Twilio Phone Number: ")
        
        os.environ['TWILIO_ACCOUNT_SID'] = twilio_sid
        os.environ['TWILIO_AUTH_TOKEN'] = twilio_token
        os.environ['TWILIO_PHONE_NUMBER'] = twilio_phone
        print("✅ Twilio configured")
    
    return True

# Usage:
if __name__ == "__main__":
    secure_api_setup()
    # Now start your application
""")

def example_3_config_file():
    """Example 3: Configuration File with Encryption"""
    print("\n📄 Example 3: Encrypted Configuration File")
    print("=" * 40)
    
    print("""
import json
import base64
from cryptography.fernet import Fernet

class EncryptedConfig:
    def __init__(self, config_file="config/api_keys.json"):
        self.config_file = config_file
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        key_file = "config/.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs("config", exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Read-only for owner
            return key
    
    def save_api_keys(self, api_keys):
        encrypted_keys = {}
        for key, value in api_keys.items():
            encrypted_value = self.cipher.encrypt(value.encode())
            encrypted_keys[key] = base64.b64encode(encrypted_value).decode()
        
        with open(self.config_file, 'w') as f:
            json.dump({"encrypted_keys": encrypted_keys}, f)
        os.chmod(self.config_file, 0o600)
    
    def load_api_keys(self):
        if not os.path.exists(self.config_file):
            return {}
        
        with open(self.config_file, 'r') as f:
            data = json.load(f)
        
        decrypted_keys = {}
        for key, encrypted_value in data.get("encrypted_keys", {}).items():
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted_value = self.cipher.decrypt(encrypted_bytes).decode()
            decrypted_keys[key] = decrypted_value
        
        return decrypted_keys

# Usage:
config = EncryptedConfig()
api_keys = config.load_api_keys()

# Set environment variables from encrypted config
for key, value in api_keys.items():
    os.environ[key] = value
""")

def example_4_validation_and_fallbacks():
    """Example 4: API Key Validation and Fallbacks"""
    print("\n🧪 Example 4: Validation and Fallback Handling")
    print("=" * 40)
    
    print("""
import os
import logging
from typing import Dict, Any

class APIKeyValidator:
    def __init__(self):
        self.validation_results = {}
    
    def validate_openai_key(self, api_key: str) -> Dict[str, Any]:
        if not api_key or api_key.startswith("your_"):
            return {"valid": False, "error": "API key not configured"}
        
        if not api_key.startswith("sk-"):
            return {"valid": False, "error": "Invalid OpenAI API key format"}
        
        try:
            # Test the API key
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return {"valid": True, "model": "gpt-3.5-turbo"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def validate_twilio_credentials(self, sid: str, token: str) -> Dict[str, Any]:
        if not all([sid, token]) or any(val.startswith("your_") for val in [sid, token]):
            return {"valid": False, "error": "Twilio credentials not configured"}
        
        try:
            from twilio.rest import Client
            client = Client(sid, token)
            account = client.api.accounts(sid).fetch()
            return {"valid": True, "account_name": account.friendly_name}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def setup_fallbacks(self):
        # Setup fallback responses for when APIs are unavailable
        fallback_responses = {
            "chatbot": [
                "I'm here to help with safety questions.",
                "Please tell a trusted adult if you need immediate help.",
                "Your safety is important. What would you like to know?"
            ],
            "emergency": "Emergency alert logged. Please contact authorities directly.",
            "complaint": "Complaint template generated. Please review and customize."
        }
        return fallback_responses

# Usage in your application:
validator = APIKeyValidator()

# Validate OpenAI
openai_result = validator.validate_openai_key(os.getenv('OPENAI_API_KEY'))
if openai_result['valid']:
    print("✅ OpenAI API: Ready")
else:
    print(f"⚠️ OpenAI API: {openai_result['error']}")

# Validate Twilio
twilio_result = validator.validate_twilio_credentials(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
if twilio_result['valid']:
    print("✅ Twilio API: Ready")
else:
    print(f"⚠️ Twilio API: {twilio_result['error']}")
""")

def main():
    """Display all API key integration examples"""
    print("🛡️ SafeChild-Lite API Key Integration Guide")
    print("=" * 60)
    
    example_1_environment_variables()
    example_2_secure_input()
    example_3_config_file()
    example_4_validation_and_fallbacks()
    
    print("\n🎯 Recommended Setup Process:")
    print("1. Choose Method 1 (Environment Variables) for development")
    print("2. Use Method 2 (Secure Input) for initial setup")
    print("3. Implement Method 4 (Validation) for production")
    print("4. Use Method 3 (Encrypted Config) for advanced security")
    print()
    print("🚀 Ready to start? Run: python run_with_api_check.py")

if __name__ == "__main__":
    main()