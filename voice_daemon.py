#!/usr/bin/env python3
"""
Voice Input Daemon — 按住右 Option 说话，松开自动识别并粘贴

Usage:
  python3 voice_daemon.py          # Start daemon (background)
  python3 voice_daemon.py --stop   # Stop daemon
"""
import sys, os, signal, time, tempfile, subprocess, threading, json
from pathlib import Path
import numpy as np
from urllib.request import Request, urlopen
from urllib.error import URLError

# === Config ===
import json

_SCRIPT_DIR = Path(__file__).parent
_CONFIG_PATH = _SCRIPT_DIR / "config.json"

with open(_CONFIG_PATH) as f:
    _cfg = json.load(f)

MODELS_DIR = Path(_cfg["models_dir"]).expanduser()
MODEL_SUBDIR = _cfg["model_subdir"]
MODEL_FILENAME = _cfg["model_filename"]
TOKENS_FILENAME = _cfg["tokens_filename"]
HOTKEY = _cfg["hotkey"]
SAMPLE_RATE = _cfg.get("sample_rate", 16000)
PID_FILE = _cfg.get("pid_file", "/tmp/voice_daemon.pid")

MODEL_PATH = MODELS_DIR / MODEL_SUBDIR / MODEL_FILENAME
TOKENS_PATH = MODELS_DIR / MODEL_SUBDIR / TOKENS_FILENAME

PUNCT_MODEL_DIR = _cfg.get("punctuation_model_dir")
PUNCT_MODEL_PATH = Path(PUNCT_MODEL_DIR) / "model.onnx" if PUNCT_MODEL_DIR else None

OLLAMA_ENABLED = _cfg.get("ollama_enabled", False)
OLLAMA_MODEL = _cfg.get("ollama_model", "qwen2.5:7b")

_recognizer = None
def get_recognizer():
    global _recognizer
    if _recognizer is None:
        import sherpa_onnx
        _recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=str(MODEL_PATH), tokens=str(TOKENS_PATH),
            num_threads=4, language="auto", use_itn=True,
        )
    return _recognizer

def transcribe(pcm):
    rec = get_recognizer()
    samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    stream = rec.create_stream()
    stream.accept_waveform(SAMPLE_RATE, samples)
    rec.decode_stream(stream)
    return stream.result.text.strip()

_punctuation = None
def get_punctuation():
    global _punctuation
    if _punctuation is None and PUNCT_MODEL_PATH and PUNCT_MODEL_PATH.exists():
        import sherpa_onnx
        model_config = sherpa_onnx.OfflinePunctuationModelConfig(
            ct_transformer=str(PUNCT_MODEL_PATH), num_threads=4)
        config = sherpa_onnx.OfflinePunctuationConfig(model=model_config)
        _punctuation = sherpa_onnx.OfflinePunctuation(config)
    return _punctuation

def add_punctuation(text):
    punct = get_punctuation()
    if punct and text:
        return punct.add_punctuation(text)
    return text

def paste_text(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    script = f'''
    set the clipboard to "{escaped}"
    delay 0.1
    tell application "System Events" to keystroke "v" using command down
    '''
    subprocess.run(["osascript", "-e", script])

def _sound_start():
    subprocess.run(["afplay", "/System/Library/Sounds/Blow.aiff"], stderr=subprocess.DEVNULL)

def _sound_done():
    subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], stderr=subprocess.DEVNULL)

def correct_text(text):
    if not OLLAMA_ENABLED or not text:
        return text
    prompt = f"你是一个文本纠错助手。下面是一段语音识别结果，请修正其中的同音字错误和不通顺之处。只输出修正后的文本，不要额外说明。\n\n{text}"
    body = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode()
    req = Request("http://localhost:11434/api/generate", data=body,
                  headers={"Content-Type": "application/json"})
    try:
        resp = json.loads(urlopen(req, timeout=30).read())
        corrected = resp.get("response", "").strip()
        if corrected:
            sys.stderr.write(f"[voice] Corrected: {corrected}\n")
            sys.stderr.flush()
            return corrected
    except URLError as e:
        sys.stderr.write(f"[voice] Ollama unavailable ({e.reason}), using original text\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"[voice] Correction failed ({e}), using original text\n")
        sys.stderr.flush()
    return text

def _sound_start():
    subprocess.run(["afplay", "/System/Library/Sounds/Blow.aiff"], stderr=subprocess.DEVNULL)

def _sound_done():
    subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], stderr=subprocess.DEVNULL)

# === Recording State ===
_recording = False
_recorded_audio = []
_recording_stream = None
_lock = threading.Lock()

def start_recording():
    global _recording, _recorded_audio, _recording_stream
    with _lock:
        if _recording:
            return
        _recording = True
        _recorded_audio.clear()
    import sounddevice as sd
    def callback(indata, frames, time, status):
        with _lock:
            if _recording:
                _recorded_audio.append(indata.copy())
    _recording_stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype='int16', callback=callback
    )
    _recording_stream.start()
    threading.Thread(target=_sound_start, daemon=True).start()
    sys.stderr.write("[voice] Recording started\n")
    sys.stderr.flush()

def stop_recording():
    global _recording, _recording_stream, _recorded_audio
    if _recording_stream:
        _recording_stream.stop()
        _recording_stream.close()
        _recording_stream = None
    with _lock:
        if not _recording:
            return
        _recording = False
        audio_data = list(_recorded_audio)
        _recorded_audio = []
    sys.stderr.write("[voice] Recording stopped\n")
    sys.stderr.flush()

    if not audio_data:
        return

    audio = np.concatenate(audio_data)
    pcm = audio.tobytes()
    if len(pcm) < 3200:
        return
    
    sys.stderr.write(f"[voice] Transcribing {len(pcm)} bytes...\n")
    sys.stderr.flush()
    text = transcribe(pcm)
    sys.stderr.write(f"[voice] ASR: {text}\n")
    sys.stderr.flush()
    # Strip all punctuation ASR may have added (use_itn), let punct model re-add
    import re as _re
    text_clean = _re.sub(r"[，。？、！；：,.?!;:\u3000-\u303f\uff00-\uffef]", " ", text)
    text_clean = _re.sub(r"\s+", " ", text_clean).strip()
    text = add_punctuation(text_clean)
    if text:
        sys.stderr.write(f"[voice] Punctuated: {text}\n")
        sys.stderr.flush()
    text = correct_text(text)
    
    if text:
        paste_text(text)
        sys.stderr.write(f"[voice] Pasted: {text}\n")
        sys.stderr.flush()
        _sound_done()

def run_daemon():
    from pynput import keyboard
    
    def on_press(key):
        try:
            if key == getattr(keyboard.Key, HOTKEY):
                start_recording()
        except AttributeError:
            pass
    
    def on_release(key):
        try:
            if key == getattr(keyboard.Key, HOTKEY):
                # Run in thread to avoid blocking listener
                threading.Thread(target=stop_recording, daemon=True).start()
        except AttributeError:
            pass
    
    # Write PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    sys.stderr.write(f"[voice] Daemon started (PID {os.getpid()})\n")
    sys.stderr.write("[voice] Hold Right Option to record, release to paste\n")
    sys.stderr.flush()
    
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    if "--stop" in sys.argv:
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Daemon {pid} stopped")
            except ProcessLookupError:
                print("Daemon not running")
            os.remove(PID_FILE)
        else:
            print("Daemon not running")
        sys.exit(0)
    
    run_daemon()
