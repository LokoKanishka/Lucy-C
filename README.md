# Lucy-C

Lucy-C is a local, open-source voice assistant stack.

Goal: clone this repo on another machine and get a **push-to-talk** web UI where:
- you press and hold a button to talk
- Lucy transcribes your speech
- Lucy replies with text **and voice**

## Quick start

```bash
git clone https://github.com/LokoKanishka/Lucy-C.git
cd Lucy-C
./scripts/install.sh
./scripts/run_web_ui.sh
# open the URL it prints (default http://127.0.0.1:5000)
```

## System requirements

- Linux (tested on Ubuntu 24.04)
- `ffmpeg`
- `ollama` running locally (default: http://127.0.0.1:11434)
- `mimic3` CLI available for TTS (`pipx install mycroft-mimic3-tts` or via pip)

### GPU note (recommended)
If you have an NVIDIA GPU, set ASR to CUDA in `config/config.yaml`:

```yaml
asr:
  device: "cuda"
  compute_type: "float16"
```

## Notes

This project is intentionally self-contained: code + scripts live in this repo.
External tools (Ollama, ffmpeg, Mimic3 voices) are installed outside the repo,
but `scripts/install.sh` and `scripts/doctor.sh` help you validate the setup.
