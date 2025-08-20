from typing import List, Dict, Any, Optional, Protocol


class AIProvider(Protocol):
    """Protocol for AI provider implementations"""

    name: str

    async def chat(self, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ...

    async def complete(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ...

    async def health(self) -> Dict[str, Any]:
        ...


