from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path

# CRÍTICO: Parchear antes de cualquier importación de red
import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit

from lucy_c.audio_codec import decode_audio_bytes_to_f32_mono
from lucy_c.config import LucyConfig
from lucy_c.history_store import HistoryItem, HistoryStore, default_history_dir
from lucy_c.facts_store import FactsStore, default_facts_dir

# New Architecture Imports
from lucy_c.core.orchestrator import LucyOrchestrator
from lucy_c.core.cognitive import CognitiveEngine
from lucy_c.core.senses import SensorySystem
from lucy_c.core.actions import ActionController
from lucy_c.tool_router import ToolRouter

# Providers
from lucy_c.ollama_llm import OllamaLLM
from lucy_c.clawdbot_llm import ClawdbotLLM
from lucy_c.asr import FasterWhisperASR
from lucy_c.mimic3_tts import Mimic3TTS

log = logging.getLogger("LucyC.Web")

def create_app() -> tuple[Flask, SocketIO, LucyOrchestrator]:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "lucy-c-dev-secret")
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    socketio = SocketIO(app, cors_allowed_origins="*")

    # Status Callback for WebSocket feedback
    def status_callback(message: str, type: str = "info"):
        socketio.emit("status", {"message": message, "type": type})
        
        # Detect tool execution and emit structured event (Badge System)
        tool_badges = {
            "Mirando pantalla": ("screenshot", "sensor", "👁️"),
            "Haciendo clic": ("click", "actuator", "🖐️"),
            "Escribiendo": ("type", "actuator", "⌨️"),
            "Moviendo": ("move", "actuator", "🖱️"),
            "Leyendo archivo": ("read_file", "sensor", "📄"),
            "Escribiendo archivo": ("write_file", "actuator", "📝"),
            "Guardando en memoria": ("remember", "memory", "🧠"),
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

    # Configuration & Persistence
    root = Path(__file__).resolve().parents[2]
    cfg_path = os.environ.get("LUCY_C_CONFIG", str(root / "config" / "config.yaml"))
    
    # Load env vars first (dotenv)
    try:
        from dotenv import load_dotenv
        load_dotenv(root / ".env")
    except ImportError:
        pass

    cfg = LucyConfig.load(cfg_path)
    
    # Overrides from Env
    if os.environ.get("CLAWDBOT_GATEWAY_TOKEN"):
        cfg.clawdbot.token = os.environ.get("CLAWDBOT_GATEWAY_TOKEN")

    history = HistoryStore(default_history_dir())
    facts = FactsStore(default_facts_dir())

    # --- Dependency Injection Construction ---
    
    # 1. LLM Provider
    local_only = os.environ.get("LUCY_LOCAL_ONLY", "1") == "1"
    provider_name = cfg.llm.provider
    
    if local_only and provider_name not in ["ollama", "clawdbot"]:
        log.warning("LUCY_LOCAL_ONLY=1: Forcing provider to 'ollama'")
        provider_name = "ollama"
        cfg.llm.provider = "ollama"

    if provider_name == "clawdbot":
        llm = ClawdbotLLM(cfg.clawdbot)
    else:
        llm = OllamaLLM(cfg.ollama)
    
    # 2. Audio Components
    asr = FasterWhisperASR(cfg.asr)
    tts = Mimic3TTS(cfg.tts)
    senses = SensorySystem(asr=asr, tts=tts)
    
    # 3. Cognitive Engine
    brain = CognitiveEngine(llm=llm, history=history, facts=facts)
    
    # 4. Action Controller (Body)
    tool_router = ToolRouter()
    # Note: Actions need access to LLM for Vision tools, hence passing `llm`
    body = ActionController(cfg=cfg, tool_router=tool_router, llm_provider=llm)
    
    # 5. Orchestrator
    orchestrator = LucyOrchestrator(
        cfg=cfg,
        brain=brain,
        senses=senses,
        body=body,
        status_callback=status_callback
    )

    # API Routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/api/models")
    def models():
        try:
            # We try to use the LLM provider's list_models if available
            current_provider = cfg.llm.provider
            
            # If Ollama, we can get detailed info
            if isinstance(llm, OllamaLLM):
                detailed = llm.list_models_detailed()
                from dataclasses import asdict
                models_data = [asdict(m) for m in detailed]
            else:
                # Generic fallback
                models_list = llm.list_models()
                models_data = [{"name": m, "size_gb": 0, "family": "unknown"} for m in models_list]
            
            current_model = cfg.ollama.model if current_provider == "ollama" else (cfg.clawdbot.agent_id or "lucy")
            
            return jsonify({
                "models": models_data,
                "current": current_model,
                "provider": current_provider
            })
        except Exception as e:
            log.exception("Models API Error")
            return jsonify({"error": str(e)})

    @app.route("/api/chat", methods=["POST"])
    def chat_http():
        payload = request.get_json(silent=True) or {}
        text = (payload.get("message") or "").strip()
        session_user = (payload.get("session_user") or "").strip() or "lucy-c:anonymous"
        
        result = orchestrator.process_text_input(text, session_user=session_user)
        
        # Save to history (Orchestrator brain implies it, but we double save here or rely on brain?
        # CognitiveEngine uses history for *context building* but does it *write* to history?
        # NO. CognitiveEngine reads history. Writing happens here in the app layer or Orchestrator.
        # Let's check Orchestrator... it does NOT write to history store explicitly.
        # So we MUST write to history here.
        history.append(
            HistoryItem(
                ts=time.time(),
                session_user=session_user,
                kind="text",
                llm_provider=cfg.llm.provider,
                ollama_model=cfg.ollama.model,
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
                 "wav_base64": base64.b64encode(result.reply_wav).decode("ascii")
             }
        return jsonify(resp)

    @app.route("/api/history")
    def history_api():
        session_user = (request.args.get("session_user") or "").strip() or "lucy-c:anonymous"
        items = history.read(session_user=session_user, limit=200)
        return jsonify({"ok": True, "items": items})
        
    @app.route("/api/stats")
    def stats():
        import psutil
        import platform
        mem = psutil.virtual_memory()
        return jsonify({
            "ok": True,
            "cpu": psutil.cpu_percent(),
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "os": f"{platform.system()} {platform.release()}"
        })

    @app.route("/api/settings/virtual_display")
    def settings_display():
        return jsonify({"ok": True, "enabled": False})

    # SocketIO Events
    @socketio.on("connect")
    def on_connect():
        emit("status", {"message": "Connected (Core v2.0)", "type": "success"})

    @socketio.on("chat_message")
    def on_chat_message(data):
        text = (data or {}).get("message", "")
        session_user = (data or {}).get("session_user") or "lucy-c:anonymous"
        
        emit("message", {"type": "user", "content": text})
        emit("status", {"message": "Thinking...", "type": "info"})
        
        result = orchestrator.process_text_input(text, session_user=session_user)
        
        emit("message", {"type": "assistant", "content": result.reply})
        
        history.append(HistoryItem(
            ts=time.time(),
            session_user=session_user,
            kind="text",
            llm_provider=cfg.llm.provider,
            ollama_model=cfg.ollama.model,
            user_text=text,
            transcript=text,
            reply=result.reply
        ))
        
        if result.reply_wav:
            emit("audio", {
                "mime": "audio/wav", 
                "sample_rate": result.reply_sr, 
                "wav_base64": base64.b64encode(result.reply_wav).decode("ascii")
            })
        
        emit("status", {"message": "Ready", "type": "success"})

    @socketio.on("voice_input")
    def on_voice_input(data):
        raw = (data or {}).get("audio")
        if not raw: return
        
        raw_bytes = bytes(raw) if isinstance(raw, list) else raw
        decoded = decode_audio_bytes_to_f32_mono(raw_bytes, target_sr=cfg.audio.sample_rate)
        
        session_user = (data or {}).get("session_user") or "lucy-c:anonymous"
        
        result = orchestrator.process_audio_input(decoded.audio, session_user=session_user)
        
        if result.transcript:
            emit("message", {"type": "user", "content": result.transcript})
            
        emit("message", {"type": "assistant", "content": result.reply})
        
        history.append(HistoryItem(
            ts=time.time(),
            session_user=session_user,
            kind="voice",
            llm_provider=cfg.llm.provider,
            ollama_model=cfg.ollama.model,
            user_text="",
            transcript=result.transcript,
            reply=result.reply
        ))

        if result.reply_wav:
             emit("audio", {
                 "mime": "audio/wav", 
                 "sample_rate": result.reply_sr, 
                 "wav_base64": base64.b64encode(result.reply_wav).decode("ascii")
             })
             
        emit("status", {"message": "Ready", "type": "success"})

    return app, socketio, orchestrator

def main():
    logging.basicConfig(level=logging.INFO)
    app, socketio, _ = create_app()
    port = int(os.environ.get("PORT", "5050"))
    socketio.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
