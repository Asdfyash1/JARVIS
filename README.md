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
- **NVIDIA LLM by default**: uses `NVIDIA_API_KEY` and the NVIDIA OpenAI-compatible endpoint.
- **Provider-ready LLM layer**: config includes NVIDIA, OpenAI, and Gemini settings so the provider can be switched later.
- **Local-first speech**: Faster-Whisper STT and Piper/Coqui-style local TTS integration points.
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
  ├─ Piper/Coqui TTS integration points
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
- `actions.require_confirmation`: `true`
- `actions.browser_debugger_addresses`: ordered Chrome/Edge remote debugging endpoints.
- `actions.linux_app_allowlist`: allowed apps Jarvis can open, such as Chrome, Edge, VS Code, and Terminal.

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
- `message Alex on WhatsApp` → `whatsapp_message` → approval required before sending.

## Documentation

- `SETUP_GUIDE.md`
- `DELIVERY_REPORT.md`
- `jarvis-backend/README.md`
- `jarvis-frontend/README.md`
