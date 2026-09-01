#!/usr/bin/env python3
# ============================================================
# BirdNET Outdoor-Mikrofon – WAV-Empfänger v1.2
# ============================================================
# Nimmt WAV-Dateien vom XIAO ESP32-S3 via HTTP POST entgegen
# und speichert sie in ~/BirdSongs/StreamData/ zur Analyse.
#
# v1.2 Erweiterungen:
#   - ALSA Loopback: WAV wird async via aplay an hw:Loopback,0,0
#     gesendet → BirdNET-Go lauscht auf hw:Loopback,1,0
#
# v1.1 Erweiterungen:
#   - Batteriespannung vom ESP32 empfangen und loggen
#   - Remote-Konfiguration für ESP32 (/config Endpoint)
#   - Voltage-API für Dashboard (/api/voltage)
#
# Built as a "brain gym" project – keeping the mind sharp
# through electronics and code. 🧠💪
# by Paul and Claude (Anthropic Claude, 2026)
# ============================================================

import os
import json
import time
import logging
import subprocess
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

# Neue Pfade für v1.1
RECEIVER_DIR = Path.home() / "birdnet-receiver"
VOLTAGE_LOG = RECEIVER_DIR / "voltage_log.json"
CONFIG_FILE = RECEIVER_DIR / "config.json"

# v1.2: ALSA Loopback Device (Playback-Seite)
# Card 3 = Loopback, Device 0 = Playback, Subdevice 0
LOOPBACK_DEVICE = "hw:Loopback,0,0"
LOOPBACK_ENABLED = True

# Default ESP32-Konfiguration (Fallback)
DEFAULT_CONFIG = {
    "active_hour_start": 4,
    "active_hour_end": 22,
    "record_duration_sec": 20,
    "deep_sleep_sec": 5,
    "wifi_timeout_ms": 10000,
    "post_timeout_ms": 5000,
    "gain": 2.0,
    "noise_threshold": 500,
    "hp_filter_alpha": 0.98,
    "use_noise_gate": True,
    "use_hp_filter": True
}

# Voltage-Log: max. Einträge (ca. 7 Tage bei 2160 Zyklen/Tag)
MAX_VOLTAGE_ENTRIES = 15000

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
RECEIVER_DIR.mkdir(parents=True, exist_ok=True)

# Config-Datei initialisieren falls nicht vorhanden
if not CONFIG_FILE.exists():
    cfg_init = DEFAULT_CONFIG.copy()
    cfg_init["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CONFIG_FILE.write_text(json.dumps(cfg_init, indent=2))
    logger.info(f"Config-Datei erstellt: {CONFIG_FILE}")

# v1.2: Liste für aktive aplay-Prozesse (Cleanup)
_aplay_processes = []

# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def load_config():
    """ESP32-Konfiguration aus JSON laden."""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        logger.error("Config JSON fehlerhaft – nutze Defaults")
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """ESP32-Konfiguration in JSON speichern."""
    cfg["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    logger.info(f"Config gespeichert: {CONFIG_FILE}")


def log_voltage(voltage):
    """Batteriespannung in JSON-Log anhängen."""
    entries = []
    if VOLTAGE_LOG.exists():
        try:
            entries = json.loads(VOLTAGE_LOG.read_text())
        except json.JSONDecodeError:
            entries = []

    entries.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "voltage": round(voltage, 3)
    })

    # Alte Einträge entfernen wenn Limit erreicht
    if len(entries) > MAX_VOLTAGE_ENTRIES:
        entries = entries[-MAX_VOLTAGE_ENTRIES:]

    VOLTAGE_LOG.write_text(json.dumps(entries))
    logger.info(f"Batterie: {voltage:.3f}V geloggt")


