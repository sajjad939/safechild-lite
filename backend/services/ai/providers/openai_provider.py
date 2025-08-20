import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from .base import AIProvider


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def chat(self, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.client:
            return {"success": False, "error": "OpenAI API key not configured"}
        opts = options or {}
        resp = await self.client.chat.completions.create(
            model=opts.get("model", self.model),
            messages=messages,
            max_tokens=opts.get("max_tokens", 1000),
            temperature=opts.get("temperature", 0.7),
            timeout=opts.get("timeout", 30.0),
        )
        content = resp.choices[0].message.content if resp.choices and resp.choices[0].message else ""
        return {
            "success": True,
            "content": content,
            "usage": getattr(resp, "usage", None),
            "model": opts.get("model", self.model)
        }

    async def complete(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # For simplicity, reuse chat with single user message
        return await self.chat([{"role": "user", "content": prompt}], options)

    async def health(self) -> Dict[str, Any]:
        return {"status": "available" if self.client else "unavailable", "model": self.model}


