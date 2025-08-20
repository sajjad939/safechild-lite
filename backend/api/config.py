from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from backend.services.ai.ai_manager import AIManager


router = APIRouter(prefix="/api/config", tags=["config"])

ai_manager = AIManager()


class ProviderConfig(BaseModel):
    provider: str = Field(..., description="'openai' or 'aiml'")
    config: Optional[Dict[str, Any]] = None


@router.get("/ai")
async def get_ai_config():
    return ai_manager.get_config()


@router.post("/ai")
async def set_ai_config(body: ProviderConfig):
    try:
        ai_manager.set_provider(body.provider, body.config or {})
        return {"success": True, **ai_manager.get_config()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ai/health")
async def ai_health():
    provider = ai_manager.get_provider()
    return await provider.health()


