import type { Confirmation, JarvisEvent } from './types';

const API_URL = import.meta.env.VITE_JARVIS_API_URL ?? '';
const WS_URL =
  import.meta.env.VITE_JARVIS_WS_URL ??
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`;

export function connectEvents(onEvent: (event: JarvisEvent) => void, onStatus: (online: boolean) => void) {
  let stopped = false;
  let socket: WebSocket | undefined;

  const connect = () => {
    socket = new WebSocket(WS_URL);
    socket.onopen = () => onStatus(true);
    socket.onclose = () => {
      onStatus(false);
      if (!stopped) window.setTimeout(connect, 1200);
    };
    socket.onerror = () => onStatus(false);
    socket.onmessage = (message) => onEvent(JSON.parse(message.data) as JarvisEvent);
  };

  connect();
  return () => {
    stopped = true;
    socket?.close();
  };
}

export async function sendText(text: string, speak = true) {
  const response = await fetch(`${API_URL}/api/input`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, speak })
  });
  if (!response.ok) throw new Error(await response.text());
  return (await response.json()) as { status: string; reply: string };
}

export async function confirmAction(confirmation: Confirmation, approved: boolean) {
  await fetch(`${API_URL}/api/action/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action_id: confirmation.action.id, approved })
  });
}

export async function startVoice() {
  await fetch(`${API_URL}/api/voice/start`, { method: 'POST' });
}

export async function stopVoice() {
  await fetch(`${API_URL}/api/voice/stop`, { method: 'POST' });
}

export async function transcribeVoice(blob: Blob) {
  const form = new FormData();
  form.append('file', blob, 'speech.wav');
  const response = await fetch(`${API_URL}/api/voice/transcribe`, {
    method: 'POST',
    body: form
  });
  if (!response.ok) throw new Error(await response.text());
  return (await response.json()) as { status: string; text: string; reply: string };
}

export async function interrupt() {
  await fetch(`${API_URL}/api/interrupt`, { method: 'POST' });
}
