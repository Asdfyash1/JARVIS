# Project Jarvis Setup Guide

Project Jarvis has two main parts:

- `jarvis-backend` — local Python AI/action engine.
- `jarvis-frontend` — Electron + React desktop HUD.

## Prerequisites

- Python 3.10+
- Node.js 20+
- Chrome or Edge for browser automation
- NVIDIA API key for default LLM provider
- Optional GPU/CUDA for faster local STT/TTS

## 1. Backend setup

```bash
cd jarvis-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NVIDIA_API_KEY="your-nvidia-api-key"
PYTHONPATH=src python -m jarvis_backend --config config.yaml
```

Health check:

```bash
curl http://127.0.0.1:8765/health
```

## 2. Local STT

Faster-Whisper is the main speech-to-text engine:

```yaml
stt:
  engine: "faster_whisper"
  model_size: "small.en"
  device: "auto"
  compute_type: "auto"
```

Recommendations:

- Low-latency CPU: `base.en` or `small.en`.
- Better GPU accuracy: `medium.en` or `large-v3`.
- Use `beam_size: 1` for faster turn handling.

## 3. Local TTS with VoxCPM2

VoxCPM2 is the default text-to-speech voice engine:

```yaml
tts:
  engine: "voxcpm"
  voxcpm_model: "openbmb/VoxCPM2"
  voice_profile: "female_thick"
```

Switch voice profile:

```yaml
tts:
  voice_profile: "male_thick"
```

VoxCPM is a voice-generation/TTS project in its official documentation, so Jarvis keeps Faster-Whisper for STT input.

## 4. Browser automation setup

Jarvis controls an existing browser profile through remote debugging.

Chrome:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/jarvis-chrome-profile"
```

Edge:

```bash
microsoft-edge --remote-debugging-port=9223 --user-data-dir="$HOME/jarvis-edge-profile"
```

Config:

```yaml
actions:
  browser_debugger_address: "127.0.0.1:9222"
  edge_debugger_address: "127.0.0.1:9223"
```

## 5. WhatsApp setup

1. Start Chrome/Edge with remote debugging.
2. Open `https://web.whatsapp.com`.
3. Log in with your phone.
4. Ask Jarvis to message a contact, phone number, or currently open chat.
5. Approve the Safety Gate before Jarvis sends or prepares the message.

If multiple WhatsApp matches appear for a name, Jarvis asks which one to use.

## 6. Frontend setup

```bash
cd jarvis-frontend
npm install
npm run start
```

This launches the Electron desktop app.

## 7. Validation

Backend:

```bash
cd jarvis-backend
source .venv/bin/activate
PYTHONPATH=src python -m compileall src tests
PYTHONPATH=src python -m pytest
```

Frontend:

```bash
cd jarvis-frontend
npm run build
```

## 8. Safety

Jarvis never executes arbitrary LLM text. It uses structured actions, Pydantic validation, GUI confirmation, and allowlisted executors.
