import os
import aiohttp
from typing import List, Dict, Any, Optional

from .base import AIProvider


class AIMLProvider:
    name = "aiml"

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("AIML_BASE_URL", "http://localhost:8001")
        self.api_key = api_key or os.getenv("AIML_API_KEY")
        self.model = model or os.getenv("AIML_MODEL", "default")

    async def chat(self, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": (options or {}).get("model", self.model),
            "messages": messages,
            "temperature": (options or {}).get("temperature", 0.7),
            "max_tokens": (options or {}).get("max_tokens", 1000)
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"AIML API error: {resp.status}"}
                data = await resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "content": content, "raw": data, "model": payload["model"]}

    async def complete(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.chat([{"role": "user", "content": prompt}], options)

    async def health(self) -> Dict[str, Any]:
        try:
            url = f"{self.base_url.rstrip('/')}/health"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    return {"status": "healthy" if resp.status == 200 else "unhealthy"}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}


