import os
from typing import Dict, Any, Optional

from .providers.openai_provider import OpenAIProvider
from .providers.aiml_provider import AIMLProvider


class AIManager:
    """Runtime-configurable AI provider manager"""

    def __init__(self):
        self.provider_name = os.getenv("AI_PROVIDER", "openai").lower()
        self.config: Dict[str, Any] = {
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4")
            },
            "aiml": {
                "base_url": os.getenv("AIML_BASE_URL", "http://localhost:8001"),
                "api_key": os.getenv("AIML_API_KEY"),
                "model": os.getenv("AIML_MODEL", "default")
            }
        }
        self._provider = self._build_provider(self.provider_name)

    def _build_provider(self, name: str):
        if name == "aiml":
            cfg = self.config["aiml"]
            return AIMLProvider(cfg.get("base_url"), cfg.get("api_key"), cfg.get("model"))
        # default: openai
        cfg = self.config["openai"]
        return OpenAIProvider(cfg.get("api_key"), cfg.get("model"))

    def get_provider(self):
        return self._provider

    def set_provider(self, name: str, cfg: Optional[Dict[str, Any]] = None):
        name = name.lower()
        if name not in ("openai", "aiml"):
            raise ValueError("Unsupported provider")
        if cfg:
            self.config[name].update(cfg)
        self.provider_name = name
        self._provider = self._build_provider(name)

    def get_config(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "config": self.config.get(self.provider_name, {})
        }


