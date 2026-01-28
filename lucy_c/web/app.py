from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from flask import Flask, jsonify, render_template
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

    pipeline = LucyPipeline(cfg)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True})

    @socketio.on("connect")
    def on_connect():
        emit("status", {"message": "Connected", "type": "success"})

    @socketio.on("voice_input")
    def on_voice_input(data):
        try:
            raw = data.get("audio")
            if raw is None:
                emit("error", {"message": "Missing audio"})
                return

            # browser sends Array.from(Uint8Array) -> list[int]
            raw_bytes = bytes(raw) if isinstance(raw, list) else raw

            emit("status", {"message": "Decoding...", "type": "info"})
            decoded = decode_audio_bytes_to_f32_mono(raw_bytes, target_sr=pipeline.cfg.audio.sample_rate)

            emit("status", {"message": "Transcribing...", "type": "info"})
            result = pipeline.run_turn_from_audio(decoded.audio)

            if result.transcript:
                emit("message", {"type": "user", "content": result.transcript})

            emit("message", {"type": "assistant", "content": result.reply})

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
