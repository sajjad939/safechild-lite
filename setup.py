#!/usr/bin/env python3
"""
SafeChild-Lite Setup Script
Automated setup and dependency installation
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a command and handle errors"""
    logger.info(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main setup function"""
    logger.info("🛡️ SafeChild-Lite Setup")
    logger.info("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        logger.error("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create necessary directories
    directories = [
        "temp/audio_cache",
        "temp/documents",
        "templates/documents",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created directory: {directory}")
    
    # Setup environment file
    env_file = Path(".env")
    if not env_file.exists():
        logger.info("📝 Creating .env file from template...")
        
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(".env.example", ".env")
            logger.info("✅ .env file created from .env.example")
        else:
            # Create basic .env file
            with open(".env", "w") as f:
                f.write("# SafeChild-Lite Configuration\n")
                f.write("APP_ENV=development\n")
                f.write("DEBUG=true\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
                f.write("BACKEND_URL=http://localhost:8000\n")
            logger.info("✅ Basic .env file created")
    
    # Setup complete
    logger.info("🎉 Setup completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Edit .env file with your API keys")
    logger.info("2. Run: python start.py")
    logger.info("3. Open http://localhost:8501 in your browser")
    logger.info("")
    logger.info("For more information, see README.md")

if __name__ == "__main__":
    main()