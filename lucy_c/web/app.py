from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from lucy_c.audio_codec import decode_audio_bytes_to_f32_mono
from lucy_c.config import LucyConfig
from lucy_c.pipeline import LucyPipeline


log = logging.getLogger("LucyC.Web")


def create_app() -> tuple[Flask, SocketIO, LucyPipeline]:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("LUCY_C_SECRET", "lucy-c")

    socketio = SocketIO(app, cors_allowed_origins="*")

    root = Path(__file__).resolve().parents[2]
    cfg_path = os.environ.get("LUCY_C_CONFIG", str(root / "config" / "config.yaml"))
    cfg = LucyConfig.load(cfg_path)

    # Pull Clawdbot token from env if present (recommended)
    cfg.clawdbot.token = os.environ.get("CLAWDBOT_GATEWAY_TOKEN", cfg.clawdbot.token)

    pipeline = LucyPipeline(cfg)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/api/models")
    def models():
        try:
            models = pipeline.ollama.list_models()
        except Exception as e:
            return jsonify({"models": [], "current": pipeline.cfg.ollama.model, "error": str(e)})
        return jsonify({"models": models, "current": pipeline.cfg.ollama.model, "provider": pipeline.cfg.llm.provider})

    @app.route("/api/chat", methods=["POST"])
    def chat_http():
        """HTTP fallback for when Socket.IO is blocked or flaky."""
        payload = request.get_json(silent=True) or {}
        text = (payload.get("message") or "").strip()
        if not text:
            return jsonify({"ok": False, "error": "empty message"}), 400

        session_user = (payload.get("session_user") or "").strip() or None
        result = pipeline.run_turn_from_text(text, session_user=session_user)
        resp = {"ok": True, "reply": result.reply}
        if result.reply_wav:
            resp["audio"] = {
                "mime": "audio/wav",
                "sample_rate": result.reply_sr,
                "wav_base64": base64.b64encode(result.reply_wav).decode("ascii"),
            }
        return jsonify(resp)

    @socketio.on("connect")
    def on_connect():
        emit("status", {"message": "Connected", "type": "success"})

    @socketio.on("update_config")
    def on_update_config(data):
        try:
            data = data or {}
            provider = data.get("llm_provider")
            if provider:
                pipeline.cfg.llm.provider = str(provider)
                emit("status", {"message": f"Provider set to {provider}", "type": "success"})

            model = data.get("ollama_model")
            if model:
                pipeline.cfg.ollama.model = model
                pipeline.ollama.cfg.model = model
                emit("status", {"message": f"Model set to {model}", "type": "success"})

            if not provider and not model:
                emit("status", {"message": "No config changes", "type": "info"})
        except Exception as e:
            emit("error", {"message": str(e)})

    @socketio.on("chat_message")
    def on_chat_message(data):
        try:
            text = (data or {}).get("message", "")
            text = (text or "").strip()
            if not text:
                return

            emit("message", {"type": "user", "content": text})
            emit("status", {"message": "Thinking...", "type": "info"})

            session_user = (data or {}).get("session_user")
            result = pipeline.run_turn_from_text(text, session_user=session_user)

            emit("message", {"type": "assistant", "content": result.reply})
            if result.reply_wav:
                emit(
                    "audio",
                    {
                        "mime": "audio/wav",
                        "sample_rate": result.reply_sr,
                        "wav_base64": base64.b64encode(result.reply_wav).decode("ascii"),
                    },
                )
            emit("status", {"message": "Ready", "type": "success"})

        except Exception as e:
            log.exception("chat_message failed")
            emit("error", {"message": str(e)})

    @socketio.on("voice_input")
    def on_voice_input(data):
        try:
            raw = (data or {}).get("audio")
            if raw is None:
                emit("error", {"message": "Missing audio"})
                return

            raw_bytes = bytes(raw) if isinstance(raw, list) else raw

            emit("status", {"message": "Decoding...", "type": "info"})
            decoded = decode_audio_bytes_to_f32_mono(raw_bytes, target_sr=pipeline.cfg.audio.sample_rate)

            emit("status", {"message": "Transcribing...", "type": "info"})
            session_user = (data or {}).get("session_user")
            result = pipeline.run_turn_from_audio(decoded.audio, session_user=session_user)

            if result.transcript:
                emit("message", {"type": "user", "content": result.transcript})

            emit("message", {"type": "assistant", "content": result.reply})

            if result.reply_wav:
                emit(
                    "audio",
                    {
                        "mime": "audio/wav",
                        "sample_rate": result.reply_sr,
                        "wav_base64": base64.b64encode(result.reply_wav).decode("ascii"),
                    },
                )

            emit("status", {"message": "Ready", "type": "success"})

        except Exception as e:
            log.exception("voice_input failed")
            emit("error", {"message": str(e)})

    return app, socketio, pipeline


def main():
    logging.basicConfig(level=logging.INFO)
    app, socketio, _pipeline = create_app()
    port = int(os.environ.get("PORT", "5000"))

    # eventlet server
    socketio.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
