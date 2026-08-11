#!/usr/bin/env python3
# ============================================================
# BirdNET Outdoor-Mikrofon – WAV-Empfänger
# ============================================================
# Nimmt WAV-Dateien vom XIAO ESP32-S3 via HTTP POST entgegen
# und speichert sie in ~/BirdSongs/StreamData/ zur Analyse.
#
# Built as a "brain gym" project – keeping the mind sharp
# through electronics and code. 🧠💪
# by Paul and Claude, Anthropic 2026
# ============================================================

import os
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

# ============================================================
# KONFIGURATION
# ============================================================

BIRDSONGS_DIR = Path.home() / "BirdSongs"
STREAM_DATA_DIR = BIRDSONGS_DIR / "StreamData"

HOST = "0.0.0.0"
PORT = 5000

# ============================================================
# SETUP
# ============================================================

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

STREAM_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# ROUTEN
# ============================================================

@app.route('/upload', methods=['POST'])
def upload_wav():
    """Empfaengt WAV vom ESP32, speichert in StreamData."""
    try:
        data = request.get_data()

        if len(data) < 44:
            logger.error(f"Datei zu klein: {len(data)} Bytes")
            return jsonify({"status": "error", "message": "Too small"}), 400

        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            logger.error("Ungueltiger WAV-Header!")
            return jsonify({"status": "error", "message": "Invalid WAV"}), 400

        # Dateiname mit Zeitstempel
        timestamp = datetime.now().strftime("%Y-%m-%d-birdnet-%H:%M:%S")
        filename = f"{timestamp}.wav"
        filepath = STREAM_DATA_DIR / filename

        with open(filepath, 'wb') as f:
            f.write(data)

        size_kb = len(data) / 1024
        duration = (len(data) - 44) / (48000 * 2)

        logger.info(f"Gespeichert: {filename} ({size_kb:.1f} KB, {duration:.1f}s)")

        return jsonify({
            "status": "ok",
            "filename": filename,
            "size": len(data),
            "duration": round(duration, 1)
        }), 200

    except Exception as e:
        logger.error(f"Fehler: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health-Check Endpoint."""
    wav_count = len(list(STREAM_DATA_DIR.glob("*.wav")))
    return jsonify({
        "status": "ok",
        "service": "birdnet-receiver",
        "wav_files": wav_count,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/stats', methods=['GET'])
def stats():
    """Statistiken ueber empfangene Dateien."""
    wav_files = sorted(STREAM_DATA_DIR.glob("*.wav"))
    total_size = sum(f.stat().st_size for f in wav_files)
    return jsonify({
        "total_files": len(wav_files),
        "total_size_mb": round(total_size / 1048576, 2),
        "latest": wav_files[-1].name if wav_files else None
    }), 200


# ============================================================
# START
# ============================================================

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("  BirdNET WAV-Empfaenger gestartet")
    logger.info(f"  http://{HOST}:{PORT}")
    logger.info(f"  Speicherort: {STREAM_DATA_DIR}")
    logger.info("=" * 50)
    app.run(host=HOST, port=PORT, debug=False)
