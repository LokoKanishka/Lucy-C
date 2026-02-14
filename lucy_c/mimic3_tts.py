from __future__ import annotations

import io
import logging
import subprocess

import numpy as np
import soundfile as sf

from lucy_c.config import TTSConfig
from lucy_c.interfaces.audio import TTSProvider, TTSResult


class Mimic3TTS(TTSProvider):
    def __init__(self, cfg: TTSConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Mimic3")
        self._cache: dict[str, tuple[TTSResult, float]] = {}  # key -> (result, last_access_time)
        self._cache_hits = 0
        self._cache_misses = 0
        self._enabled = self._check_executable()

    def _check_executable(self) -> bool:
        import shutil
        from pathlib import Path
        
        # 1. Check PATH
        self._exe_path = shutil.which("mimic3")
        if self._exe_path:
            return True
            
        # 2. Check current .venv/bin (project root)
        # mimic3_tts.py is in lucy_c/, so parents[1] is project root
        venv_mimic = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "mimic3"
        if venv_mimic.exists():
            self._exe_path = str(venv_mimic)
            return True
            
        self.log.warning("mimic3 executable not found in PATH or .venv. Voice output will be disabled.")
        return False

    def synthesize(self, text: str) -> TTSResult:
        if not self._enabled:
            raise RuntimeError("mimic3 not found")
        import time
        
        # Simple cache to avoid re-running mimic3 for identical text
        cache_key = f"{self.cfg.voice}:{text}"
        current_time = time.time()
        
        if cache_key in self._cache:
            result, _ = self._cache[cache_key]
            self._cache[cache_key] = (result, current_time)  # Update access time
            self._cache_hits += 1
            hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses) * 100
            self.log.debug("TTS Cache HIT (%.1f%% hit rate): %s", hit_rate, text[:30])
            return result

        self._cache_misses += 1
        
        cmd = [self._exe_path, "--voice", self.cfg.voice, "--stdout"]
        
        # Add speed/length_scale if present
        if hasattr(self.cfg, "length_scale"):
            cmd.extend(["--length-scale", str(self.cfg.length_scale)])
            
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"mimic3 failed: {proc.stderr.decode('utf-8', 'ignore')}")

        with io.BytesIO(proc.stdout) as bio:
            data, sr = sf.read(bio, dtype="float32")

        if data.ndim == 2:
            data = data[:, 0]
        
        res = TTSResult(audio_f32=np.asarray(data, dtype=np.float32).reshape(-1), sample_rate=sr)
        
        # LRU eviction: Keep cache under limit
        MAX_CACHE_SIZE = 100
        if len(self._cache) >= MAX_CACHE_SIZE:
            # Evict oldest 30% by access time
            items = sorted(self._cache.items(), key=lambda x: x[1][1])
            evict_count = int(MAX_CACHE_SIZE * 0.3)
            for key, _ in items[:evict_count]:
                del self._cache[key]
            self.log.info("TTS cache evicted %d items (LRU)", evict_count)
        
        self._cache[cache_key] = (res, current_time)
        
        return res