def play_to_loopback(filepath):
    """WAV-Datei asynchron via aplay in den ALSA Loopback spielen.

    Läuft non-blocking im Hintergrund, damit der HTTP-Response
    sofort zurückgegeben werden kann. BirdNET-Go lauscht auf
    der Capture-Seite (hw:Loopback,1,0) des Loopback-Devices.
    """
    if not LOOPBACK_ENABLED:
        return

    # Cleanup: beendete Prozesse aus der Liste entfernen
    still_running = []
    for proc in _aplay_processes:
        if proc.poll() is None:
            still_running.append(proc)
        else:
            if proc.returncode != 0:
                logger.warning(f"aplay beendet mit Code {proc.returncode}")
    _aplay_processes.clear()
    _aplay_processes.extend(still_running)

    try:
        proc = subprocess.Popen(
            ["aplay", "-D", LOOPBACK_DEVICE, str(filepath)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        _aplay_processes.append(proc)
        logger.info(f"Loopback: aplay gestartet (PID {proc.pid}) → {filepath.name}")
    except FileNotFoundError:
        logger.error("aplay nicht gefunden! ALSA-Utils installiert?")
    except Exception as e:
        logger.error(f"Loopback-Fehler: {e}")


# ============================================================
# ROUTEN – Bestehend (aus v1.0)
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

        # NEU v1.1: Batteriespannung aus Header lesen
        voltage = request.headers.get('X-Battery-Voltage', None)
        if voltage:
            try:
                log_voltage(float(voltage))
            except ValueError:
                logger.warning(f"Ungueltige Spannung im Header: {voltage}")

        # NEU v1.2: WAV in ALSA Loopback spielen (async)
        play_to_loopback(filepath)

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
    # v1.2: Loopback-Status melden
    active_aplay = sum(1 for p in _aplay_processes if p.poll() is None)
    return jsonify({
        "status": "ok",
        "service": "birdnet-receiver",
        "version": "1.2",
        "wav_files": wav_count,
        "loopback_enabled": LOOPBACK_ENABLED,
        "loopback_device": LOOPBACK_DEVICE,
        "active_aplay_processes": active_aplay,
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
# ROUTEN – Neu in v1.1: Config & Voltage API
# ============================================================

@app.route('/config', methods=['GET'])
def get_config():
    """ESP32 holt sich hier die aktuelle Konfiguration."""
    cfg = load_config()
    logger.info("Config an ESP32 ausgeliefert")
    return jsonify(cfg), 200


@app.route('/config', methods=['POST'])
def update_config():
    """Dashboard sendet neue Konfiguration."""
    new_cfg = request.get_json()
    if not new_cfg:
        return jsonify({"error": "Kein JSON empfangen"}), 400

    # Aktuelle Config laden
    cfg = load_config()

    # Nur bekannte Keys uebernehmen (Sicherheit)
    for key in DEFAULT_CONFIG:
        if key in new_cfg:
            cfg[key] = new_cfg[key]

    save_config(cfg)
    return jsonify({"status": "ok", "config": cfg}), 200


@app.route('/api/voltage', methods=['GET'])
def get_voltage():
    """Spannungsdaten fuer Dashboard (mit Zeitfilter)."""
    hours = request.args.get('hours', 24, type=int)

    if not VOLTAGE_LOG.exists():
        return jsonify({"entries": [], "current": None, "stats": None})

    try:
        entries = json.loads(VOLTAGE_LOG.read_text())
    except json.JSONDecodeError:
        return jsonify({"entries": [], "current": None, "stats": None})

    # Nach Zeitraum filtern
    cutoff = time.time() - (hours * 3600)
    filtered = []
    for e in entries:
        try:
            ts = time.mktime(time.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S"))
            if ts > cutoff:
                filtered.append(e)
        except (ValueError, KeyError):
            continue

    current = filtered[-1] if filtered else None
    stats = None
    if filtered:
        voltages = [e["voltage"] for e in filtered]
        stats = {
            "min": round(min(voltages), 3),
            "max": round(max(voltages), 3),
            "avg": round(sum(voltages) / len(voltages), 3),
            "count": len(voltages)
        }

    return jsonify({
        "entries": filtered,
        "current": current,
        "stats": stats
    }), 200


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Config-API fuer Dashboard (Alias)."""
    return get_config()


@app.route('/api/config', methods=['POST'])
def api_update_config():
    """Config-API fuer Dashboard (Alias)."""
    return update_config()

# ============================================================
# START
# ============================================================

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("  BirdNET WAV-Empfaenger v1.2")
    logger.info(f"  http://{HOST}:{PORT}")
    logger.info(f"  Speicherort: {STREAM_DATA_DIR}")
    logger.info(f"  Config: {CONFIG_FILE}")
    logger.info(f"  Voltage-Log: {VOLTAGE_LOG}")
    logger.info(f"  Loopback: {LOOPBACK_DEVICE} ({'AN' if LOOPBACK_ENABLED else 'AUS'})")
    logger.info("=" * 50)

    app.run(host=HOST, port=PORT, debug=False)