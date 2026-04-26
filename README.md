# Project Jarvis

Project Jarvis is a modular, realtime, voice-enabled AI assistant with a Python backend and an Electron + React desktop GUI.

## Repos inside this repository

- `jarvis-backend` — Python async AI engine for audio, STT/TTS, LLM streaming, memory, tools, actions, browser/system control, and safety confirmation.
- `jarvis-frontend` — Electron + React desktop client with Jarvis-style animated GUI, chat, waveform, browser mic, browser speech output, and action confirmation UI.

## Run backend

```bash
cd jarvis-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NVIDIA_API_KEY="your-nvidia-api-key"
PYTHONPATH=src python -m jarvis_backend --config config.yaml
```

## Run desktop app

```bash
cd jarvis-frontend
npm install
npm run start
```

This launches a separate Electron desktop application window, not just a website.

## Documentation

- `SETUP_GUIDE.md`
- `DELIVERY_REPORT.md`
- `jarvis-backend/README.md`
- `jarvis-frontend/README.md`
