# Project Jarvis

Project Jarvis is a modular, real-time, voice-enabled AI assistant with a Python AI engine and an Electron + React desktop HUD. It is designed to chat, listen, speak, remember conversation context, and execute browser/system actions only after explicit user confirmation.

## What is included

```text
JARVIS/
├── jarvis-backend/      # FastAPI + asyncio AI/action engine
├── jarvis-frontend/     # Electron + React + TypeScript desktop GUI
├── SETUP_GUIDE.md       # Detailed local setup guide
└── DELIVERY_REPORT.md   # Implementation summary and improvement roadmap
```

## Core capabilities

- **Desktop app GUI**: `npm run start` launches a separate Electron app window, not just a website.
- **Local backend service**: the Electron app talks to `jarvis-backend` over localhost REST/WebSocket; this is the desktop-app architecture, not a hosted website.
- **NVIDIA LLM by default**: uses `NVIDIA_API_KEY` and the NVIDIA OpenAI-compatible endpoint.
- **Provider-ready LLM layer**: config includes NVIDIA, OpenAI, and Gemini settings so the provider can be switched later.
- **Voice layer**: Faster-Whisper remains the local STT engine; VoxCPM2 is the default local TTS engine for expressive voice output.
- **Configurable Jarvis voices**: default thick female contralto profile plus selectable thick male baritone profile.
- **Browser microphone path**: the GUI can record browser mic audio and send it to backend transcription.
- **Browser speech fallback**: the UI can speak replies with browser speech synthesis when local TTS assets are unavailable.
- **Conversation memory**: SQLite-backed chat history.
- **Confirmed actions**: app open/close/focus, website opens, Google search, YouTube controls/search, WhatsApp prep/send, and allowlisted system commands.
- **Safety gate**: actions are parsed as structured intents and require user approval before execution.
- **Chrome and Edge support**: browser actions use remote debugging for Chrome or Microsoft Edge and fall back to Chrome DevTools Protocol when Selenium/ChromeDriver is mismatched.

## Architecture

```text
Electron/React GUI
  ├─ Chat composer and HUD state display
  ├─ Browser mic capture and browser speech output
  ├─ WebSocket events for state/action confirmations
  └─ REST calls for direct chat/voice replies

FastAPI backend
  ├─ JarvisAgent orchestration
  ├─ NVIDIA/OpenAI/Gemini-compatible LLM client config
  ├─ ActionParser for structured action extraction
  ├─ ActionManager safety confirmation layer
  ├─ BrowserActionExecutor for Chrome/Edge CDP/Selenium actions
  ├─ SystemActionExecutor for allowlisted OS commands/apps
  ├─ Faster-Whisper STT pipeline
  ├─ VoxCPM2 TTS voice-design pipeline
  ├─ Piper/Coqui fallback TTS integration points
  └─ SQLite memory store
```

## Quick start

### 1. Backend

```bash
cd jarvis-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NVIDIA_API_KEY="your-nvidia-api-key"
PYTHONPATH=src python -m jarvis_backend --config config.yaml
```

Backend default: `http://127.0.0.1:8765`

Health check:

```bash
curl http://127.0.0.1:8765/health
```

### 2. Browser automation setup

Jarvis controls your existing browser through remote debugging.

Chrome:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/jarvis-chrome-profile"
```

Microsoft Edge:

```bash
microsoft-edge --remote-debugging-port=9223 --user-data-dir="$HOME/jarvis-edge-profile"
```

The backend config tries both by default:

```yaml
actions:
  browser_debugger_address: "127.0.0.1:9222"
  edge_debugger_address: "127.0.0.1:9223"
  browser_debugger_addresses:
    - "127.0.0.1:9222"
    - "127.0.0.1:9223"
