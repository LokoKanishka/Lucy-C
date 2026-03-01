"""
XTTS Neural Voice Service for Lucy
Coqui TTS with GPU acceleration and voice cloning.
"""

import logging
import time
from pathlib import Path
from typing import Optional
import numpy as np

from lucy_c.config import TTSConfig
from lucy_c.mimic3_tts import TTSResult

log = logging.getLogger("LucyC.XTTS")


class XTTSService:
    """Neural TTS using Coqui XTTS v2 with GPU acceleration."""
    
    def __init__(self, cfg: TTSConfig):
        self.cfg = cfg
        self.log = log
        self.model = None
        self.speaker_wav = None
        self._cache: dict[str, tuple[TTSResult, float]] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._enabled = False
        
        # Try to initialize
        try:
            self._load_model()
            self._load_speaker()
            self._enabled = True
            self.log.info("XTTS neural voice initialized successfully")
        except Exception as e:
            self.log.error(f"Failed to initialize XTTS: {e}")
            self._enabled = False
    
    def _load_model(self):
        """Load XTTS v2 model to GPU if available."""
        try:
            from TTS.api import TTS
            import torch
            
            model_name = getattr(self.cfg, 'model_path', 'tts_models/multilingual/multi-dataset/xtts_v2')
            
            self.log.info(f"Loading XTTS model: {model_name}")
            self.model = TTS(model_name)
            
            # Move to GPU if available and configured
            use_gpu = getattr(self.cfg, 'use_gpu', True)
            if use_gpu and torch.cuda.is_available():
                self.log.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
                self.model.to("cuda")
            else:
                self.log.info("Using CPU (GPU not available or disabled)")
                
        except ImportError as e:
            self.log.error(f"TTS library not installed: {e}")
            raise RuntimeError("TTS library not available. Install with: pip install TTS")
        except Exception as e:
            self.log.error(f"Failed to load XTTS model: {e}")
            raise
    
    def _load_speaker(self):
        """Load speaker reference audio for voice cloning."""
        speaker_path = getattr(self.cfg, 'speaker_wav', 'data/voices/lucy_ref.wav')
        speaker_file = Path(speaker_path)
        
        # If reference doesn't exist, try to use a default
        if not speaker_file.exists():
            self.log.warning(f"Speaker reference not found: {speaker_path}")
            # Try default location
            default_ref = Path(__file__).parent.parent / "data" / "voices" / "default_ref.wav"
            if default_ref.exists():
                speaker_file = default_ref
                self.log.info(f"Using default speaker reference: {default_ref}")
            else:
                self.log.warning("No speaker reference available. Voice cloning may not work optimally.")
                self.speaker_wav = None
                return
        
        self.speaker_wav = str(speaker_file.absolute())
        self.log.info(f"Loaded speaker reference: {self.speaker_wav}")
    
    def synthesize(self, text: str) -> TTSResult:
        """
        Synthesize speech from text using XTTS.
        
        Args:
            text: Text to synthesize
            
        Returns:
            TTSResult with audio data and sample rate
        """
        if not self._enabled:
            raise RuntimeError("XTTS not initialized")
        
        # Cache check
        cache_key = f"xtts:{text}"
        current_time = time.time()
        
        if cache_key in self._cache:
            result, _ = self._cache[cache_key]
            self._cache[cache_key] = (result, current_time)
            self._cache_hits += 1
            hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses) * 100
            self.log.debug(f"TTS Cache HIT ({hit_rate:.1f}%): {text[:30]}")
            return result
        
        self._cache_misses += 1
        
        try:
            # Get language
            language = getattr(self.cfg, 'language', 'es')
            
            # Generate audio
            self.log.debug(f"Synthesizing with XTTS: {text[:50]}...")
            
            if self.speaker_wav:
                # With voice cloning
                wav = self.model.tts(
                    text=text,
                    speaker_wav=self.speaker_wav,
                    language=language
                )
            else:
                # Without voice cloning (will use default voice)
                wav = self.model.tts(
                    text=text,
                    language=language
                )
            
            # Convert to numpy array
            if isinstance(wav, list):
                wav = np.array(wav, dtype=np.float32)
            
            # Ensure mono
            if wav.ndim == 2:
                wav = wav[:, 0]
            
            # Get sample rate from model
            sample_rate = self.model.synthesizer.output_sample_rate if hasattr(self.model, 'synthesizer') else 22050
            
            result = TTSResult(
                audio_f32=wav.astype(np.float32).reshape(-1),
                sample_rate=sample_rate
            )
            
            # Cache management (LRU)
            MAX_CACHE_SIZE = 100
            if len(self._cache) >= MAX_CACHE_SIZE:
                items = sorted(self._cache.items(), key=lambda x: x[1][1])
                evict_count = int(MAX_CACHE_SIZE * 0.3)
                for key, _ in items[:evict_count]:
                    del self._cache[key]
                self.log.info(f"TTS cache evicted {evict_count} items (LRU)")
            
            self._cache[cache_key] = (result, current_time)
            
            return result
            
        except Exception as e:
            self.log.error(f"XTTS synthesis failed: {e}")
            raise
