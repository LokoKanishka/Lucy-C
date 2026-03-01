# Browser Setup for Lucy-C Audio

Lucy-C requires microphone and speaker access through your web browser. This guide helps you configure browser permissions correctly.

## ✅ Prerequisites

Before configuring the browser, verify that your system audio works:

```bash
# Run system-level audio test
./test_audio_system.sh

# Run Python-level audio test
source .venv/bin/activate
python3 test_audio.py
```

Both tests should pass before proceeding.

## 🌐 Browser Configuration

### Chrome / Chromium / Edge

1. Navigate to `http://localhost:5000`
2. Click the **lock icon** or **i icon** in the address bar (left of the URL)
3. Find **Microphone** in the permissions list
4. Change from "Ask" or "Block" to **"Allow"**
5. Reload the page (F5)
6. Click anywhere on the page to activate audio context
7. The microphone icon should now be active

### Firefox

1. Navigate to `http://localhost:5000`
2. Click the **lock icon** in the address bar
3. Click **Connection** > **More information**
4. Go to **Permissions** tab
5. Find **Use the Microphone**
6. Uncheck "Use default" and select **"Allow"**
7. Close the dialog and reload the page (F5)
8. Click anywhere on the page to activate audio

## 🔊 Audio Autoplay

Browsers block autoplay audio by default. To enable Lucy's voice:

1. After loading the page, **click anywhere** on the interface
2. This user interaction allows the browser to play audio
3. Lucy's voice should now work automatically

## 🐛 Troubleshooting

### No microphone icon visible

- Check browser console (F12) for errors
- Verify Lucy-C server is running: `python3 lucy_c/web/app.py`
- Try a different browser

### Microphone not capturing

- Verify system audio works: `./test_audio_system.sh`
- Check browser permissions again
- Try revoking and re-granting permission

### No voice output

- Click on the page to activate audio context
- Check browser console for autoplay blocks
- Verify speaker volume is not muted
- Run: `python3 test_audio.py` to verify Python TTS works

## 📝 Notes

- Permissions are **per-origin**, so `localhost:5000` needs separate permission from `127.0.0.1:5000`
- Use **https** in production for better browser compatibility
- Some browsers require user interaction before allowing audio
