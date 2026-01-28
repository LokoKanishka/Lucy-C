from __future__ import annotations

import logging
from dataclasses import dataclass

from lucy_c.asr import FasterWhisperASR
from lucy_c.config import LucyConfig
from lucy_c.mimic3_tts import Mimic3TTS
from lucy_c.ollama_llm import OllamaLLM


@dataclass
class TurnResult:
    transcript: str
    reply: str
    reply_wav: bytes
    reply_sr: int


class LucyPipeline:
    def __init__(self, cfg: LucyConfig):
        self.cfg = cfg
        self.log = logging.getLogger("LucyC.Pipeline")
        self.asr = FasterWhisperASR(cfg.asr)
        self.llm = OllamaLLM(cfg.ollama)
        self.tts = Mimic3TTS(cfg.tts)

    def run_turn_from_text(self, text: str) -> TurnResult:
        transcript = (text or "").strip()
        if not transcript:
            reply = "Decime algo."
        else:
            reply = self.llm.generate(transcript).text

        reply_wav = b""
        reply_sr = 0
        try:
            tts_res = self.tts.synthesize(reply)
            from lucy_c.audio_codec import encode_wav_bytes

            reply_wav = encode_wav_bytes(tts_res.audio_f32, tts_res.sample_rate)
            reply_sr = tts_res.sample_rate
        except Exception as e:
            self.log.warning("TTS failed (%s). Continuing with text-only.", e)

        return TurnResult(transcript=transcript, reply=reply, reply_wav=reply_wav, reply_sr=reply_sr)

    def run_turn_from_audio(self, audio_f32) -> TurnResult:
        asr_res = self.asr.transcribe(audio_f32)
        transcript = asr_res.text.strip()
        if not transcript:
            reply = "No escuché nada."
        else:
            reply = self.llm.generate(transcript).text

        reply_wav = b""
        reply_sr = 0
        try:
            tts_res = self.tts.synthesize(reply)
            from lucy_c.audio_codec import encode_wav_bytes

            reply_wav = encode_wav_bytes(tts_res.audio_f32, tts_res.sample_rate)
            reply_sr = tts_res.sample_rate
        except Exception as e:
            self.log.warning("TTS failed (%s). Continuing with text-only.", e)

        return TurnResult(transcript=transcript, reply=reply, reply_wav=reply_wav, reply_sr=reply_sr)
