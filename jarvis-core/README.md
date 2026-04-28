# Project Jarvis Core Engine

Async Python AI engine for Project Jarvis.

## What it does

- Serves REST + WebSocket APIs through FastAPI.
- Runs the Jarvis agent orchestration loop.
- Maintains SQLite conversation memory.
- Handles local speech-to-text with Faster-Whisper.
- Handles local speech output with VoxCPM2 by default.
- Supports Piper and Coqui fallback TTS adapters.
- Calls NVIDIA LLM by default, with OpenAI/Gemini provider-ready config.
- Parses structured action JSON.
- Requires confirmation before risky actions execute.
- Automates Chrome/Edge through remote debugging, Selenium, and CDP fallback.
- Supports app control, web page opens, Google search, YouTube search/control, WhatsApp messaging, and allowlisted commands.

## Structure

```text
jarvis-core/
├── config.yaml
├── requirements.txt
├── pyproject.toml
├── src/jarvis_backend/
│   ├── actions/      # Browser/system executors + confirmation manager
│   ├── audio/        # Mic, playback, VAD, voice pipeline
│   ├── llm/          # LLM client and action parser
│   ├── memory/       # SQLite memory
│   ├── server/       # FastAPI app
│   ├── state/        # Pydantic models/state store
│   ├── stt/          # Faster-Whisper STT
│   └── tts/          # VoxCPM/Piper/Coqui TTS
└── tests/
```

## Run

```bash
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

## Voice

STT:

```yaml
stt:
  engine: "faster_whisper"
  model_size: "small.en"
```

TTS:

```yaml
tts:
  engine: "voxcpm"
  voxcpm_model: "openbmb/VoxCPM2"
  voice_profile: "female_thick"
```

Set `voice_profile: "male_thick"` for the male voice.

## Browser setup

Chrome:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/jarvis-chrome-profile"
```

Edge:

```bash
microsoft-edge --remote-debugging-port=9223 --user-data-dir="$HOME/jarvis-edge-profile"
```

## WhatsApp behavior

Jarvis supports:

```json
{"action":"whatsapp_message","contact":"U Karthik","message":"hi"}
{"action":"whatsapp_message","phone_number":"+15551234567","message":"hi"}
{"action":"whatsapp_message","message":"hi"}
```

If multiple WhatsApp matches appear for a contact search, Jarvis asks the user which one to use instead of guessing.

## API

- `POST /api/input`
- `POST /api/voice/start`
- `POST /api/voice/stop`
- `POST /api/voice/transcribe`
- `POST /api/interrupt`
- `POST /api/action/confirm`
- `GET /health`
- `WS /ws`

## Test

```bash
PYTHONPATH=src python -m compileall src tests
PYTHONPATH=src python -m pytest
```
