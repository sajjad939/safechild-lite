#!/usr/bin/env python3
"""
SafeChild-Lite Application Runner with API Key Validation
Comprehensive startup script with API key checking and fallback handling
"""

import os
import sys
import subprocess
import logging
import time
import signal
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafeChildRunner:
    """Application runner with comprehensive API key management"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
        # API key validation results
        self.api_validation = {}
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("🛑 Shutdown signal received")
        self.running = False
        self.stop_services()
        sys.exit(0)
    
    def validate_api_keys(self) -> Dict[str, Any]:
        """Comprehensive API key validation"""
        logger.info("🔍 Validating API configuration...")
        
        validation_results = {
            "openai": {"configured": False, "valid": False, "error": None},
            "twilio": {"configured": False, "valid": False, "error": None},
            "overall_status": "unknown"
        }
        
        # Check OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your_openai_api_key_here":
            validation_results["openai"]["configured"] = True
            try:
                # Test OpenAI connection
                import openai
                client = openai.OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                validation_results["openai"]["valid"] = True
                logger.info("✅ OpenAI API: Valid and working")
            except Exception as e:
                validation_results["openai"]["error"] = str(e)
                logger.warning(f"⚠️ OpenAI API: Configured but not working - {e}")
        else:
            logger.warning("⚠️ OpenAI API: Not configured")
        
        # Check Twilio
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
        
        if all([twilio_sid, twilio_token, twilio_phone]) and \
           not any(val.startswith("your_") for val in [twilio_sid, twilio_token, twilio_phone]):
            validation_results["twilio"]["configured"] = True
            try:
                # Test Twilio connection
                from twilio.rest import Client
                client = Client(twilio_sid, twilio_token)
                account = client.api.accounts(twilio_sid).fetch()
                validation_results["twilio"]["valid"] = True
                logger.info("✅ Twilio API: Valid and working")
            except Exception as e:
                validation_results["twilio"]["error"] = str(e)
                logger.warning(f"⚠️ Twilio API: Configured but not working - {e}")
        else:
            logger.warning("⚠️ Twilio API: Not configured (SMS features disabled)")
        
        # Determine overall status
        if validation_results["openai"]["valid"]:
            if validation_results["twilio"]["valid"]:
                validation_results["overall_status"] = "fully_configured"
            else:
                validation_results["overall_status"] = "partially_configured"
        else:
            validation_results["overall_status"] = "minimal_configuration"
        
        self.api_validation = validation_results
        return validation_results
    
    def display_api_status(self):
        """Display API configuration status"""
        print("\n📊 API Configuration Status")
        print("=" * 30)
        
        # OpenAI Status
        openai_status = self.api_validation.get("openai", {})
        if openai_status.get("valid"):
            print("🤖 OpenAI API: ✅ Connected and working")
        elif openai_status.get("configured"):
            print(f"🤖 OpenAI API: ⚠️ Configured but not working - {openai_status.get('error', 'Unknown error')}")
        else:
            print("🤖 OpenAI API: ❌ Not configured")
        
        # Twilio Status
        twilio_status = self.api_validation.get("twilio", {})
        if twilio_status.get("valid"):
            print("📱 Twilio API: ✅ Connected and working")
        elif twilio_status.get("configured"):
            print(f"📱 Twilio API: ⚠️ Configured but not working - {twilio_status.get('error', 'Unknown error')}")
        else:
            print("📱 Twilio API: ❌ Not configured (SMS features disabled)")
        
        # Overall Status
        overall = self.api_validation.get("overall_status", "unknown")
        if overall == "fully_configured":
            print("\n🎉 Status: Fully configured - All features available")
        elif overall == "partially_configured":
            print("\n⚠️ Status: Partially configured - Some features may be limited")
        else:
            print("\n❌ Status: Minimal configuration - Limited functionality")
        
        print()
    
    def offer_setup_options(self) -> bool:
        """Offer setup options if API keys are missing"""
        if self.api_validation.get("overall_status") == "fully_configured":
            return True
        
        print("🔧 API Key Setup Options:")
        print("1. 🔐 Interactive secure setup")
        print("2. 📝 Manual .env file editing")
        print("3. 🚀 Continue with current configuration")
        print("4. ❌ Exit and configure manually")
        print()
        
        try:
            choice = input("Choose an option (1-4): ").strip()
            
            if choice == "1":
                from config.secure_config import SecureConfig
                config_manager = SecureConfig()
                return config_manager.interactive_setup()
            elif choice == "2":
                print("\n📝 Manual Setup Instructions:")
                print("1. Open the .env file in your text editor")
                print("2. Replace these placeholder values:")
                print("   - OPENAI_API_KEY=your_openai_api_key_here")
                print("   - TWILIO_ACCOUNT_SID=your_twilio_account_sid_here")
                print("   - TWILIO_AUTH_TOKEN=your_twilio_auth_token_here")
                print("   - TWILIO_PHONE_NUMBER=your_twilio_phone_number_here")
                print("3. Save the file and restart the application")
                print("\nPress Enter when ready to continue...")
                input()
                return True
            elif choice == "3":
                print("⚠️ Continuing with current configuration...")
                return True
            elif choice == "4":
                print("❌ Exiting for manual configuration")
                return False
            else:
                print("❌ Invalid choice, continuing with current configuration")
                return True
                
        except KeyboardInterrupt:
            print("\n🛑 Setup cancelled")
            return False
    
    def start_backend(self) -> bool:
        """Start backend service with error handling"""
        logger.info("🚀 Starting backend service...")
        
        try:
            # Set environment variables for the backend process
            env = os.environ.copy()
            
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "backend.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for backend to start
            time.sleep(5)
            
            # Check if backend is running
            if self.backend_process.poll() is None:
                # Test backend health
                try:
                    import requests
                    response = requests.get("http://localhost:8000/health", timeout=10)
                    if response.status_code == 200:
                        logger.info("✅ Backend service: Healthy and responding")
                        logger.info("🔧 Backend API: http://localhost:8000")
                        logger.info("📚 API Docs: http://localhost:8000/docs")
                        return True
                    else:
                        logger.warning("⚠️ Backend service: Started but not healthy")
                        return True
                except Exception as e:
                    logger.warning(f"⚠️ Backend service: Started but health check failed - {e}")
                    return True
            else:
                logger.error("❌ Backend service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self) -> bool:
        """Start frontend service"""
        logger.info("🚀 Starting frontend service...")
        
        try:
            # Set environment variables for the frontend process
            env = os.environ.copy()
            env.update({
                "STREAMLIT_SERVER_PORT": "8501",
                "STREAMLIT_SERVER_ADDRESS": "0.0.0.0",
                "STREAMLIT_SERVER_HEADLESS": "true",
                "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false"
            })
            
            self.frontend_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", "frontend/app.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for frontend to start
            time.sleep(8)
            
            # Check if frontend is running
            if self.frontend_process.poll() is None:
                # Test frontend health
                try:
                    import requests
                    response = requests.get("http://localhost:8501", timeout=15)
                    if response.status_code == 200:
                        logger.info("✅ Frontend service: Healthy and responding")
                        logger.info("🌐 Frontend URL: http://localhost:8501")
                        return True
                    else:
                        logger.warning("⚠️ Frontend service: Started but not responding")
                        return True
                except Exception as e:
                    logger.warning(f"⚠️ Frontend service: Started but health check failed - {e}")
                    return True
            else:
                logger.error("❌ Frontend service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start frontend: {e}")
            return False
    
    def monitor_services(self):
        """Monitor running services"""
        logger.info("👀 Monitoring services (Press Ctrl+C to stop)...")
        
        while self.running:
            try:
                # Check backend
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("❌ Backend service stopped unexpectedly")
                    break
                
                # Check frontend
                if self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("❌ Frontend service stopped unexpectedly")
                    break
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Error monitoring services: {e}")
                break
    
    def stop_services(self):
        """Stop all services gracefully"""
        logger.info("🛑 Stopping services...")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=10)
                logger.info("✅ Backend service stopped")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                logger.warning("⚠️ Backend service force killed")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=10)
                logger.info("✅ Frontend service stopped")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                logger.warning("⚠️ Frontend service force killed")
    
    def run(self) -> bool:
        """Run the complete application with API key validation"""
        print("🛡️ SafeChild-Lite Application Runner")
        print("=" * 50)
        
        # Validate API keys
        self.validate_api_keys()
        self.display_api_status()
        
        # Offer setup if needed
        if not self.offer_setup_options():
            return False
        
        # Re-validate after potential setup
        self.validate_api_keys()
        
        # Start services
        if not self.start_backend():
            logger.error("❌ Failed to start backend service")
            return False
        
        if not self.start_frontend():
            logger.error("❌ Failed to start frontend service")
            self.stop_services()
            return False
        
        # Display success message
        print("\n🎉 SafeChild-Lite is now running!")
        print("=" * 40)
        print("📱 Frontend: http://localhost:8501")
        print("🔧 Backend API: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print()
        print("🔧 Available Features:")
        
        if self.api_validation.get("openai", {}).get("valid"):
            print("   ✅ AI Chatbot (OpenAI)")
            print("   ✅ Complaint Generation (AI-powered)")
        else:
            print("   ⚠️ AI Chatbot (Limited - using fallbacks)")
            print("   ⚠️ Complaint Generation (Template-based)")
        
        if self.api_validation.get("twilio", {}).get("valid"):
            print("   ✅ SMS Emergency Alerts (Twilio)")
        else:
            print("   ⚠️ SMS Emergency Alerts (Disabled)")
        
        print("   ✅ Text-to-Speech (Local)")
        print("   ✅ PDF Generation (Local)")
        print("   ✅ Safety Education Content")
        print()
        print("Press Ctrl+C to stop all services")
        
        # Monitor services
        try:
            self.monitor_services()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_services()
        
        logger.info("👋 SafeChild-Lite stopped")
        return True

def main():
    """Main entry point"""
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check if dependencies are installed
    try:
        import fastapi
        import streamlit
        import openai
        import requests
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Install dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Create and run the application
    runner = SafeChildRunner()
    success = runner.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()