```

### 3. Desktop app

```bash
cd jarvis-frontend
npm install
npm run start
```

This starts Vite and then opens the Electron desktop app.

## Configuration

Main config file: `jarvis-backend/config.yaml`

Important values:

- `llm.provider`: `nvidia` by default. Can be changed to `openai` or `gemini` after adding the matching API key env var.
- `llm.api_key_env`: `NVIDIA_API_KEY`
- `stt.engine`: `faster_whisper`. VoxCPM is a TTS/voice generation model, so STT stays on Faster-Whisper unless another ASR model is added.
- `tts.engine`: `voxcpm` by default.
- `tts.voice_profile`: `female_thick` by default; set to `male_thick` for a deeper male voice.
- `actions.require_confirmation`: `true`
- `actions.browser_debugger_addresses`: ordered Chrome/Edge remote debugging endpoints.
- `actions.linux_app_allowlist`: allowed apps Jarvis can open, such as Chrome, Edge, VS Code, and Terminal.

## VoxCPM voice setup

VoxCPM2 is used for expressive TTS voice design:

```yaml
tts:
  engine: "voxcpm"
  voxcpm_model: "openbmb/VoxCPM2"
  voice_profile: "female_thick"
  voice_profiles:
    female_thick: "A confident adult woman with a deeper, thicker, warm contralto voice, calm Jarvis assistant tone, clear articulation, cinematic presence"
    male_thick: "A confident adult man with a deep, thick, warm baritone voice, calm Jarvis assistant tone, clear articulation, cinematic presence"
```

Switch to male:

```yaml
tts:
  voice_profile: "male_thick"
```

VoxCPM is not an STT/ASR engine in the official docs; Jarvis keeps Faster-Whisper for speech-to-text input and uses VoxCPM for speech output.

## Testing and validation

Backend:

```bash
cd jarvis-backend
python -m compileall src tests
PYTHONPATH=src .venv/bin/python -m pytest tests/test_action_parser.py
```

Frontend:

```bash
cd jarvis-frontend
npm run build
```

Manual browser action test:

1. Start Chrome or Edge with remote debugging.
2. Start backend and desktop app.
3. Ask Jarvis: `open YouTube in my browser`.
4. Verify the Safety Gate appears.
5. Click `Approve`.
6. Verify YouTube opens in Chrome or Edge.

Manual YouTube search test:

1. Ask Jarvis: `search YouTube for Interstellar theme`.
2. Verify the Safety Gate appears.
3. Click `Approve`.
4. Verify Chrome or Edge opens `youtube.com/results?search_query=Interstellar+theme`.

Manual WhatsApp unknown-number test:

1. Log into WhatsApp Web in the same Chrome or Edge profile started with remote debugging.
2. Ask Jarvis: `message +15551234567 on WhatsApp saying hi`.
3. Verify the Safety Gate says it will prepare a WhatsApp message to that phone number.
4. Click `Approve`.
5. Jarvis opens `wa.me/<phone>?text=hi` in the logged-in browser session.
6. Review WhatsApp, then press send only if the message and recipient are correct.

Chrome does not need to be updated for basic open/search/WhatsApp-link actions because Jarvis falls back to direct Chrome/Edge DevTools Protocol tab creation. If you want Selenium keyboard/mouse automation inside a page, keep ChromeDriver compatible with the installed Chrome/Edge version.

## Troubleshooting

### Chat says the backend is offline

- Confirm backend is running on `127.0.0.1:8765`.
- Check `curl http://127.0.0.1:8765/health`.
- Restart the frontend after changing backend URLs.

### Browser action stays stuck on Executing

- Make sure Chrome or Edge is running with remote debugging.
- Chrome should expose `http://127.0.0.1:9222/json/version`.
- Edge should expose `http://127.0.0.1:9223/json/version`.
- Jarvis now falls back to direct CDP open-tab calls if Selenium ChromeDriver is mismatched.

### NVIDIA responses fail

- Ensure `NVIDIA_API_KEY` is exported in the backend shell.
- Keep secrets in environment variables only. Do not commit keys.

### Voice transcription fails

- Confirm backend dependencies installed successfully.
- Browser mic requires browser permission.
- Local Faster-Whisper model download may take time on first run.

## Safety model

Jarvis does not directly execute actions from text. The LLM proposes structured actions, the backend parses them, the GUI shows a Safety Gate, and the backend executes only after approval.

Examples:

- `open YouTube in my browser` → `open_website` → approval required.
- `search Google for latest AI news` → `google_search` → approval required.
- `message Alex on WhatsApp` → `whatsapp_message` contact flow → approval required before sending.
- `message +15551234567 on WhatsApp saying hi` → `wa.me` phone-number flow → approval required before opening the prepared message.

## Documentation

- `SETUP_GUIDE.md`
- `DELIVERY_REPORT.md`
- `jarvis-backend/README.md`
- `jarvis-frontend/README.md`
