#!/usr/bin/env python3
"""
SafeChild-Lite Backend Runner
Run this script to start the backend server
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the backend server"""
    try:
        # Import after path setup
        from backend.config import settings
        
        logger.info("🚀 Starting SafeChild-Lite Backend Server")
        logger.info(f"Environment: {settings.app_env}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Host: {settings.host}")
        logger.info(f"Port: {settings.port}")
        
        # Check required environment variables
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not getattr(settings, var.lower(), None)]
        
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
            logger.warning("Some features may not work properly")
        
        # Run the server
        uvicorn.run(
            "backend.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()