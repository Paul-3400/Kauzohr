---
title: "receiver.py v1.4 – Persistenter RTSP-Stream"
date: 2026-09-01
author: "Paul mit Claude (Anthropic Claude 4, 2026)"
purpose: "BirdNET Outdoor-Mikrofon WAV-Empfänger mit persistentem ffmpeg→RTSP Stream für BirdNET-Go"
version: "1.4"
---

# receiver.py v1.4 – Persistenter RTSP-Stream

## Ziel-Dateiname: `receiver.py`
## Ziel-Pfad: `~/birdnet-receiver/receiver.py`

## Änderungen gegenüber v1.3
- **Ersetzt aplay/Loopback durch ffmpeg→RTSP** (mediaMTX)
- Persistenter ffmpeg-Prozess hält RTSP-Stream `/birds` dauerhaft offen
- Zwischen WAVs wird Stille gestreamt → BirdNET-Go kann jederzeit verbinden
- WAV-Empfang → PCM wird in ffmpeg-Pipe geschrieben → sofort im RTSP-Stream

## Code

```python
#!/usr/bin/env python3
# ============================================================
# BirdNET Outdoor-Mikrofon – WAV-Empfänger v1.4
# Erstellt von Paul mit Claude (Anthropic Claude 4, 2026)
# ============================================================
# ESP32 sendet WAV-Dateien via HTTP POST.
# Dieser Server:
#   1. Speichert WAV in StreamData/
#   2. Streamt PCM via persistentem ffmpeg → RTSP (mediaMTX)
#   3. Antwortet mit JSON-Config für den ESP32
# ============================================================

import os
import sys
import wave
import struct
import subprocess
import threading
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# ============================================================
# Konfiguration
# ============================================================
SAVE_DIR = "/home/paul-rppi/BirdSongs/StreamData"
HOST = "0.0.0.0"
PORT = 5000
LOG_LEVEL = logging.INFO

# RTSP-Konfiguration
RTSP_URL = "rtsp://127.0.0.1:8554/birds"
RTSP_ENABLED = True

# Audio-Format (muss zum ESP32 passen)
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes
BYTES_PER_SECOND = SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH  # 96000 B/s

# Stille-Intervall: Wie oft Stille-Chunks gesendet werden (Sekunden)
SILENCE_CHUNK_SECONDS = 0.5
SILENCE_CHUNK_SIZE = int(BYTES_PER_SECOND * SILENCE_CHUNK_SECONDS)

# ESP32-Konfiguration (wird als JSON-Response gesendet)
ESP32_CONFIG = {
    "rec_duration": 20,
    "sample_rate": SAMPLE_RATE,
    "gain": 24,
    "sleep_duration": 10,
    "deep_sleep": True,
    "wifi_timeout": 10
}

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("receiver")

# ============================================================
# Flask App
# ============================================================
app = Flask(__name__)

# ============================================================
# RTSPStream – Persistenter ffmpeg-Prozess
# ============================================================
class RTSPStream:
    """
    Hält einen persistenten ffmpeg-Prozess am Leben, der
    raw PCM (S16LE, 48kHz, Mono) via stdin empfängt und
    als Opus-RTSP-Stream an mediaMTX sendet.

    Zwischen WAV-Dateien wird Stille gesendet, damit der
    RTSP-Stream nie abbricht und BirdNET-Go jederzeit
    verbinden kann.
    """

    def __init__(self, rtsp_url, sample_rate, channels):
        self.rtsp_url = rtsp_url
        self.sample_rate = sample_rate
        self.channels = channels
        self.process = None
        self.lock = threading.Lock()
        self.running = False
        self.silence_thread = None
        self.feeding = False  # True wenn gerade WAV-Daten gesendet werden
        self._start_count = 0

    def start(self):
        """Startet den ffmpeg-Prozess und den Stille-Generator."""
        with self.lock:
            if self.process and self.process.poll() is None:
                log.warning("RTSP: ffmpeg läuft bereits (PID %d)", self.process.pid)
                return

            self._start_ffmpeg()
            self.running = True

            # Stille-Generator Thread starten
            self.silence_thread = threading.Thread(
                target=self._silence_generator,
                daemon=True,
                name="silence-generator"
            )
            self.silence_thread.start()

    def _start_ffmpeg(self):
        """Startet einen neuen ffmpeg-Prozess."""
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            # Input: Raw PCM von stdin
            "-f", "s16le",
            "-ar", str(self.sample_rate),
            "-ac", str(self.channels),
            "-i", "pipe:0",
            # Output: Opus via RTSP
            "-acodec", "libopus",
            "-ar", str(self.sample_rate),
            "-ac", str(self.channels),
            "-b:a", "96k",
            "-f", "rtsp",
            "-rtsp_transport", "tcp",
            self.rtsp_url
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            self._start_count += 1
            log.info("RTSP: ffmpeg gestartet (PID %d, Start #%d) → %s",
                     self.process.pid, self._start_count, self.rtsp_url)
        except Exception as e:
            log.error("RTSP: ffmpeg Start fehlgeschlagen: %s", e)
            self.process = None

    def _silence_generator(self):
        """
        Sendet kontinuierlich Stille (Null-Bytes) in die ffmpeg-Pipe,
        solange keine WAV-Daten gesendet werden.
        Hält den RTSP-Stream permanent aktiv.
        """
        silence_chunk = b'\x00' * SILENCE_CHUNK_SIZE
        log.info("RTSP: Stille-Generator gestartet (%.1fs Chunks, %d Bytes)",
                 SILENCE_CHUNK_SECONDS, SILENCE_CHUNK_SIZE)

        while self.running:
            try:
                if not self.feeding:
                    self._write_to_pipe(silence_chunk)
                time.sleep(SILENCE_CHUNK_SECONDS)
            except Exception as e:
                log.error("RTSP: Stille-Generator Fehler: %s", e)
                self._restart_ffmpeg()
                time.sleep(2)

    def _write_to_pipe(self, data):
        """Schreibt Daten in die ffmpeg stdin-Pipe (thread-safe)."""
        with self.lock:
            if self.process and self.process.poll() is None:
                try:
                    self.process.stdin.write(data)
                    self.process.stdin.flush()
                except (BrokenPipeError, OSError) as e:
                    log.error("RTSP: Pipe gebrochen: %s", e)
                    self._restart_ffmpeg_unlocked()
            else:
                self._restart_ffmpeg_unlocked()

    def _restart_ffmpeg(self):
        """Restart mit Lock."""
        with self.lock:
            self._restart_ffmpeg_unlocked()

    def _restart_ffmpeg_unlocked(self):
        """Beendet alten Prozess und startet neu (ohne Lock)."""
        if self.process:
            try:
                self.process.stdin.close()
            except Exception:
                pass
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            log.warning("RTSP: ffmpeg beendet, starte neu...")
        self._start_ffmpeg()

    def feed_wav(self, filepath):
        """
        Liest eine WAV-Datei, extrahiert die PCM-Daten und
        schreibt sie in die ffmpeg-Pipe.

        Konvertiert bei Bedarf Sample-Rate und Channels.
        """
        self.feeding = True
        try:
            with wave.open(filepath, 'rb') as wf:
                wav_rate = wf.getframerate()
                wav_channels = wf.getnchannels()
                wav_width = wf.getsampwidth()
                n_frames = wf.getnframes()
                pcm_data = wf.readframes(n_frames)

            log.info("RTSP: WAV einlesen – %d Hz, %d ch, %d bit, %d frames (%.1f sek)",
                     wav_rate, wav_channels, wav_width * 8, n_frames,
                     n_frames / wav_rate)

            # Format-Konvertierung falls nötig
            pcm_data = self._convert_pcm(
                pcm_data, wav_rate, wav_channels, wav_width
            )

            # PCM in die Pipe schreiben (in Chunks für Echtzeit-Streaming)
            chunk_duration = 0.1  # 100ms Chunks
            chunk_size = int(BYTES_PER_SECOND * chunk_duration)
            offset = 0

            while offset < len(pcm_data):
                chunk = pcm_data[offset:offset + chunk_size]
                self._write_to_pipe(chunk)
                offset += chunk_size
                time.sleep(chunk_duration * 0.95)  # Knapp unter Echtzeit

            duration = len(pcm_data) / BYTES_PER_SECOND
            log.info("RTSP: WAV gestreamt (%.1f sek PCM-Daten)", duration)

        except Exception as e:
            log.error("RTSP: Fehler beim WAV-Streaming: %s", e)
        finally:
            self.feeding = False

    def _convert_pcm(self, pcm_data, src_rate, src_channels, src_width):
        """
        Konvertiert PCM-Daten zum Zielformat (48kHz, Mono, 16-bit).
        """
        # Stereo → Mono
        if src_channels == 2 and self.channels == 1:
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            mono = []
            for i in range(0, len(samples), 2):
                mono.append((samples[i] + samples[i+1]) // 2)
            pcm_data = struct.pack(f'<{len(mono)}h', *mono)
            log.info("RTSP: Stereo → Mono konvertiert")

        # 8-bit → 16-bit
        if src_width == 1:
            samples_8 = struct.unpack(f'{len(pcm_data)}B', pcm_data)
            samples_16 = [(s - 128) * 256 for s in samples_8]
            pcm_data = struct.pack(f'<{len(samples_16)}h', *samples_16)
            log.info("RTSP: 8-bit → 16-bit konvertiert")

        # Sample-Rate Konvertierung (einfaches Resampling)
        if src_rate != self.sample_rate:
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            ratio = self.sample_rate / src_rate
            new_length = int(len(samples) * ratio)
            resampled = []
            for i in range(new_length):
                src_idx = i / ratio
                idx = int(src_idx)
                if idx >= len(samples) - 1:
                    resampled.append(samples[-1])
                else:
                    frac = src_idx - idx
                    val = int(samples[idx] * (1 - frac) + samples[idx + 1] * frac)
                    resampled.append(max(-32768, min(32767, val)))
            pcm_data = struct.pack(f'<{len(resampled)}h', *resampled)
            log.info("RTSP: %d Hz → %d Hz resampled (%d → %d samples)",
                     src_rate, self.sample_rate, len(samples), len(resampled))

        return pcm_data

    def get_status(self):
        """Gibt Status-Info zurück."""
        ffmpeg_alive = self.process and self.process.poll() is None
        return {
            "enabled": RTSP_ENABLED,
            "ffmpeg_running": ffmpeg_alive,
            "ffmpeg_pid": self.process.pid if ffmpeg_alive else None,
            "rtsp_url": self.rtsp_url,
            "start_count": self._start_count,
            "currently_feeding": self.feeding
        }

    def stop(self):
        """Beendet den Stream sauber."""
        self.running = False
        with self.lock:
            if self.process:
                try:
                    self.process.stdin.close()
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                log.info("RTSP: ffmpeg gestoppt")

# ============================================================
# Globale Stream-Instanz
# ============================================================
rtsp_stream = None

if RTSP_ENABLED:
    rtsp_stream = RTSPStream(RTSP_URL, SAMPLE_RATE, CHANNELS)

# ============================================================
# Routen
# ============================================================
@app.route("/upload", methods=["POST"])
def upload():
    """
    Empfängt WAV-Datei vom ESP32, speichert sie und
    streamt sie via RTSP an BirdNET-Go.
    """
    try:
        # --- Batteriespannung lesen (optional) ---
        battery_v = request.args.get("battery", "n/a")
        log.info("Batterie: %sV", battery_v)

        # --- WAV-Daten empfangen ---
        wav_data = request.get_data()
        if not wav_data or len(wav_data) < 44:
            log.warning("Leere oder ungültige WAV-Daten (%d Bytes)", len(wav_data))
            return jsonify({"error": "no data"}), 400

        # --- Dateiname generieren ---
        timestamp = datetime.now().strftime("%Y-%m-%d-birdnet-%H:%M:%S")
        filename = f"{timestamp}.wav"
        filepath = os.path.join(SAVE_DIR, filename)

        # --- Speichern ---
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(wav_data)
        log.info("Gespeichert: %s (%d Bytes)", filename, len(wav_data))

        # --- An RTSP-Stream senden (async) ---
        if RTSP_ENABLED and rtsp_stream:
            feed_thread = threading.Thread(
                target=rtsp_stream.feed_wav,
                args=(filepath,),
                daemon=True,
                name="rtsp-feed"
            )
            feed_thread.start()
            log.info("RTSP: WAV wird gestreamt → %s", RTSP_URL)

        # --- Config an ESP32 zurücksenden ---
        log.info("Config an ESP32 ausgeliefert: %s", ESP32_CONFIG)
        return jsonify(ESP32_CONFIG), 200

    except Exception as e:
        log.error("Upload-Fehler: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health-Check Endpoint mit RTSP-Status."""
    status = {
        "status": "ok",
        "version": "1.4",
        "save_dir": SAVE_DIR,
        "esp32_config": ESP32_CONFIG
    }
    if rtsp_stream:
        status["rtsp"] = rtsp_stream.get_status()
    return jsonify(status), 200

# ============================================================
# Startup
# ============================================================
def start_rtsp():
    """Startet den RTSP-Stream beim Server-Start."""
    if RTSP_ENABLED and rtsp_stream:
        # Kurz warten bis mediaMTX bereit ist
        time.sleep(2)
        rtsp_stream.start()
        log.info("RTSP-Stream initialisiert → %s", RTSP_URL)
    else:
        log.info("RTSP-Stream deaktiviert")

if __name__ == "__main__":
    log.info("=" * 60)
    log.info("BirdNET WAV-Empfänger v1.4 – RTSP-Stream")
    log.info("Erstellt von Paul mit Claude (Anthropic Claude 4, 2026)")
    log.info("Speicherort: %s", SAVE_DIR)
    log.info("RTSP: %s → %s", "aktiv" if RTSP_ENABLED else "inaktiv", RTSP_URL)
    log.info("=" * 60)

    # RTSP-Stream in Background starten
    startup_thread = threading.Thread(target=start_rtsp, daemon=True)
    startup_thread.start()

    # Flask starten
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
```

## Deployment

### 📌 Typora-CopyPaste-Thonny-Save
1. Diese `.md` in **Typora** öffnen
2. Python-Code **kopieren**
3. In **Thonny** einfügen
4. Speichern als `receiver.py`
5. Per SCP auf den Pi laden

### Auf dem Pi
```bash
# Prüfen
grep "v1\." ~/birdnet-receiver/receiver.py

# Service neu starten
sudo systemctl restart birdnet_receiver
sudo systemctl status birdnet_receiver
```

### Integrationstest
```bash
# RTSP-Stream prüfen
curl -s http://localhost:9997/v3/paths/list

# BirdNET-Go Logs
sudo docker logs birdnet-go 2>&1 | tail -20
```
