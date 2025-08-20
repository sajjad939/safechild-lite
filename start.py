#!/usr/bin/env python3
"""
SafeChild-Lite Application Starter
This script starts both backend and frontend services
"""

import os
import sys
import subprocess
import time
import logging
import signal
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafeChildLauncher:
    """Launcher for SafeChild-Lite application"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("🛑 Shutdown signal received")
        self.running = False
        self.stop_services()
        sys.exit(0)
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        logger.info("🔍 Checking dependencies...")
        
        required_packages = [
            "fastapi", "uvicorn", "streamlit", "openai", "requests"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"❌ Missing required packages: {', '.join(missing_packages)}")
            logger.info("Install missing packages with: pip install -r requirements.txt")
            return False
        
        logger.info("✅ All dependencies are installed")
        return True
    
    def check_environment(self):
        """Check environment configuration"""
        logger.info("🔧 Checking environment configuration...")
        
        # Check for .env file
        env_file = Path(".env")
        if not env_file.exists():
            logger.warning("⚠️ .env file not found. Copy .env.example to .env and configure it.")
            
            # Create basic .env file
            with open(".env", "w") as f:
                f.write("# SafeChild-Lite Configuration\n")
                f.write("APP_ENV=development\n")
                f.write("DEBUG=true\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
                f.write("BACKEND_URL=http://localhost:8000\n")
            
            logger.info("📝 Created basic .env file. Please configure it with your API keys.")
        
        # Check critical environment variables
        critical_vars = ["OPENAI_API_KEY"]
        missing_vars = []
        
        for var in critical_vars:
            if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️ Please configure these environment variables: {', '.join(missing_vars)}")
        
        return True
    
    def start_backend(self):
        """Start the backend service"""
        logger.info("🚀 Starting backend service...")
        
        try:
            self.backend_process = subprocess.Popen([
                sys.executable, "run_backend.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for backend to start
            time.sleep(3)
            
            # Check if backend is running
            if self.backend_process.poll() is None:
                logger.info("✅ Backend service started successfully")
                return True
            else:
                logger.error("❌ Backend service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend service"""
        logger.info("🚀 Starting frontend service...")
        
        try:
            self.frontend_process = subprocess.Popen([
                sys.executable, "run_frontend.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for frontend to start
            time.sleep(5)
            
            # Check if frontend is running
            if self.frontend_process.poll() is None:
                logger.info("✅ Frontend service started successfully")
                logger.info("🌐 Frontend available at: http://localhost:8501")
                return True
            else:
                logger.error("❌ Frontend service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start frontend: {e}")
            return False
    
    def monitor_services(self):
        """Monitor running services"""
        logger.info("👀 Monitoring services...")
        
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
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Error monitoring services: {e}")
                break
    
    def stop_services(self):
        """Stop all services"""
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
    
    def run(self):
        """Run the complete SafeChild-Lite application"""
        logger.info("🛡️ SafeChild-Lite Application Launcher")
        logger.info("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Check environment
        if not self.check_environment():
            return False
        
        # Start services
        if not self.start_backend():
            return False
        
        if not self.start_frontend():
            self.stop_services()
            return False
        
        logger.info("🎉 SafeChild-Lite is now running!")
        logger.info("📱 Frontend: http://localhost:8501")
        logger.info("🔧 Backend API: http://localhost:8000")
        logger.info("📚 API Docs: http://localhost:8000/docs")
        logger.info("Press Ctrl+C to stop all services")
        
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
    launcher = SafeChildLauncher()
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()