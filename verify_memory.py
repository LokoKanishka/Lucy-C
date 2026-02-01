import logging
from lucy_c.pipeline import LucyPipeline
from lucy_c.config import LucyConfig
from lucy_c.history_store import HistoryStore, HistoryItem
import tempfile
from pathlib import Path

# Setup dummy config
cfg = LucyConfig()

with tempfile.TemporaryDirectory() as tmpdir:
    history = HistoryStore(tmpdir)
    pipeline = LucyPipeline(cfg, history=history)
    
    user = "test_user_123"
    
    # 1. Test empty history
    msgs = pipeline._get_chat_messages("Hola", session_user=user)
    print("Messages (empty history):")
    for m in msgs:
        print(f"  {m['role']}: {m['content'][:50]}...")
        
    # 2. Add some history
    history.append(HistoryItem(
        ts=1.0, session_user=user, kind="text", 
        llm_provider="ollama", ollama_model="llama3",
        user_text="Me llamo Diego", transcript="Me llamo Diego",
        reply="Hola Diego, un gusto."
    ))
    
    msgs = pipeline._get_chat_messages("Como me llamo?", session_user=user)
    print("\nMessages (with history):")
    for m in msgs:
        print(f"  {m['role']}: {m['content'][:50]}...")

    # Check order
    assert msgs[1]["content"] == "Me llamo Diego"
    assert msgs[2]["content"] == "Hola Diego, un gusto."
    assert msgs[3]["content"] == "Como me llamo?"
    print("\nVerification successful! Order and content are correct.")
