#!/usr/bin/env python3
"""
Secure Configuration Management for SafeChild-Lite
Handles API keys and sensitive configuration securely
"""

import os
import json
import logging
import getpass
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class SecureConfig:
    """Secure configuration management with encryption support"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.env_file = Path(".env")
        self.encrypted_config = self.config_dir / "encrypted_config.json"
        self.key_file = self.config_dir / ".key"
        
        # Initialize encryption key
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Make key file read-only
            os.chmod(self.key_file, 0o600)
            return key
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a configuration value"""
        if not value:
            return ""
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a configuration value"""
        if not encrypted_value:
            return ""
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    def interactive_setup(self) -> bool:
        """Interactive API key setup with secure input"""
        print("🔐 Secure Interactive API Key Setup")
        print("=" * 40)
        
        api_keys = {}
        
        # OpenAI API Key (Required)
        print("\n🤖 OpenAI Configuration (Required for AI features)")
        print("   Get your API key at: https://platform.openai.com/api-keys")
        
        while True:
            openai_key = getpass.getpass("   Enter OpenAI API Key: ")
            if openai_key.strip():
                if self._validate_openai_key(openai_key):
                    api_keys["OPENAI_API_KEY"] = openai_key.strip()
                    print("   ✅ OpenAI API key validated")
                    break
                else:
                    print("   ❌ Invalid OpenAI API key format. Please try again.")
            else:
                print("   ❌ OpenAI API key is required. Please enter a valid key.")
        
        # Twilio Configuration (Optional)
        print("\n📱 Twilio Configuration (Optional for SMS alerts)")
        print("   Get your credentials at: https://console.twilio.com/")
        
        setup_twilio = input("   Setup Twilio for SMS alerts? (y/N): ").lower().startswith('y')
        
        if setup_twilio:
            twilio_sid = getpass.getpass("   Enter Twilio Account SID: ")
            if twilio_sid.strip():
                api_keys["TWILIO_ACCOUNT_SID"] = twilio_sid.strip()
            
            twilio_token = getpass.getpass("   Enter Twilio Auth Token: ")
            if twilio_token.strip():
                api_keys["TWILIO_AUTH_TOKEN"] = twilio_token.strip()
            
            twilio_phone = input("   Enter Twilio Phone Number (e.g., +1234567890): ")
            if twilio_phone.strip():
                api_keys["TWILIO_PHONE_NUMBER"] = twilio_phone.strip()
        
        # Save configuration
        self._save_to_env_file(api_keys)
        self._save_encrypted_config(api_keys)
        
        print("\n✅ API keys configured successfully!")
        return True
    
    def _validate_openai_key(self, key: str) -> bool:
        """Basic validation of OpenAI API key format"""
        return key.startswith("sk-") and len(key) > 20
    
    def _save_to_env_file(self, api_keys: Dict[str, str]):
        """Save API keys to .env file"""
        # Read existing .env file
        env_content = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_content[key] = value
        
        # Update with new API keys
        env_content.update(api_keys)
        
        # Write back to .env file
        with open(self.env_file, 'w') as f:
            f.write("# SafeChild-Lite Configuration\n")
            f.write("# Generated by secure setup utility\n\n")
            
            # Application settings
            f.write("# Application Settings\n")
            f.write("APP_ENV=development\n")
            f.write("DEBUG=true\n")
            f.write("LOG_LEVEL=INFO\n")
            f.write("HOST=0.0.0.0\n")
            f.write("PORT=8000\n\n")
            
            # API keys
            f.write("# API Keys\n")
            for key, value in api_keys.items():
                f.write(f"{key}={value}\n")
            
            f.write("\n# Other Configuration\n")
            other_config = {
                "OPENAI_MODEL": "gpt-4",
                "OPENAI_MAX_TOKENS": "1000",
                "OPENAI_TEMPERATURE": "0.7",
                "AI_PROVIDER": "openai",
                "TTS_DEFAULT_LANGUAGE": "en",
                "SMS_MAX_LENGTH": "160",
                "SECRET_KEY": "your_secret_key_here",
                "ALLOWED_ORIGINS": "http://localhost:8501,http://localhost:3000"
            }
            
            for key, value in other_config.items():
                if key not in env_content:
                    f.write(f"{key}={value}\n")
    
    def _save_encrypted_config(self, api_keys: Dict[str, str]):
        """Save encrypted configuration file"""
        encrypted_keys = {}
        for key, value in api_keys.items():
            encrypted_keys[key] = self.encrypt_value(value)
        
        config_data = {
            "encrypted": True,
            "api_keys": encrypted_keys,
            "created_at": self._get_timestamp()
        }
        
        with open(self.encrypted_config, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Make config file read-only
        os.chmod(self.encrypted_config, 0o600)
    
    def load_encrypted_config(self) -> Dict[str, str]:
        """Load and decrypt configuration"""
        if not self.encrypted_config.exists():
            return {}
        
        try:
            with open(self.encrypted_config, 'r') as f:
                config_data = json.load(f)
            
            if not config_data.get("encrypted"):
                return config_data.get("api_keys", {})
            
            decrypted_keys = {}
            for key, encrypted_value in config_data.get("api_keys", {}).items():
                decrypted_keys[key] = self.decrypt_value(encrypted_value)
            
            return decrypted_keys
            
        except Exception as e:
            logger.error(f"Failed to load encrypted config: {e}")
            return {}
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def test_api_connections(self) -> Dict[str, Any]:
        """Test API connections with configured keys"""
        print("🧪 Testing API Connections...")
        print("-" * 30)
        
        results = {}
        
        # Test OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your_openai_api_key_here":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                # Test with a simple request
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                results["openai"] = {"status": "✅ Connected", "model": "gpt-3.5-turbo"}
                print("   ✅ OpenAI API: Connected")
            except Exception as e:
                results["openai"] = {"status": "❌ Failed", "error": str(e)}
                print(f"   ❌ OpenAI API: Failed - {e}")
        else:
            results["openai"] = {"status": "⚠️ Not configured"}
            print("   ⚠️ OpenAI API: Not configured")
        
        # Test Twilio
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if twilio_sid and twilio_token and \
           twilio_sid != "your_twilio_account_sid_here" and \
           twilio_token != "your_twilio_auth_token_here":
            try:
                from twilio.rest import Client
                client = Client(twilio_sid, twilio_token)
                # Test connection by fetching account info
                account = client.api.accounts(twilio_sid).fetch()
                results["twilio"] = {"status": "✅ Connected", "account": account.friendly_name}
                print("   ✅ Twilio API: Connected")
            except Exception as e:
                results["twilio"] = {"status": "❌ Failed", "error": str(e)}
                print(f"   ❌ Twilio API: Failed - {e}")
        else:
            results["twilio"] = {"status": "⚠️ Not configured"}
            print("   ⚠️ Twilio API: Not configured")
        
        print()
        return results

def main():
    """Main function for secure configuration setup"""
    config_manager = SecureConfig()
    
    print("🛡️ SafeChild-Lite Secure Configuration Setup")
    print("=" * 50)
    print()
    
    print("Choose your setup method:")
    print("1. 🔧 Interactive Setup (Recommended)")
    print("2. 📝 Manual .env file editing")
    print("3. 🧪 Test current configuration")
    print("4. 📄 View setup instructions")
    print()
    
    try:
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            success = config_manager.interactive_setup()
            if success:
                config_manager.test_api_connections()
        elif choice == "2":
            print("\n📝 Manual Setup Instructions:")
            print("1. Edit the .env file in your text editor")
            print("2. Replace placeholder values with your actual API keys")
            print("3. Save the file and restart the application")
        elif choice == "3":
            config_manager.test_api_connections()
        elif choice == "4":
            # Instructions already displayed
            pass
        else:
            print("❌ Invalid choice")
            return False
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n🛑 Setup cancelled")
        return False
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        return False

if __name__ == "__main__":
    main()