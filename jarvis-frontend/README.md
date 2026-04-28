# Project Jarvis Frontend

Electron + React desktop HUD for Project Jarvis.

## What it does

- Launches as a standalone Electron desktop app.
- Shows Jarvis HUD state, chat, waveform, and backend connection status.
- Records browser microphone audio for backend transcription.
- Speaks replies with browser speech synthesis when local playback is unavailable.
- Shows Safety Gate cards for action confirmations.
- Communicates with backend through REST and WebSocket.

## Structure

```text
jarvis-frontend/
├── electron/
│   ├── main.cjs       # Electron main process
│   └── preload.cjs    # Safe preload bridge
├── src/
│   ├── assets/        # Jarvis HUD image
│   ├── lib/           # API client and shared types
│   ├── styles/        # HUD/global CSS
│   ├── App.tsx        # Main app UI
│   └── main.tsx       # React entrypoint
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Run

```bash
npm install
npm run start
```

`npm run start` runs Vite and opens the Electron desktop window.

## Backend connection

Default backend:

```text
http://127.0.0.1:8765
ws://127.0.0.1:8765/ws
```

Override:

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

- `idle`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `awaiting_confirmation`
- `executing_action`
- `error`
