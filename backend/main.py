from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import os
import time
from typing import Dict, Any

# Import API routers
from backend.api.chatbot import router as chatbot_router
from backend.api.complaint import router as complaint_router
from backend.api.emergency import router as emergency_router
from backend.api.awareness import router as awareness_router
from backend.api.tts import router as tts_router
from backend.api.config import router as config_router

# Import utilities
from utils.timeUtils import TimeUtils
from utils.textCleaner import TextCleaner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
startup_time = None
request_count = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global startup_time
    
    # Startup
    startup_time = time.time()
    logger.info("🚀 SafeChild-Lite Backend starting up...")
    
    # Initialize utilities
    try:
        time_utils = TimeUtils()
        text_cleaner = TextCleaner()
        logger.info("✅ Utilities initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing utilities: {str(e)}")
    
    # Check environment variables
    required_env_vars = [
        "OPENAI_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly")
    else:
        logger.info("✅ All required environment variables are set")
    
    logger.info("🎯 SafeChild-Lite Backend is ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 SafeChild-Lite Backend shutting down...")
    if startup_time:
        uptime = time.time() - startup_time
        logger.info(f"⏱️ Total uptime: {uptime:.2f} seconds")

# Create FastAPI app
app = FastAPI(
    title="SafeChild-Lite Backend API",
    description="Backend API for SafeChild-Lite child safety application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit default
        "http://localhost:3000",  # React default
        "https://safechild-lite.vercel.app",  # Vercel frontend
        "https://safechild-lite-frontend.vercel.app",  # Alternative Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.vercel.app",
        "*.railway.app",
        "*.herokuapp.com"
    ]
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    global request_count
    request_count += 1
    
    start_time = time.time()
    
    # Log request
    logger.info(f"📥 Request {request_count}: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(f"📤 Response {request_count}: {response.status_code} ({process_time:.3f}s)")
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = str(request_count)
    
    return response

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "message": "Invalid request data provided"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "message": "Please try again later"
        }
    )

# Include API routers without extra prefixes (routers define their own)
app.include_router(chatbot_router)
app.include_router(complaint_router)
app.include_router(emergency_router)
app.include_router(awareness_router)
app.include_router(config_router)
app.include_router(tts_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with application information"""
    return {
        "message": "Welcome to SafeChild-Lite Backend API",
        "version": "1.0.0",
        "description": "Child safety application backend",
        "status": "active",
        "timestamp": TimeUtils().get_current_timestamp()
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global startup_time, request_count
    
    try:
        # Check utilities
        time_utils = TimeUtils()
        text_cleaner = TextCleaner()
        
        # Calculate uptime
        uptime = time.time() - startup_time if startup_time else 0
        
        return {
            "status": "healthy",
            "service": "safechild-lite-backend",
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "uptime_formatted": TimeUtils().get_relative_time(startup_time) if startup_time else "unknown",
            "total_requests": request_count,
            "timestamp": time_utils.get_current_timestamp(),
            "utilities": {
                "time_utils": "active",
                "text_cleaner": "active"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "safechild-lite-backend",
                "error": str(e),
                "timestamp": TimeUtils().get_current_timestamp()
            }
        )

# API status endpoint
@app.get("/api/status")
async def api_status():
    """Get status of all API endpoints"""
    try:
        time_utils = TimeUtils()
        
        # Check each service
        services = {
            "chatbot": {
                "endpoint": "/api/chatbot/health",
                "status": "active"
            },
            "complaint": {
                "endpoint": "/api/complaint/health",
                "status": "active"
            },
            "emergency": {
                "endpoint": "/api/emergency/health",
                "status": "active"
            },
            "awareness": {
                "endpoint": "/api/awareness/health",
                "status": "active"
            }
        }
        
        return {
            "status": "active",
            "services": services,
            "total_services": len(services),
            "timestamp": time_utils.get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"API status check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": TimeUtils().get_current_timestamp()
            }
        )

# Environment info endpoint
@app.get("/api/environment")
async def environment_info():
    """Get environment information (non-sensitive)"""
    try:
        time_utils = TimeUtils()
        
        # Get environment variables (non-sensitive)
        env_info = {
            "NODE_ENV": os.getenv("NODE_ENV", "development"),
            "PYTHON_VERSION": os.getenv("PYTHON_VERSION", "3.9+"),
            "PLATFORM": os.getenv("PLATFORM", "unknown"),
            "DEPLOYMENT": os.getenv("DEPLOYMENT", "local")
        }
        
        # Check if required services are configured
        services_configured = {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "twilio": bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")),
            "tts": True,  # gTTS is local
            "pdf": True   # ReportLab is local
        }
        
        return {
            "environment": env_info,
            "services_configured": services_configured,
            "timestamp": time_utils.get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Environment info check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "timestamp": TimeUtils().get_current_timestamp()
            }
        )

# Metrics endpoint
@app.get("/api/metrics")
async def get_metrics():
    """Get application metrics"""
    global startup_time, request_count
    
    try:
        time_utils = TimeUtils()
        
        # Calculate metrics
        uptime = time.time() - startup_time if startup_time else 0
        requests_per_minute = (request_count / (uptime / 60)) if uptime > 0 else 0
        
        metrics = {
            "uptime_seconds": round(uptime, 2),
            "uptime_formatted": time_utils.get_relative_time(startup_time) if startup_time else "unknown",
            "total_requests": request_count,
            "requests_per_minute": round(requests_per_minute, 2),
            "startup_time": time_utils.format_timestamp(startup_time) if startup_time else None,
            "current_time": time_utils.get_current_timestamp()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "timestamp": TimeUtils().get_current_timestamp()
            }
        )

# API documentation customization
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    """Custom API documentation"""
    return {
        "message": "API Documentation",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json"
    }

# Error handling for 404
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Catch all unmatched routes"""
    logger.warning(f"404 - Route not found: {full_path}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Route '{full_path}' not found",
            "available_routes": [
                "/",
                "/health",
                "/docs",
                "/redoc",
                "/api/status",
                "/api/environment",
                "/api/metrics",
                "/api/chatbot/*",
                "/api/complaint/*",
                "/api/emergency/*",
                "/api/awareness/*"
            ]
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting SafeChild-Lite Backend on {host}:{port}")
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
