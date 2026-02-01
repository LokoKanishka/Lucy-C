from __future__ import annotations

import io
import logging
import subprocess
from dataclasses import dataclass

import numpy as np
import soundfile as sf

from lucy_c.config import TTSConfig


@dataclass
class TTSResult:
    audio_f32: np.ndarray
    sample_rate: int


class Mimic3TTS:
    def __init__(self, cfg: TTSConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Mimic3")
        self._cache: dict[str, tuple[TTSResult, float]] = {}  # key -> (result, last_access_time)
        self._cache_hits = 0
        self._cache_misses = 0

    def synthesize(self, text: str) -> TTSResult:
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
        
        proc = subprocess.run(
            ["mimic3", "--voice", self.cfg.voice, "--stdout"],
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
