# Project Jarvis Backend

Production-oriented async Python backend for a real-time voice AI assistant.

## Implemented capabilities

- FastAPI WebSocket/REST server.
- Event-driven runtime with typed event bus.
- Continuous voice pipeline: microphone frames → VAD → Faster-Whisper STT → LLM → VoxCPM/Piper/Coqui TTS → audio playback.
- Local-first STT with Faster-Whisper as the primary speech engine.
- Local TTS with VoxCPM2 voice design by default, plus Piper and Coqui fallback options.
- NVIDIA API streaming chat completions for reasoning.
- Persistent SQLite conversation memory.
- Structured JSON action parsing.
- Mandatory confirmation gate before actions.
- System control executor with allowlisted apps/commands.
- Browser automation by attaching Selenium to an existing Chrome/Edge remote debugging session.
- WhatsApp Web message preparation flow that stops before sending.
- Interrupt support while the assistant is speaking or thinking.

## Quick start

```bash
cd jarvis-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NVIDIA_API_KEY="your-nvidia-api-key"
python -m jarvis_backend --config config.yaml
```

Health check:

```bash
curl http://127.0.0.1:8765/health
```

## Local STT: Faster-Whisper

Faster-Whisper is the main STT engine. It auto-tries CUDA first when `device: auto` and falls back to CPU int8 if CUDA initialization fails.

Recommended config:

```yaml
stt:
  engine: "faster_whisper"
  model_size: "small.en"
  device: "auto"
  compute_type: "auto"
```

For stronger accuracy, use `medium.en` or `large-v3`. For low-latency CPU, use `base.en` or `small.en`.

## Local TTS: VoxCPM2

VoxCPM2 is the default TTS engine. It supports voice design from a natural-language voice description.

```yaml
tts:
  engine: "voxcpm"
  voxcpm_model: "openbmb/VoxCPM2"
  voxcpm_cfg_value: 2.0
  voxcpm_inference_timesteps: 10
  voice_profile: "female_thick"
  voice_profiles:
    female_thick: "A confident adult woman with a deeper, thicker, warm contralto voice, calm Jarvis assistant tone, clear articulation, cinematic presence"
    male_thick: "A confident adult man with a deep, thick, warm baritone voice, calm Jarvis assistant tone, clear articulation, cinematic presence"
```

Set `voice_profile: "male_thick"` to switch to the deeper male Jarvis voice.

VoxCPM is a TTS/voice generation project, not a speech-to-text engine in the official docs. Jarvis therefore keeps Faster-Whisper for STT input and uses VoxCPM for TTS output.

## Local TTS fallback: Piper

Install Piper and download a voice:

```bash
mkdir -p voices
wget -O voices/en_US-lessac-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget -O voices/en_US-lessac-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

Set:

```yaml
tts:
  engine: "piper"
  piper_binary: "piper"
  voice_model: "./voices/en_US-lessac-medium.onnx"
```

## Browser debugging setup

Jarvis attaches to your existing browser session through remote debugging.

Linux:

Chrome:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/jarvis-chrome-profile"
```

Microsoft Edge:

```bash
microsoft-edge --remote-debugging-port=9223 --user-data-dir="$HOME/jarvis-edge-profile"
```

Windows:

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\jarvis-profile"
```

Then keep:

```yaml
actions:
  browser_debugger_address: "127.0.0.1:9222"
  edge_debugger_address: "127.0.0.1:9223"
  browser_debugger_addresses:
    - "127.0.0.1:9222"
    - "127.0.0.1:9223"
```

Website opens, Google searches, and YouTube search actions use Selenium when compatible and fall back to direct Chrome/Edge DevTools Protocol tab creation when ChromeDriver does not match the running browser.

## API

- `POST /api/input` — text input.
- `POST /api/voice/start` — start continuous microphone pipeline.
- `POST /api/voice/stop` — stop microphone pipeline.
- `POST /api/interrupt` — interrupt current speech/response.
- `POST /api/action/confirm` — approve or deny pending actions.
- `GET /health` — status.
- `WS /ws` — realtime events.

## Safety model

The LLM only proposes structured actions. The backend parses, validates, asks for user confirmation, and then executes using allowlisted executors.

Actions requiring confirmation include:

- Opening apps.
- Opening websites.
- Searches.
- Browser automation.
- WhatsApp message preparation.
- System commands.

## Run tests

```bash
python -m pytest
```
