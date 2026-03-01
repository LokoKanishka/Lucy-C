from __future__ import annotations
import logging
import numpy as np
from typing import Optional

from lucy_c.interfaces.audio import ASRProvider, TTSProvider
from lucy_c.audio_codec import encode_wav_bytes

class SensorySystem:
    """
    Abstractions for Lucy's senses (Hearing and Speaking).
    Manages ASR and TTS interactions.
    """
    def __init__(self, asr: ASRProvider, tts: TTSProvider):
        self.asr = asr
        self.tts = tts
        self.log = logging.getLogger("LucyC.Senses")

    def listen(self, audio_input: np.ndarray) -> str:
        """Process audio input to text."""
        try:
            result = self.asr.transcribe(audio_f32=audio_input)
            text = result.text.strip()
            if text:
                self.log.info("Heard: %s (Lang: %s)", text, result.language)
            return text
        except Exception as e:
            self.log.error("Hearing failure: %s", e)
            return ""

    def speak(self, text: str) -> tuple[bytes, int]:
        """Process text output to audio bytes."""
        try:
            # We assume text is already normalized or the provider handles it
            # But the old pipeline did normalize_for_tts. Let's incorporate that if needed or rely on provider.
            # Ideally the provider should handle it, but for compatibility let's do it here or inside Orchestrator.
            # Let's assume Orchestrator passes clean text, or provider handles it. 
            # Actually, let's look at mimic3_tts.py... it just synthesizes. 
            # Safe to assume simple string for now.
            
            # Note: pipeline.py imported normalize_for_tts. We should probably keep that logic 
            # either here or in the Cognitive engine's output processing. 
            # Putting it here seems 'sensory'.
            from lucy_c.text_normalizer import normalize_for_tts
            clean_text = normalize_for_tts(text)
            
            res = self.tts.synthesize(clean_text)
            
            # Encode to WAV bytes for transport
            wav_bytes = encode_wav_bytes(res.audio_f32, res.sample_rate)
            return wav_bytes, res.sample_rate
        except Exception as e:
            self.log.error("Speaking failure: %s", e)
            return b"", 0
