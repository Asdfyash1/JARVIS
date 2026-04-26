# Project Jarvis Frontend

Electron + React GUI for Project Jarvis with realtime WebSocket updates, animated state transitions, waveform visualization, chat, and action confirmation UX.

## Implemented capabilities

- Electron desktop shell.
- React + TypeScript UI.
- Futuristic dark Jarvis-style visual system.
- Animated arc reactor core with state-specific motion.
- Audio waveform visualizer driven by backend audio-level events.
- Live chat with streaming AI response deltas.
- Backend connection status.
- Continuous voice start/stop controls.
- Interrupt button.
- Safety confirmation card for tool/action requests.

## Quick start

```bash
cd jarvis-frontend
npm install
npm run start
```

The frontend expects the backend at:

```text
http://127.0.0.1:8765
ws://127.0.0.1:8765/ws
```

Override with:

```bash
VITE_JARVIS_API_URL=http://127.0.0.1:8765 \
VITE_JARVIS_WS_URL=ws://127.0.0.1:8765/ws \
npm run start
```

## Build

```bash
npm run build
```

## UI states

The GUI renders backend `system_state` events:

- `idle`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `awaiting_confirmation`
- `executing_action`
- `error`
