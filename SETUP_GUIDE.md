# Project Jarvis Setup Guide

This delivery contains two repos:

- `jarvis-backend` — Python async AI engine.
- `jarvis-frontend` — Electron + React GUI client.

## 1. Backend setup

```bash
cd /home/ubuntu/repos/jarvis-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NVIDIA_API_KEY="your-nvidia-api-key"
python -m jarvis_backend --config config.yaml
```

## 2. Faster-Whisper local STT

Faster-Whisper is configured as the main STT engine:

```yaml
stt:
  engine: "faster_whisper"
  model_size: "small.en"
  device: "auto"
  compute_type: "auto"
```

GPU acceleration:

- Install CUDA-compatible NVIDIA drivers.
- Use `device: "cuda"` and `compute_type: "float16"`.
- Keep `auto` if you want CPU fallback.

Low latency recommendations:

- CPU: `base.en` or `small.en`.
- GPU: `small.en`, `medium.en`, or `large-v3`.
- Use beam size `1` for fastest partial-turn transcription.

## 3. Local TTS

Default local TTS is Piper.

Install Piper, then download a voice:

```bash
cd /home/ubuntu/repos/jarvis-backend
mkdir -p voices
wget -O voices/en_US-lessac-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget -O voices/en_US-lessac-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

Optional Coqui local TTS:

```bash
pip install TTS
```

Then set:

```yaml
tts:
  engine: "coqui"
```

## 4. Browser debugging

Jarvis must attach to an existing browser session.

Linux:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/jarvis-browser-profile"
```

Windows:

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\jarvis-profile"
```

## 5. Frontend setup

```bash
cd /home/ubuntu/repos/jarvis-frontend
npm install
npm run start
```

## 6. Running both together

Terminal 1:

```bash
cd /home/ubuntu/repos/jarvis-backend
source .venv/bin/activate
export NVIDIA_API_KEY="your-nvidia-api-key"
python -m jarvis_backend --config config.yaml
```

Terminal 2:

```bash
cd /home/ubuntu/repos/jarvis-frontend
npm run start
```

## 7. Safety

Jarvis never directly executes arbitrary LLM text. The LLM proposes structured JSON actions, then the backend:

1. Parses the JSON.
2. Validates fields.
3. Shows a GUI confirmation prompt.
4. Executes only after approval.

System commands and apps are allowlisted in `config.yaml`.
