#!/bin/bash
# Install heavy models for Lucy-C
# This downloads large models (~2GB+) for neural TTS

set -e

echo "════════════════════════════════════════════════════════════"
echo "   Lucy-C Heavy Models Installation"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python first."
    exit 1
fi

# Create model cache directory
echo "📁 Creating model cache directory..."
mkdir -p ~/.local/share/tts
mkdir -p data/voices

# Check if TTS is installed
echo ""
echo "🔍 Checking for Coqui TTS..."
if ! python3 -c "import TTS" 2>/dev/null; then
    echo "⚠️  Coqui TTS not installed."
    echo "   Installing now (this may take a while)..."
    pip install --break-system-packages TTS torch torchaudio
fi

# Download XTTS model
echo ""
echo "📥 Downloading XTTS v2 model (~2GB)..."
echo "   This will be cached for future use."
echo ""

python3 << 'EOF'
try:
    from TTS.api import TTS
    import torch
    
    print("Loading XTTS v2 model...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    
    if torch.cuda.is_available():
        print(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
        print("   XTTS will use GPU acceleration!")
    else:
        print("⚠️  No GPU detected. XTTS will use CPU (slower).")
    
    print("✅ XTTS model ready!")
    
except Exception as e:
    print(f"❌ Failed to download XTTS: {e}")
    exit(1)
EOF

# Create default reference voice if needed
if [ ! -f "data/voices/lucy_ref.wav" ]; then
    echo ""
    echo "📢 Creating default voice reference..."
    echo "   (You can replace data/voices/lucy_ref.wav with your own 6-10s audio)"
    
    python3 << 'EOF'
try:
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    # Generate a reference sample
    tts.tts_to_file(
        text="Hola, soy Lucy, tu asistente virtual.",
        file_path="data/voices/lucy_ref.wav",
        language="es"
    )
    print("✅ Default voice reference created")
except Exception as e:
    print(f"⚠️  Could not create default reference: {e}")
EOF
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Installation complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "To use XTTS neural voice, set in your config.yaml:"
echo ""
echo "  tts:"
echo "    provider: \"xtts\""
echo "    use_gpu: true"
echo ""
echo "Or set environment variable:"
echo "  export LUCY_TTS_PROVIDER=xtts"
echo ""
