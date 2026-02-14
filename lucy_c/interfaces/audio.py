from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np

@dataclass
class TTSResult:
    audio_f32: np.ndarray
    sample_rate: int

@dataclass
class ASRResult:
    text: str
    language: str

class TTSProvider(ABC):
    """Abstract contract for Text-To-Speech providers."""
    
    @abstractmethod
    def synthesize(self, text: str) -> TTSResult:
        """Convert text to audio."""
        pass

class ASRProvider(ABC):
    """Abstract contract for Automatic Speech Recognition providers."""
    
    @abstractmethod
    def transcribe(self, audio_f32: np.ndarray) -> ASRResult:
        """Convert audio to text."""
        pass
