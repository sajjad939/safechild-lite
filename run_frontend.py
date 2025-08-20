#!/usr/bin/env python3
"""
SafeChild-Lite Frontend Runner
Run this script to start the Streamlit frontend
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the frontend server"""
    try:
        logger.info("🚀 Starting SafeChild-Lite Frontend (Streamlit)")
        
        # Set environment variables for Streamlit
        env = os.environ.copy()
        env.update({
            "STREAMLIT_SERVER_PORT": "8501",
            "STREAMLIT_SERVER_ADDRESS": "0.0.0.0",
            "STREAMLIT_SERVER_HEADLESS": "true",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false"
        })
        
        # Run Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            "frontend/app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        logger.info("Starting Streamlit server...")
        subprocess.run(cmd, env=env)
        
    except KeyboardInterrupt:
        logger.info("🛑 Frontend stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()