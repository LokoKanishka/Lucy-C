import sys
from pathlib import Path
import logging
import numpy as np

# Add the project root to sys.path
root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

from lucy_c.config import LucyConfig
from lucy_c.mimic3_tts import Mimic3TTS
from lucy_c.asr import FasterWhisperASR

def verify_voice_enhancements():
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger("VerifyVoice")
    
    cfg_path = root / "config" / "config.yaml"
    cfg = LucyConfig.load(cfg_path)
    
    # Enable speed tuning for test
    cfg.tts.length_scale = 0.9 # Slightly faster
    
    # 1. Test TTS Initialization
    log.info("TEST 1: Testing Mimic3 initialization and path detection...")
    try:
        tts = Mimic3TTS(cfg.tts)
        if tts._enabled:
            log.info("SUCCESS: Mimic3 is ENABLED.")
        else:
            log.error("FAILURE: Mimic3 is DISABLED.")
            return # Cannot continue TTS tests
    except Exception as e:
        log.error(f"FAILURE: Mimic3 init failed: {e}")
        return

    # 2. Test TTS Synthesis
    log.info("TEST 2: Testing TTS synthesis with length_scale...")
    try:
        result = tts.synthesize("Hola che, ¿todo bien?")
        if result.audio_f32 is not None and len(result.audio_f32) > 0:
            log.info(f"SUCCESS: Synthesis produced {len(result.audio_f32)} samples at {result.sample_rate}Hz.")
        else:
            log.error("FAILURE: Synthesis produced empty audio.")
    except Exception as e:
        log.error(f"FAILURE: Synthesis failed: {e}")

    # 3. Test ASR Prompting
    log.info("TEST 3: Testing ASR initial_prompt configuration...")
    try:
        # We don't need a real audio for this, just check if it loads with the prompt
        asr = FasterWhisperASR(cfg.asr)
        log.info(f"ASR initial_prompt: {cfg.asr.initial_prompt}")
        log.info("SUCCESS: ASR initialized with Argentine bias.")
    except Exception as e:
        log.error(f"FAILURE: ASR init failed: {e}")

if __name__ == "__main__":
    verify_voice_enhancements()
