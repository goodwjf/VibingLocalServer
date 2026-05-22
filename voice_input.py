#!/usr/bin/env python3
"""
Voice Input Tool — record → ASR → paste
Usage:
  python3 voice_input.py record      # Start recording (background)
  python3 voice_input.py stop        # Stop recording → ASR → paste
  python3 voice_input.py transcribe <wav>  # Transcribe existing file
"""
import sys, os, signal, json, time, subprocess, tempfile
from pathlib import Path
import numpy as np

MODEL_DIR = Path.home() / "Library/Application Support/Memo/models"
SENSE_VOICE_DIR = MODEL_DIR / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
MODEL_PATH = SENSE_VOICE_DIR / "model.int8.onnx"
TOKENS_PATH = SENSE_VOICE_DIR / "tokens.txt"
SAMPLE_RATE = 16000
PID_FILE = "/tmp/voice_input_record.pid"
PCM_FILE = "/tmp/voice_input_recording.pcm"

def transcribe(pcm):
    import sherpa_onnx
    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=str(MODEL_PATH), tokens=str(TOKENS_PATH),
        num_threads=4, language="auto", use_itn=True,
    )
    samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    stream = recognizer.create_stream()
    stream.accept_waveform(SAMPLE_RATE, samples)
    recognizer.decode_stream(stream)
    return stream.result.text.strip()

def paste_text(text):
    """Paste text using clipboard + Cmd+V"""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    script = f'''
    set the clipboard to "{escaped}"
    delay 0.1
    tell application "System Events" to keystroke "v" using command down
    '''
    subprocess.run(["osascript", "-e", script])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "record":
        try:
            import sounddevice as sd
        except ImportError:
            print("Install: pip install sounddevice", file=sys.stderr)
            sys.exit(1)

        recorded = []
        def cb(indata, frames, time, status):
            recorded.append(indata.copy())

        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', callback=cb)
        stream.start()

        # Write PID so stop can find us
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        print(f"Recording started (PID {os.getpid()})", file=sys.stderr)

        # Wait until killed
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()
            if recorded:
                audio = np.concatenate(recorded)
                with open(PCM_FILE, "wb") as f:
                    f.write(audio.tobytes())
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

    elif len(sys.argv) > 1 and sys.argv[1] == "stop":
        # Kill the recording process
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                # Wait a moment for PCM file to be written
                time.sleep(0.5)
            except ProcessLookupError:
                pass

        # Transcribe
        if os.path.exists(PCM_FILE):
            with open(PCM_FILE, "rb") as f:
                pcm = f.read()
            os.remove(PCM_FILE)

            if len(pcm) > 44:  # Minimum audio
                print(f"Processing {len(pcm)} bytes...", file=sys.stderr)
                text = transcribe(pcm)
                print(f"ASR: {text}", file=sys.stderr)
                if text:
                    paste_text(text)
                    print(f"Pasted: {text}")
            else:
                print("Audio too short", file=sys.stderr)
        else:
            print("No recording found", file=sys.stderr)

    elif len(sys.argv) > 2 and sys.argv[1] == "transcribe":
        import soundfile as sf
        audio, sr = sf.read(sys.argv[2])
        pcm = (audio * 32768).astype(np.int16).tobytes()
        text = transcribe(pcm)
        print(text)
