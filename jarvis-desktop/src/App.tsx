import { AnimatePresence, motion } from 'framer-motion';
import { Mic, Power, Radio, Send, ShieldCheck, Square, Zap } from 'lucide-react';
import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { confirmAction, connectEvents, interrupt, sendText, startVoice, stopVoice, transcribeVoice } from './lib/api';
import type { ChatMessage, Confirmation, JarvisEvent, JarvisState } from './lib/types';
import hudImage from './assets/jarvis-hud.png';
import './styles/app.css';

const stateCopy: Record<JarvisState, string> = {
  idle: 'Core Online',
  listening: 'Listening',
  transcribing: 'Transcribing',
  thinking: 'Thinking',
  speaking: 'Speaking',
  awaiting_confirmation: 'Awaiting Confirmation',
  executing_action: 'Executing',
  error: 'Fault Detected'
};

function uid() {
  return crypto.randomUUID();
}

export default function App() {
  const [online, setOnline] = useState(false);
  const [state, setState] = useState<JarvisState>('idle');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: uid(),
      role: 'assistant',
      content: 'Project Jarvis online. VoxCPM2 voice core is armed.'
    }
  ]);
  const [input, setInput] = useState('');
  const [audioLevel, setAudioLevel] = useState(0.18);
  const [confirmation, setConfirmation] = useState<Confirmation | null>(null);
  const [recording, setRecording] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingChunksRef = useRef<Float32Array[]>([]);
  const recordingSampleRateRef = useRef(44100);

  useEffect(() => {
    window.scrollTo({ left: 0, top: 0 });
    return connectEvents(handleEvent, setOnline);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const statusTone = useMemo(() => {
    if (!online) return 'offline';
    if (state === 'error') return 'error';
    if (state === 'awaiting_confirmation') return 'confirm';
    return 'online';
  }, [online, state]);

  function handleEvent(event: JarvisEvent) {
    if (event.type === 'system_state') {
      setState((event.payload.state as JarvisState) ?? 'idle');
    }
    if (event.type === 'audio_level') {
      setAudioLevel(Math.min(1, Math.max(0.05, Number(event.payload.level) * 20)));
    }
    if (event.type === 'user_input' || event.type === 'transcription') {
      const text = String(event.payload.text ?? '');
      if (text) setMessages((items) => [...items, { id: uid(), role: 'user', content: text }]);
    }
    if (event.type === 'ai_response_delta') {
      const delta = String(event.payload.delta ?? '');
      setMessages((items) => {
        const last = items.at(-1);
        if (last?.role === 'assistant' && last.streaming) {
          return items.map((item, index) =>
            index === items.length - 1 ? { ...item, content: item.content + delta } : item
          );
        }
        return [...items, { id: uid(), role: 'assistant', content: delta, streaming: true }];
      });
    }
    if (event.type === 'ai_response') {
      const text = String(event.payload.text ?? '');
      if (text) speakInBrowser(text);
      setMessages((items) => {
        const last = items.at(-1);
        if (last?.role === 'assistant' && last.streaming) {
          return items.map((item, index) =>
            index === items.length - 1 ? { ...item, content: text || item.content, streaming: false } : item
          );
        }
        return text ? [...items, { id: uid(), role: 'assistant', content: text }] : items;
      });
    }
    if (event.type === 'action_confirmation') {
      setConfirmation(event.payload as unknown as Confirmation);
    }
    if (event.type === 'action_result') {
      setConfirmation(null);
      setMessages((items) => [
        ...items,
        {
          id: uid(),
          role: 'system',
          content: `${event.payload.ok ? 'Action complete' : 'Action blocked'}: ${event.payload.message ?? ''}`
        }
      ]);
    }
    if (event.type === 'error') {
      setMessages((items) => [
        ...items,
        { id: uid(), role: 'system', content: `Error: ${String(event.payload.message ?? 'Unknown error')}` }
      ]);
    }
  }

  function speakInBrowser(text: string) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.96;
    utterance.pitch = 0.88;
    utterance.volume = 1;
    const voice =
      window.speechSynthesis
        .getVoices()
        .find((candidate) => /male|david|mark|daniel|google uk english male/i.test(candidate.name)) ??
      window.speechSynthesis.getVoices()[0];
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput('');
    setMessages((items) => [...items, { id: uid(), role: 'user', content: text }]);
    try {
      const result = await sendText(text, false);
      if (result.reply) {
        setMessages((items) => [...items, { id: uid(), role: 'assistant', content: result.reply }]);
        speakInBrowser(result.reply);
      }
    } catch (error) {
      setMessages((items) => [
        ...items,
        { id: uid(), role: 'system', content: `Chat failed: ${error instanceof Error ? error.message : 'unknown error'}` }
      ]);
    }
  }

  async function resolveConfirmation(approved: boolean) {
    if (!confirmation) return;
    await confirmAction(confirmation, approved);
    setConfirmation(null);
  }

  async function toggleAppMic() {
    if (recording) {
      const context = audioContextRef.current;
      const processor = processorRef.current;
      const stream = streamRef.current;
      processor?.disconnect();
      stream?.getTracks().forEach((track) => track.stop());
      await context?.close();
      setRecording(false);
      const wav = encodeWav(recordingChunksRef.current, recordingSampleRateRef.current);
      try {
        const result = await transcribeVoice(wav);
        if (result.text) setMessages((items) => [...items, { id: uid(), role: 'user', content: result.text }]);
        if (result.reply) {
          setMessages((items) => [...items, { id: uid(), role: 'assistant', content: result.reply }]);
          speakInBrowser(result.reply);
        }
        if (!result.text) {
          setMessages((items) => [...items, { id: uid(), role: 'system', content: 'Mic heard no clear speech. Try again closer to the mic.' }]);
        }
      } catch (error) {
        setMessages((items) => [
          ...items,
          { id: uid(), role: 'system', content: `Mic failed: ${error instanceof Error ? error.message : 'unknown error'}` }
        ]);
      }
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const context = new AudioContext({ sampleRate: 16000 });
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);
    recordingChunksRef.current = [];
    recordingSampleRateRef.current = context.sampleRate;
    processor.onaudioprocess = (event) => {
      recordingChunksRef.current.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    };
    source.connect(processor);
    processor.connect(context.destination);
    audioContextRef.current = context;
    processorRef.current = processor;
    streamRef.current = stream;
    setRecording(true);
  }

  return (
    <div className="app-shell">
      <img className="hud-wallpaper" src={hudImage} alt="" />
      <div className="hud-vignette" />
      <aside className="command-rail">
        <div className="brand">
          <div>
            <span>Project</span>
            <strong>JARVIS</strong>
          </div>
        </div>
        <div className={`connection ${statusTone}`}>
          <Radio size={16} />
          <span>{online ? 'Core linked' : 'Core offline'}</span>
        </div>
        <button className="rail-button primary" onClick={() => startVoice()}>
          <Mic size={18} />
          VM Voice
        </button>
        <button className={`rail-button ${recording ? 'recording' : 'primary'}`} onClick={() => toggleAppMic()}>
          <Mic size={18} />
          {recording ? 'Stop App Mic' : 'App Mic'}
        </button>
        <button className="rail-button" onClick={() => stopVoice()}>
          <Square size={18} />
          Stop Voice
        </button>
        <button className="rail-button danger" onClick={() => interrupt()}>
          <Power size={18} />
          Interrupt
        </button>
        <div className="telemetry">
          <span>Voice model</span>
          <strong>VoxCPM2 local</strong>
          <span>Voice engine</span>
          <strong>VoxCPM2 thick voice</strong>
          <span>Reasoning core</span>
          <strong>NVIDIA API stream</strong>
        </div>
      </aside>

      <main className="main-stage">
        <section className="hero-panel">
          <div className="status-row">
            <span className={`status-dot ${statusTone}`} />
            <span>{stateCopy[state]}</span>
          </div>
          <HudDisplay state={state} level={audioLevel} />
        </section>

        <section className="chat-panel">
          <header>
            <div>
              <span className="eyebrow">Conversation</span>
              <h1>Jarvis Link</h1>
            </div>
            <div className="shield">
              <ShieldCheck size={18} />
              Confirm-before-action
            </div>
          </header>

          <div className="messages">
            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  layout
                  initial={{ opacity: 0, y: 24, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -12 }}
                  className={`message ${message.role}`}
                >
                  <div className="message-orb">{message.role === 'assistant' ? <Zap size={14} /> : null}</div>
                  <p>{message.content}</p>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={scrollRef} />
          </div>

          <AnimatePresence>
            {confirmation && (
              <motion.div
                className="confirmation-card"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
              >
                <div>
                  <span className="eyebrow">Safety Gate</span>
                  <strong>{confirmation.prompt}</strong>
                </div>
                <div className="confirmation-actions">
                  <button onClick={() => resolveConfirmation(false)}>Deny</button>
                  <button className="approve" onClick={() => resolveConfirmation(true)}>
                    Approve
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <form className="composer" onSubmit={submit}>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask Jarvis anything or request a confirmed action..."
            />
            <button type="submit">
              <Send size={18} />
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

function encodeWav(chunks: Float32Array[], sampleRate: number) {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const buffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(buffer);
  let offset = 0;
  const writeString = (value: string) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
    offset += value.length;
  };
  writeString('RIFF');
  view.setUint32(offset, 36 + length * 2, true);
  offset += 4;
  writeString('WAVE');
  writeString('fmt ');
  view.setUint32(offset, 16, true);
  offset += 4;
  view.setUint16(offset, 1, true);
  offset += 2;
  view.setUint16(offset, 1, true);
  offset += 2;
  view.setUint32(offset, sampleRate, true);
  offset += 4;
  view.setUint32(offset, sampleRate * 2, true);
  offset += 4;
  view.setUint16(offset, 2, true);
  offset += 2;
  view.setUint16(offset, 16, true);
  offset += 2;
  writeString('data');
  view.setUint32(offset, length * 2, true);
  offset += 4;
  for (const chunk of chunks) {
    for (const sample of chunk) {
      const clamped = Math.max(-1, Math.min(1, sample));
      view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
      offset += 2;
    }
  }
  return new Blob([view], { type: 'audio/wav' });
}

function HudDisplay({ state, level }: { state: JarvisState; level: number }) {
  return (
    <div className={`hud-display ${state}`}>
      <img src={hudImage} alt="Jarvis HUD interface" />
      <motion.div
        className="hud-pulse"
        animate={{ scale: [1, 1.08 + level * 0.08, 1], opacity: [0.25, 0.65, 0.25] }}
        transition={{ repeat: Infinity, duration: state === 'thinking' ? 1.2 : 2.2 }}
      />
      <Waveform level={level} state={state} />
    </div>
  );
}

function JarvisCore({ state, level }: { state: JarvisState; level: number }) {
  return (
    <div className={`core-wrap ${state}`} data-level={level}>
      <motion.div
        className="outer-ring"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: state === 'thinking' ? 5 : 12, ease: 'linear' }}
      />
      <motion.div
        className="middle-ring"
        animate={{ rotate: -360, scale: 1 + level * 0.06 }}
        transition={{ rotate: { repeat: Infinity, duration: 9, ease: 'linear' }, scale: { duration: 0.2 } }}
      />
      <motion.div
        className="inner-core"
        animate={{ scale: [1, 1.08 + level * 0.12, 1], opacity: [0.88, 1, 0.88] }}
        transition={{ repeat: Infinity, duration: state === 'speaking' ? 1.2 : 2.4 }}
      >
        <svg className="helmet-emblem" viewBox="0 0 160 160" aria-label="Jarvis armored AI emblem">
          <defs>
            <linearGradient id="helmetGold" x1="24" x2="136" y1="22" y2="138">
              <stop offset="0" stopColor="#fff7ad" />
              <stop offset="0.38" stopColor="#fbbf24" />
              <stop offset="1" stopColor="#b45309" />
            </linearGradient>
            <linearGradient id="helmetRed" x1="20" x2="150" y1="30" y2="130">
              <stop offset="0" stopColor="#ef4444" />
              <stop offset="1" stopColor="#7f1d1d" />
            </linearGradient>
            <filter id="helmetGlow">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <path className="helmet-shell" d="M80 16 123 34 139 78 127 128 99 146H61l-28-18-12-50 16-44Z" />
          <path className="helmet-face" d="M49 48h62l13 34-13 38-22 13H71l-22-13-13-38Z" />
          <path className="helmet-brow" d="M43 66 67 58h26l24 8-8 14H51Z" />
          <path className="helmet-eye left" d="M48 86h32l-8 12H51Z" />
          <path className="helmet-eye right" d="M80 86h32l-3 12H88Z" />
          <path className="helmet-mouth" d="M58 116h44l-12 10H70Z" />
          <path className="helmet-coreline" d="M80 58v70" />
        </svg>
      </motion.div>
      <div className="scanline" />
    </div>
  );
}

function Waveform({ level, state }: { level: number; state: JarvisState }) {
  const bars = Array.from({ length: 48 }, (_, index) => {
    const phase = Math.sin(index * 0.55 + Date.now() / 650);
    return Math.max(10, 20 + phase * 24 + level * 90);
  });
  return (
    <div className={`waveform ${state}`}>
      {bars.map((height, index) => (
        <motion.span
          key={index}
          animate={{ height }}
          transition={{ duration: 0.28, ease: 'easeOut' }}
          style={{ opacity: 0.36 + (index % 7) * 0.08 }}
        />
      ))}
    </div>
  );
}
