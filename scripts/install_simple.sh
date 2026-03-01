#!/bin/bash
# Simplified installation script for Lucy-C with Python 3.10

set -e

echo "🔧 Installing Lucy-C dependencies (Python 3.10)"
echo "================================================"

# Activate virtual environment
source .venv/bin/activate

echo ""
echo "📦 Step 1/5: Installing core dependencies..."
pip install --no-deps \
    flask flask-socketio \
    pyyaml \
    numpy soundfile \
    requests

echo ""
echo "📦 Step 2/5: Installing audio/processing..."
pip install \
    pyautogui python-xlib \
    faster-whisper \
    httpx python-multipart eventlet

echo ""
echo "📦 Step 3/5: Installing RAG/Vector DB (simplified)..."
pip install \
    chromadb==0.4.24 \
    sentence-transformers==2.2.0 \
    --no-deps

# Install chromadb dependencies manually
pip install \
    onnxruntime pydantic requests tqdm \
    posthog bcrypt typer pypika overrides

echo ""
echo "📦 Step 4/5: Installing web/NLP tools..."
pip install \
    trafilatura beautifulsoup4 lxml \
    pytesseract opencv-python python-Levenshtein

echo ""
echo "📦 Step 5/5: Installing Coqui TTS..."
pip install TTS --no-deps

# Install TTS dependencies
pip install \
    librosa inflect anyascii \
    cython aiohttp

echo ""
echo "✅ Base installation complete!"
echo ""
echo "Next step: Run ./scripts/install_heavy.sh to download XTTS models"
