from __future__ import annotations

import logging
from dataclasses import dataclass

from lucy_c.asr import FasterWhisperASR
from lucy_c.clawdbot_llm import ClawdbotLLM
from lucy_c.config import LucyConfig
from lucy_c.mimic3_tts import Mimic3TTS
from lucy_c.ollama_llm import OllamaLLM
from lucy_c.text_normalizer import normalize_for_tts


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

        self.ollama = OllamaLLM(cfg.ollama)
        self.clawdbot = ClawdbotLLM(cfg.clawdbot)

        self.tts = Mimic3TTS(cfg.tts)

    def _generate_reply(self, text: str, *, session_user: str | None = None) -> str:
        provider = (self.cfg.llm.provider or "ollama").lower()
        model = self.cfg.ollama.model
        if provider == "clawdbot":
            if not self.cfg.clawdbot.token:
                return "Clawdbot token no configurado (CLAWDBOT_GATEWAY_TOKEN)."
            return self.clawdbot.generate(text, model=model, user=session_user).text
        return self.ollama.generate(text, model=model).text

    def _tts_bytes(self, reply_text: str) -> tuple[bytes, int]:
        """Return (wav_bytes, sample_rate). Empty wav if TTS fails."""
        try:
            tts_text = normalize_for_tts(reply_text)
            tts_res = self.tts.synthesize(tts_text)
            from lucy_c.audio_codec import encode_wav_bytes

            wav = encode_wav_bytes(tts_res.audio_f32, tts_res.sample_rate)
            return wav, tts_res.sample_rate
        except Exception as e:
            self.log.warning("TTS failed (%s). Continuing with text-only.", e)
            return b"", 0

    def run_turn_from_text(self, text: str, *, session_user: str | None = None) -> TurnResult:
        transcript = (text or "").strip()
        if not transcript:
            reply = "Decime algo."
        else:
            reply = self._generate_reply(transcript, session_user=session_user)

        wav, sr = self._tts_bytes(reply)
        return TurnResult(transcript=transcript, reply=reply, reply_wav=wav, reply_sr=sr)

    def run_turn_from_audio(self, audio_f32, *, session_user: str | None = None) -> TurnResult:
        asr_res = self.asr.transcribe(audio_f32)
        transcript = asr_res.text.strip()
        if not transcript:
            reply = "No escuché nada."
        else:
            reply = self._generate_reply(transcript, session_user=session_user)

        wav, sr = self._tts_bytes(reply)
        return TurnResult(transcript=transcript, reply=reply, reply_wav=wav, reply_sr=sr)
