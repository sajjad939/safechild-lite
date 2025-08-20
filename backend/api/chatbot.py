from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime

from backend.services.gptService import GPTService
from utils.textCleaner import TextCleaner
from utils.timeUtils import TimeUtils

logger = logging.getLogger(__name__)

# Initialize services
gpt_service = GPTService()
text_cleaner = TextCleaner()
time_utils = TimeUtils()

# In-memory storage for chat sessions (replace with database in production)
chat_sessions = {}

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

class ChatMessage(BaseModel):
    """Model for chat message"""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context information")

class ChatResponse(BaseModel):
    """Model for chat response"""
    success: bool = Field(..., description="Whether the request was successful")
    response: str = Field(..., description="AI response message")
    session_id: str = Field(..., description="Chat session ID")
    timestamp: str = Field(..., description="Response timestamp")
    message_id: str = Field(..., description="Unique message ID")
    model_info: Optional[Dict[str, Any]] = Field(None, description="AI model information")
    fallback: Optional[bool] = Field(False, description="Whether fallback response was used")

class ChatSession(BaseModel):
    """Model for chat session"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    created_at: str = Field(..., description="Session creation timestamp")
    last_activity: str = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Total message count")
    status: str = Field(..., description="Session status")

class ChatHistory(BaseModel):
    """Model for chat history"""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, str]] = Field(..., description="Chat messages")
    total_messages: int = Field(..., description="Total message count")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(chat_message: ChatMessage, request: Request):
    """Chat with the SafeChild AI bot"""
    try:
        # Validate and clean input
        if not chat_message.message or not chat_message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        cleaned_message = text_cleaner.clean_text(chat_message.message)
        if not cleaned_message:
            raise HTTPException(status_code=400, detail="Message contains invalid content")
        
        # Get or create session
        session_id = chat_message.session_id or _generate_session_id()
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "user_id": _extract_user_id(request),
                "created_at": time_utils.get_current_timestamp(),
                "last_activity": time_utils.get_current_timestamp(),
                "message_count": 0,
                "status": "active",
                "messages": []
            }
        
        # Update session activity
        chat_sessions[session_id]["last_activity"] = time_utils.get_current_timestamp()
        chat_sessions[session_id]["message_count"] += 1
        
        # Add user message to history
        user_message = {
            "role": "user",
            "content": cleaned_message,
            "timestamp": time_utils.get_current_timestamp()
        }
        chat_sessions[session_id]["messages"].append(user_message)
        
        # Get AI response
        user_context = chat_message.user_context or {}
        ai_response = await gpt_service.get_chatbot_response(
            cleaned_message,
            chat_sessions[session_id]["messages"],
            user_context
        )
        
        if not ai_response["success"]:
            logger.warning(f"GPT service failed for session {session_id}: {ai_response.get('error')}")
        
        # Add AI response to history
        ai_message = {
            "role": "assistant",
            "content": ai_response.get("response", "I'm sorry, I couldn't process your request."),
            "timestamp": time_utils.get_current_timestamp()
        }
        chat_sessions[session_id]["messages"].append(ai_message)
        
        # Generate message ID
        message_id = _generate_message_id()
        
        # Prepare response
        response_data = {
            "success": ai_response.get("success", False),
            "response": ai_response.get("response", "I'm sorry, I couldn't process your request."),
            "session_id": session_id,
            "timestamp": time_utils.get_current_timestamp(),
            "message_id": message_id,
            "model_info": {
                "model": ai_response.get("model"),
                "tokens_used": ai_response.get("tokens_used"),
                "fallback": ai_response.get("fallback", False)
            } if ai_response.get("success") else None,
            "fallback": ai_response.get("fallback", False)
        }
        
        logger.info(f"Chat response generated for session {session_id}, message ID: {message_id}")
        return ChatResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=ChatResponse)
async def chat_with_bot_root(chat_message: ChatMessage, request: Request):
    return await chat_with_bot(chat_message, request)

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    """Get chat session information"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = chat_sessions[session_id]
        return ChatSession(
            session_id=session_id,
            user_id=session.get("user_id"),
            created_at=session["created_at"],
            last_activity=session["last_activity"],
            message_count=session["message_count"],
            status=session["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions/{session_id}/history", response_model=ChatHistory)
async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat history for a session"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        session = chat_sessions[session_id]
        messages = session["messages"][-limit:] if limit < len(session["messages"]) else session["messages"]
        
        return ChatHistory(
            session_id=session_id,
            messages=messages,
            total_messages=len(session["messages"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        deleted_session = chat_sessions.pop(session_id)
        logger.info(f"Deleted chat session {session_id} with {deleted_session['message_count']} messages")
        
        return {"success": True, "message": f"Session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/{session_id}/clear")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        message_count = len(chat_sessions[session_id]["messages"])
        chat_sessions[session_id]["messages"] = []
        chat_sessions[session_id]["message_count"] = 0
        
        logger.info(f"Cleared chat history for session {session_id}, removed {message_count} messages")
        
        return {
            "success": True, 
            "message": f"Chat history cleared for session {session_id}",
            "messages_removed": message_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions", response_model=List[ChatSession])
async def list_chat_sessions(limit: int = 20, offset: int = 0):
    """List all chat sessions"""
    try:
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        sessions = list(chat_sessions.values())
        sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        
        paginated_sessions = sessions[offset:offset + limit]
        
        return [
            ChatSession(
                session_id=session_id,
                user_id=session.get("user_id"),
                created_at=session["created_at"],
                last_activity=session["last_activity"],
                message_count=session["message_count"],
                status=session["status"]
            )
            for session_id, session in list(chat_sessions.items())[offset:offset + limit]
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/analyze")
async def analyze_safety_concern(concern_data: Dict[str, Any]):
    """Analyze a safety concern using AI"""
    try:
        concern_text = concern_data.get("concern_text", "")
        analysis_type = concern_data.get("analysis_type", "general")
        
        if not concern_text or not concern_text.strip():
            raise HTTPException(status_code=400, detail="Concern text cannot be empty")
        
        cleaned_text = text_cleaner.clean_text(concern_text)
        if not cleaned_text:
            raise HTTPException(status_code=400, detail="Concern text contains invalid content")
        
        # Get AI analysis
        analysis_result = await gpt_service.analyze_safety_concern(cleaned_text, analysis_type)
        
        if not analysis_result["success"]:
            logger.warning(f"Safety concern analysis failed: {analysis_result.get('error')}")
        
        return {
            "success": analysis_result.get("success", False),
            "analysis": analysis_result.get("analysis", "Analysis could not be completed."),
            "analysis_type": analysis_type,
            "risk_level": analysis_result.get("risk_level", "unknown"),
            "recommendations": analysis_result.get("recommendations", []),
            "timestamp": time_utils.get_current_timestamp(),
            "fallback": analysis_result.get("fallback", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing safety concern: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def chatbot_health():
    """Check chatbot service health"""
    try:
        # Check GPT service health
        gpt_health = await gpt_service.health_check()
        
        # Check session status
        active_sessions = len([s for s in chat_sessions.values() if s["status"] == "active"])
        total_sessions = len(chat_sessions)
        
        return {
            "status": "healthy" if gpt_health["status"] == "healthy" else "degraded",
            "service": "Chatbot API",
            "gpt_service": gpt_health,
            "sessions": {
                "active": active_sessions,
                "total": total_sessions
            },
            "timestamp": time_utils.get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error in chatbot health check: {e}")
        return {
            "status": "unhealthy",
            "service": "Chatbot API",
            "error": str(e),
            "timestamp": time_utils.get_current_timestamp()
        }

@router.get("/stats")
async def get_chatbot_stats():
    """Get chatbot usage statistics"""
    try:
        # Calculate statistics
        total_messages = sum(session["message_count"] for session in chat_sessions.values())
        avg_messages_per_session = total_messages / len(chat_sessions) if chat_sessions else 0
        
        # Get GPT service stats
        gpt_stats = gpt_service.get_usage_stats()
        
        return {
            "sessions": {
                "total": len(chat_sessions),
                "active": len([s for s in chat_sessions.values() if s["status"] == "active"])
            },
            "messages": {
                "total": total_messages,
                "average_per_session": round(avg_messages_per_session, 2)
            },
            "gpt_service": gpt_stats,
            "timestamp": time_utils.get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error getting chatbot stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def _generate_session_id() -> str:
    """Generate unique session ID"""
    import uuid
    return str(uuid.uuid4())

def _generate_message_id() -> str:
    """Generate unique message ID"""
    import uuid
    return str(uuid.uuid4())

def _extract_user_id(request: Request) -> Optional[str]:
    """Extract user ID from request (implement based on your authentication system)"""
    # Extract from headers or return anonymous user
    user_id = request.headers.get("X-User-ID")
    return user_id or "anonymous"
