#!/bin/bash
# Start Lucy-C with all configurations

cd /home/lucy-ubuntu/Lucy-C

echo "🚀 Starting Lucy-C..."
echo ""

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export PYTHONPATH=/home/lucy-ubuntu/Lucy-C
export LUCY_LOCAL_ONLY=1

# Optional: Enable virtual display (set to 0 if you don't need it)
export LUCY_VIRTUAL_DISPLAY=0

# Optional: Use XTTS (set to mimic3 if XTTS has issues)
# export LUCY_TTS_PROVIDER=xtts
export LUCY_TTS_PROVIDER=mimic3

echo "✅ Environment configured"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   TTS Provider: $LUCY_TTS_PROVIDER"
echo "   Virtual Display: $LUCY_VIRTUAL_DISPLAY"
echo ""

echo "🌐 Starting Flask server..."
echo "   Access Lucy at: http://localhost:5050"
echo ""
echo "📝 Logs will appear below..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the application
python3 lucy_c/web/app.py
