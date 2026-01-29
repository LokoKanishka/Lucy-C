from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from lucy_c.audio_codec import decode_audio_bytes_to_f32_mono
from lucy_c.config import LucyConfig
from lucy_c.history_store import HistoryItem, HistoryStore, default_history_dir
from lucy_c.pipeline import LucyPipeline


log = logging.getLogger("LucyC.Web")


def create_app() -> tuple[Flask, SocketIO, LucyPipeline]:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("LUCY_C_SECRET", "lucy-c")
    # Disable caching so UI updates appear immediately after reload
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    socketio = SocketIO(app, cors_allowed_origins="*")

    root = Path(__file__).resolve().parents[2]
    cfg_path = os.environ.get("LUCY_C_CONFIG", str(root / "config" / "config.yaml"))
    cfg = LucyConfig.load(cfg_path)

    # Pull Clawdbot token from env if present (recommended)
    cfg.clawdbot.token = os.environ.get("CLAWDBOT_GATEWAY_TOKEN", cfg.clawdbot.token)

    pipeline = LucyPipeline(cfg)
    history = HistoryStore(default_history_dir())

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

        session_user = (payload.get("session_user") or "").strip() or "lucy-c:anonymous"
        result = pipeline.run_turn_from_text(text, session_user=session_user)

        history.append(
            HistoryItem(
                ts=time.time(),
                session_user=session_user,
                kind="text",
                llm_provider=pipeline.cfg.llm.provider,
                ollama_model=pipeline.cfg.ollama.model,
                user_text=text,
                transcript=text,
                reply=result.reply,
            )
        )

        resp = {"ok": True, "reply": result.reply}
        if result.reply_wav:
            resp["audio"] = {
                "mime": "audio/wav",
                "sample_rate": result.reply_sr,
                "wav_base64": base64.b64encode(result.reply_wav).decode("ascii"),
            }
        return jsonify(resp)

    @app.route("/api/history")
    def history_api():
        session_user = (request.args.get("session_user") or "").strip() or "lucy-c:anonymous"
        limit = int(request.args.get("limit") or "200")
        items = history.read(session_user=session_user, limit=limit)
        return jsonify({"ok": True, "session_user": session_user, "items": items})

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

            session_user = session_user or "lucy-c:anonymous"
            history.append(
                HistoryItem(
                    ts=time.time(),
                    session_user=session_user,
                    kind="text",
                    llm_provider=pipeline.cfg.llm.provider,
                    ollama_model=pipeline.cfg.ollama.model,
                    user_text=text,
                    transcript=text,
                    reply=result.reply,
                )
            )

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
            session_user = (data or {}).get("session_user") or "lucy-c:anonymous"
            handsfree = bool((data or {}).get("handsfree"))
            result = pipeline.run_turn_from_audio(decoded.audio, session_user=session_user)

            # In hands-free mode, ignore tiny/one-word junk to prevent loops.
            if handsfree:
                words = [w for w in (result.transcript or "").strip().split() if w]
                if len(words) < 2:
                    emit("status", {"message": "(Ignorado: muy corto)", "type": "info"})
                    return

            if result.transcript:
                emit("message", {"type": "user", "content": result.transcript})

            emit("message", {"type": "assistant", "content": result.reply})

            history.append(
                HistoryItem(
                    ts=time.time(),
                    session_user=session_user,
                    kind="voice",
                    llm_provider=pipeline.cfg.llm.provider,
                    ollama_model=pipeline.cfg.ollama.model,
                    user_text="",
                    transcript=result.transcript,
                    reply=result.reply,
                )
            )

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
