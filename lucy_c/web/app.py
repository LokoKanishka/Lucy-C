from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit

from lucy_c.audio_codec import decode_audio_bytes_to_f32_mono
from lucy_c.config import LucyConfig
from lucy_c.history_store import HistoryItem, HistoryStore, default_history_dir
from lucy_c.facts_store import FactsStore, default_facts_dir
from lucy_c.pipeline import Moltbot


log = logging.getLogger("LucyC.Web")


def create_app() -> tuple[Flask, SocketIO, Moltbot]:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("LUCY_C_SECRET", "lucy-c")
    # Disable caching so UI updates appear immediately after reload
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    socketio = SocketIO(app, cors_allowed_origins="*")

    # Enhanced status callback that emits both generic status and tool events
    def status_callback(message: str, type: str = "info"):
        socketio.emit("status", {"message": message, "type": type})
        
        # Detect tool execution and emit structured event
        tool_badges = {
            "Mirando pantalla": ("screenshot", "sensor", "👁️"),
            "Haciendo clic": ("click", "actuator", "🖐️"),
            "Escribiendo": ("type", "actuator", "⌨️"),
            "Usando atajo": ("hotkey", "actuator", "⌨️"),
            "Moviendo el mouse": ("move", "actuator", "🖱️"),
            "Leyendo archivo": ("read_file", "sensor", "📄"),
            "Escribiendo archivo": ("write_file", "actuator", "📝"),
            "Guardando en memoria": ("memorize_file", "memory", "🧠"),
            "Ejecutando herramientas": ("tool_execution", "actuator", "⚙️"),
            "Buscando en internet": ("search_web", "sensor", "🔍"),
            "Abriendo aplicación": ("os_run", "actuator", "🖐️"),
        }
        
        for msg_pattern, (tool_name, category, emoji) in tool_badges.items():
            if msg_pattern.lower() in message.lower():
                socketio.emit("tool_event", {
                    "tool": tool_name,
                    "category": category,
                    "emoji": emoji,
                    "status": "running",
                    "message": message
                })
                break

    root = Path(__file__).resolve().parents[2]
    cfg_path = os.environ.get("LUCY_C_CONFIG", str(root / "config" / "config.yaml"))
    cfg = LucyConfig.load(cfg_path)

    # Pull Clawdbot token from env if present (recommended)
    cfg.clawdbot.token = os.environ.get("CLAWDBOT_GATEWAY_TOKEN", cfg.clawdbot.token)

    history = HistoryStore(default_history_dir())
    facts = FactsStore(default_facts_dir())
    moltbot = Moltbot(cfg, history=history, facts=facts, status_callback=status_callback)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/api/models")
    def models():
        try:
            detailed = moltbot.ollama.list_models_detailed()
            # Convert dataclasses to dicts for JSON
            from dataclasses import asdict
            models_data = [asdict(m) for m in detailed]
            
            # Add synthetic Clawdbot model if selected
            if moltbot.cfg.llm.provider == "clawdbot":
                from lucy_c.models_registry import ModelMetadata
                claw_meta = ModelMetadata(
                    name=moltbot.cfg.clawdbot.agent_id or "lucy",
                    size_gb=0.0,
                    modified_at="persistent",
                    family="clawdbot",
                    is_vision=True
                )
                models_data.append(asdict(claw_meta))
        except Exception as e:
            log.exception("Failed to list models")
            return jsonify({"models": [], "current": moltbot.cfg.ollama.model, "error": str(e)})
        
        current_model = moltbot.cfg.ollama.model if moltbot.cfg.llm.provider == "ollama" else (moltbot.cfg.clawdbot.agent_id or "lucy")
        
        return jsonify({
            "models": models_data, 
            "current": current_model, 
            "provider": moltbot.cfg.llm.provider
        })

    @app.route("/api/chat", methods=["POST"])
    def chat_http():
        """HTTP fallback for when Socket.IO is blocked or flaky."""
        payload = request.get_json(silent=True) or {}
        text = (payload.get("message") or "").strip()
        if not text:
            return jsonify({"ok": False, "error": "empty message"}), 400

        session_user = (payload.get("session_user") or "").strip() or "lucy-c:anonymous"
        result = moltbot.run_turn_from_text(text, session_user=session_user)

        history.append(
            HistoryItem(
                ts=time.time(),
                session_user=session_user,
                kind="text",
                llm_provider=moltbot.cfg.llm.provider,
                ollama_model=moltbot.cfg.ollama.model,
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

    @app.route("/api/budgets/<filename>")
    def download_budget(filename):
        root = Path(__file__).resolve().parents[2]
        budget_dir = root / "data" / "budgets"
        return send_from_directory(budget_dir, filename)

    @app.route("/api/stats")
    def system_stats():
        import psutil
        import platform
        
        cpu_usage = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        
        # Try to get GPU info
        gpu_info = "N/A"
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_info = f"{gpus[0].name} ({gpus[0].memoryUsed / gpus[0].memoryTotal * 100:.1f}%)"
        except Exception:
            pass
        
        return jsonify({
            "ok": True,
            "cpu": cpu_usage,
            "gpu": gpu_info,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "os": f"{platform.system()} {platform.release()}",
            "uptime": time.time() - moltbot._init_time if hasattr(moltbot, "_init_time") else 0
        })
    
    @app.route("/api/settings/virtual_display", methods=["GET"])
    def get_virtual_display_status():
        """Get current virtual display status."""
        enabled = os.environ.get("LUCY_VIRTUAL_DISPLAY") == "1"
        running = moltbot.virtual_display and moltbot.virtual_display.is_running() if hasattr(moltbot, 'virtual_display') else False
        display_num = moltbot.virtual_display.display if hasattr(moltbot, 'virtual_display') and moltbot.virtual_display else None
        
        return jsonify({
            "enabled": enabled,
            "running": running,
            "display": display_num
        })
    
    @app.route("/api/settings/virtual_display", methods=["POST"])
    def toggle_virtual_display():
        """Toggle virtual display on/off."""
        data = request.get_json()
        enabled = data.get("enabled", False)
        
        try:
            if enabled:
                os.environ["LUCY_VIRTUAL_DISPLAY"] = "1"
                
                # Initialize or start virtual display
                if not hasattr(moltbot, 'virtual_display') or not moltbot.virtual_display:
                    from lucy_c.services.virtual_display import VirtualDisplay
                    moltbot.virtual_display = VirtualDisplay()
                
                if not moltbot.virtual_display.is_running():
                    success = moltbot.virtual_display.start()
                    status = "active" if success else "failed"
                else:
                    status = "active"
            else:
                os.environ["LUCY_VIRTUAL_DISPLAY"] = "0"
                
                if hasattr(moltbot, 'virtual_display') and moltbot.virtual_display:
                    if moltbot.virtual_display.is_running():
                        moltbot.virtual_display.stop()
                status = "inactive"
            
            return jsonify({
                "success": True,
                "display_mode": "virtual" if enabled else "physical",
                "status": status
            })
            
        except Exception as e:
            log.error(f"Failed to toggle virtual display: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @socketio.on("connect")
    def on_connect():
        emit("status", {"message": "Connected", "type": "success"})

    @socketio.on("update_config")
    def on_update_config(data):
        try:
            data = data or {}
            from lucy_c.pipeline import LOCAL_ONLY
            
            provider = data.get("llm_provider") or moltbot.cfg.llm.provider
            if LOCAL_ONLY and provider != "ollama":
                log.warning("Ignoring request to switch to cloud provider '%s' (LOCAL_ONLY=1)", provider)
                provider = "ollama"
                
            model = data.get("ollama_model") or moltbot.cfg.ollama.model
            
            if provider != moltbot.cfg.llm.provider or model != moltbot.cfg.ollama.model:
                session_user = data.get("session_user") or "lucy-c:anonymous"
                moltbot.switch_brain(model, provider=provider, session_user=session_user)
                log.info("BRAIN EXCHANGE: %s (%s) -> %s (%s) for %s", 
                         moltbot.cfg.llm.provider, moltbot.cfg.ollama.model, provider, model, session_user)
                emit("status", {"message": f"Brain exchanged: {model} ({provider})", "type": "success"})
            else:
                emit("status", {"message": "No brain change needed", "type": "info"})
        except Exception as e:
            log.exception("update_config failed")
            emit("error", {"message": f"Failed to update brain: {e}"})

    @socketio.on("chat_message")
    def on_chat_message(data):
        try:
            # ... rest of the function ...
            text = (data or {}).get("message", "")
            text = (text or "").strip()
            
            # Input validation
            if not text:
                emit("status", {"message": "Por favor, escribí un mensaje", "type": "warning"})
                emit("status", {"message": "Ready", "type": "success"})
                return
            
            MAX_INPUT_LENGTH = 2000
            if len(text) > MAX_INPUT_LENGTH:
                emit("status", {
                    "message": f"Mensaje muy largo ({len(text)} chars). Máximo: {MAX_INPUT_LENGTH}",
                    "type": "warning"
                })
                emit("status", {"message": "Ready", "type": "success"})
                return

            emit("message", {"type": "user", "content": text})
            emit("status", {"message": "Thinking...", "type": "info"})
            emit("moltbot_log", {"message": f"🧠 Cerebro: Procesando con {moltbot.cfg.ollama.model}", "type": "brain"})

            session_user = (data or {}).get("session_user")
            result = moltbot.run_turn_from_text(text, session_user=session_user)
            emit("moltbot_log", {"message": f"✅ Respuesta generada ({len(result.reply)} caracteres)", "type": "success"})

            emit("message", {"type": "assistant", "content": result.reply})

            session_user = session_user or "lucy-c:anonymous"
            history.append(
                HistoryItem(
                    ts=time.time(),
                    session_user=session_user,
                    kind="text",
                    llm_provider=moltbot.cfg.llm.provider,
                    ollama_model=moltbot.cfg.ollama.model,
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
            if raw is None or (isinstance(raw, (bytes, list)) and len(raw) == 0):
                log.warning("Received empty audio blob from frontend")
                emit("status", {"message": "(Audio vacío ignorado)", "type": "warning"})
                emit("status", {"message": "Ready", "type": "success"})
                return
            
            raw_bytes = bytes(raw) if isinstance(raw, list) else raw
            
            if len(raw_bytes) < 100: # Too small for a valid wav/pcm usually
                log.warning("Received suspiciously small audio blob (%d bytes)", len(raw_bytes))
                emit("status", {"message": "(Audio muy corto ignorado)", "type": "warning"})
                emit("status", {"message": "Ready", "type": "success"})
                return

            emit("status", {"message": "Decoding...", "type": "info"})
            decoded = decode_audio_bytes_to_f32_mono(raw_bytes, target_sr=moltbot.cfg.audio.sample_rate)

            emit("status", {"message": "Transcribing...", "type": "info"})
            session_user = (data or {}).get("session_user") or "lucy-c:anonymous"
            handsfree = bool((data or {}).get("handsfree"))
            result = moltbot.run_turn_from_audio(decoded.audio, session_user=session_user)

            # In hands-free mode, ignore empty transcripts to prevent loops.
            # (Allow 1-word utterances like "hola".)
            if handsfree:
                words = [w for w in (result.transcript or "").strip().split() if w]
                if len(words) == 0:
                    emit("status", {"message": "(Ignorado: vacío)", "type": "info"})
                    emit("status", {"message": "Ready", "type": "success"})
                    return

            if result.transcript:
                emit("message", {"type": "user", "content": result.transcript})

            emit("message", {"type": "assistant", "content": result.reply})

            history.append(
                HistoryItem(
                    ts=time.time(),
                    session_user=session_user,
                    kind="voice",
                    llm_provider=moltbot.cfg.llm.provider,
                    ollama_model=moltbot.cfg.ollama.model,
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

    return app, socketio, moltbot


def main():
    logging.basicConfig(level=logging.INFO)
    app, socketio, _moltbot = create_app()
    port = int(os.environ.get("PORT", "5050"))

    # eventlet server
    socketio.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
