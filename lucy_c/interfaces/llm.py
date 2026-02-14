from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMResponse:
    text: str
    raw_response: Any = None
    usage: Optional = None

class LLMProvider(ABC):
    """Abstract contract for AI providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Simple text completion."""
        pass

    @abstractmethod
    def chat(self, messages: List, **kwargs) -> LLMResponse:
        """Chat-based generation."""
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models."""
        pass
