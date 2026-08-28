"""LLM provider service supporting local Ollama, OpenRouter, and OpenAI-compatible backends."""
from __future__ import annotations

import logging
from openai import OpenAI

from services.config_service import get_config

logger = logging.getLogger(__name__)


class LLMService:
    """Standardized interface for LLM completions."""

    def __init__(self):
        self.config = get_config()
        self.provider = self.config.llm.provider.lower()
        self.model = self.config.llm.model
        self.base_url = self.config.llm.base_url
        self.api_key = self.config.llm.api_key or "noop"  # Ollama doesn't validate API keys
        
        # Configure client base URL based on provider settings
        if self.provider == "ollama":
            # Add /v1 to Ollama base URL if not present
            if not self.base_url.endswith("/v1") and not self.base_url.endswith("/v1/"):
                self.base_url = f"{self.base_url.rstrip('/')}/v1"
        elif self.provider == "openrouter":
            self.base_url = "https://openrouter.ai/api/v1"
            
        logger.info("Initializing LLM Service using %s (%s) | Endpoint: %s", self.provider, self.model, self.base_url)
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.config.llm.timeout
        )

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        temperature: float | None = None
    ) -> str:
        """Fetch chat completion from LLM provider."""
        temp = temperature if temperature is not None else self.config.llm.temperature
        
        extra_args = {}
        if json_mode:
            extra_args["response_format"] = {"type": "json_object"}
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temp,
            max_tokens=self.config.llm.max_tokens,
            **extra_args
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response returned from LLM provider.")
            
        return content.strip()
