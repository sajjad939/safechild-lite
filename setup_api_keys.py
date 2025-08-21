#!/usr/bin/env python3
"""
SafeChild-Lite API Key Setup Utility
Secure methods for configuring API keys
"""

import os
import sys
import getpass
import json
from pathlib import Path
from typing import Dict, Any, Optional

class APIKeyManager:
    """Secure API key management utility"""
    
    def __init__(self):
        self.env_file = Path(".env")
        self.config_file = Path("config/api_keys.json")
        self.required_keys = {
            "OPENAI_API_KEY": {
                "description": "OpenAI API key for AI chatbot functionality",
                "required": True,
                "example": "sk-...",
                "url": "https://platform.openai.com/api-keys"
            },
            "TWILIO_ACCOUNT_SID": {
                "description": "Twilio Account SID for SMS alerts",
                "required": False,
                "example": "AC...",
                "url": "https://console.twilio.com/"
            },
            "TWILIO_AUTH_TOKEN": {
                "description": "Twilio Auth Token for SMS alerts",
                "required": False,
                "example": "...",
                "url": "https://console.twilio.com/"
            },
            "TWILIO_PHONE_NUMBER": {
                "description": "Twilio phone number for sending SMS",
                "required": False,
                "example": "+1234567890",
                "url": "https://console.twilio.com/"
            }
        }
    
    def display_setup_instructions(self):
        """Display comprehensive setup instructions"""
        print("🛡️ SafeChild-Lite API Key Setup")
        print("=" * 50)
        print()
        
        print("📋 Required API Services:")
        for key, info in self.required_keys.items():
            status = "REQUIRED" if info["required"] else "OPTIONAL"
            print(f"  • {key}: {info['description']} ({status})")
            print(f"    Get your key at: {info['url']}")
            print(f"    Example format: {info['example']}")
            print()
        
        print("🔐 Security Notice:")
        print("  • Never share your API keys publicly")
        print("  • Use environment variables in production")
        print("  • Rotate keys regularly for security")
        print("  • Monitor API usage and billing")
        print()
    
    def method_1_environment_variables(self):
        """Method 1: Environment Variables (Recommended)"""
        print("📝 Method 1: Environment Variables (.env file)")
        print("-" * 40)
        
        if not self.env_file.exists():
            print("❌ .env file not found. Creating from template...")
            self._create_env_file()
        
        print("✅ .env file exists")
        print()
        print("🔧 To configure your API keys:")
        print("1. Open the .env file in your text editor")
        print("2. Replace the placeholder values with your actual API keys:")
        print()
        
        for key, info in self.required_keys.items():
            placeholder = f"your_{key.lower()}_here"
            print(f"   {key}={placeholder}")
            print(f"   # Replace with your actual {info['description']}")
            print()
        
        print("3. Save the file")
        print("4. Restart the application")
        print()
        
        return self._check_env_file()
    
    def method_2_interactive_setup(self):
        """Method 2: Interactive Setup"""
        print("🔧 Method 2: Interactive API Key Setup")
        print("-" * 40)
        
        api_keys = {}
        
        for key, info in self.required_keys.items():
            print(f"\n📝 {info['description']}")
            print(f"   Get your key at: {info['url']}")
            print(f"   Example format: {info['example']}")
            
            if info["required"]:
                while True:
                    value = getpass.getpass(f"   Enter {key} (required): ")
                    if value.strip():
                        api_keys[key] = value.strip()
                        break
                    else:
                        print("   ❌ This field is required. Please enter a value.")
            else:
                value = getpass.getpass(f"   Enter {key} (optional, press Enter to skip): ")
                if value.strip():
                    api_keys[key] = value.strip()
                else:
                    api_keys[key] = f"your_{key.lower()}_here"
        
        # Update .env file
        self._update_env_file(api_keys)
        print("\n✅ API keys configured successfully!")
        return True
    
    def method_3_config_file(self):
        """Method 3: Configuration File"""
        print("📄 Method 3: Configuration File")
        print("-" * 40)
        
        # Create config directory
        self.config_file.parent.mkdir(exist_ok=True)
        
        config_data = {
            "api_keys": {
                key: f"your_{key.lower()}_here" 
                for key in self.required_keys.keys()
            },
            "setup_instructions": {
                key: {
                    "description": info["description"],
                    "url": info["url"],
                    "required": info["required"]
                }
                for key, info in self.required_keys.items()
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"✅ Configuration file created: {self.config_file}")
        print()
        print("🔧 To configure your API keys:")
        print(f"1. Open {self.config_file} in your text editor")
        print("2. Replace the placeholder values in the 'api_keys' section")
        print("3. Save the file")
        print("4. Run the application")
        print()
        
        return self.config_file.exists()
    
    def validate_api_keys(self) -> Dict[str, Any]:
        """Validate configured API keys"""
        print("🔍 Validating API Key Configuration...")
        print("-" * 40)
        
        validation_results = {
            "valid": True,
            "missing_required": [],
            "missing_optional": [],
            "configured": []
        }
        
        # Check environment variables
        for key, info in self.required_keys.items():
            value = os.getenv(key)
            
            if not value or value == f"your_{key.lower()}_here":
                if info["required"]:
                    validation_results["missing_required"].append(key)
                    validation_results["valid"] = False
                else:
                    validation_results["missing_optional"].append(key)
            else:
                validation_results["configured"].append(key)
        
        # Display results
        if validation_results["configured"]:
            print("✅ Configured API Keys:")
            for key in validation_results["configured"]:
                print(f"   • {key}")
        
        if validation_results["missing_required"]:
            print("\n❌ Missing Required API Keys:")
            for key in validation_results["missing_required"]:
                info = self.required_keys[key]
                print(f"   • {key}: {info['description']}")
                print(f"     Get it at: {info['url']}")
        
        if validation_results["missing_optional"]:
            print("\n⚠️ Missing Optional API Keys:")
            for key in validation_results["missing_optional"]:
                info = self.required_keys[key]
                print(f"   • {key}: {info['description']}")
                print(f"     Get it at: {info['url']}")
        
        print()
        return validation_results
    
    def _create_env_file(self):
        """Create .env file from template"""
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
        else:
            # Create basic .env file
            with open(".env", "w") as f:
                f.write("# SafeChild-Lite Configuration\n")
                f.write("APP_ENV=development\n")
                f.write("DEBUG=true\n")
                for key in self.required_keys.keys():
                    f.write(f"{key}=your_{key.lower()}_here\n")
    
    def _check_env_file(self) -> bool:
        """Check if .env file has been configured"""
        if not self.env_file.exists():
            return False
        
        with open(self.env_file, 'r') as f:
            content = f.read()
        
        # Check if any placeholder values remain
        for key in self.required_keys.keys():
            placeholder = f"your_{key.lower()}_here"
            if placeholder in content:
                return False
        
        return True
    
    def _update_env_file(self, api_keys: Dict[str, str]):
        """Update .env file with new API keys"""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update existing lines or add new ones
        updated_lines = []
        keys_updated = set()
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in api_keys:
                    updated_lines.append(f"{key}={api_keys[key]}\n")
                    keys_updated.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Add any missing keys
        for key, value in api_keys.items():
            if key not in keys_updated:
                updated_lines.append(f"{key}={value}\n")
        
        # Write back to file
        with open(self.env_file, 'w') as f:
            f.writelines(updated_lines)

def main():
    """Main setup function"""
    manager = APIKeyManager()
    
    # Display instructions
    manager.display_setup_instructions()
    
    print("🚀 Choose your preferred setup method:")
    print("1. Environment Variables (.env file) - Recommended")
    print("2. Interactive Setup - Guided input")
    print("3. Configuration File - JSON-based config")
    print("4. Validate Current Setup")
    print("5. Skip setup and run with placeholders")
    print()
    
    try:
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            manager.method_1_environment_variables()
        elif choice == "2":
            manager.method_2_interactive_setup()
        elif choice == "3":
            manager.method_3_config_file()
        elif choice == "4":
            manager.validate_api_keys()
        elif choice == "5":
            print("⚠️ Running with placeholder API keys. Some features will not work.")
        else:
            print("❌ Invalid choice. Using environment variables method.")
            manager.method_1_environment_variables()
        
        # Final validation
        print("\n" + "="*50)
        validation = manager.validate_api_keys()
        
        if validation["valid"]:
            print("🎉 Setup complete! All required API keys are configured.")
            return True
        else:
            print("⚠️ Setup incomplete. Some required API keys are missing.")
            print("The application will run but some features may not work.")
            return False
            
    except KeyboardInterrupt:
        print("\n\n🛑 Setup cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        return False

if __name__ == "__main__":
    main()