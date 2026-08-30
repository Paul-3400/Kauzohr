#!/usr/bin/env python3
# ============================================================
# BirdNET Outdoor-Mikrofon – Battery & Config Dashboard
# ============================================================
# Separates Web-Dashboard für:
#   - Batteriespannung (Echtzeit + Verlauf)
#   - ESP32 Remote-Konfiguration
#
# Läuft als eigener Service auf Port 5001
# Liest Daten vom receiver.py (Port 5000)
#
# Built as a "brain gym" project – keeping the mind sharp
# through electronics and code. 🧠💪
# by Paul and Claude (Anthropic Claude, 2026)
# ============================================================

import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

# ============================================================
# KONFIGURATION
# ============================================================

HOST = "0.0.0.0"
PORT = 5001

# Gleiche Pfade wie receiver.py
RECEIVER_DIR = Path.home() / "birdnet-receiver"
VOLTAGE_LOG = RECEIVER_DIR / "voltage_log.json"
CONFIG_FILE = RECEIVER_DIR / "config.json"

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

# ============================================================
# HTML TEMPLATE
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BirdNET Battery & Config</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f0f1a;
            color: #e0e0e0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 16px;
            border: 1px solid #2a2a4a;
        }
        .header h1 { font-size: 1.8em; margin-bottom: 5px; }
        .header .subtitle { color: #888; font-size: 0.9em; }

        /* Stat Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #2a2a4a;
            transition: border-color 0.3s;
        }
        .stat-card:hover { border-color: #4caf50; }
        .stat-value { font-size: 2.2em; font-weight: 700; }
        .stat-label { color: #888; margin-top: 5px; font-size: 0.85em; }
        .voltage-good { color: #4caf50; }
        .voltage-warn { color: #ff9800; }
        .voltage-crit { color: #f44336; }
        .voltage-charge { color: #2196f3; }

        /* Chart */
        .chart-container {
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid #2a2a4a;
        }
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .chart-header h2 { font-size: 1.1em; }
        .time-buttons button {
            background: #2a2a4a;
            color: #ccc;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            margin-left: 5px;
            font-size: 0.85em;
        }
        .time-buttons button.active {
            background: #4caf50;
            color: #fff;
        }

        /* Config Panel */
        .config-panel {
            background: #16213e;
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #2a2a4a;
        }
        .config-panel h2 { margin-bottom: 20px; font-size: 1.1em; }
        .config-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }
        .config-section h3 {
            font-size: 0.95em;
            color: #4caf50;
            margin-bottom: 12px;
            padding-bottom: 5px;
            border-bottom: 1px solid #2a2a4a;
        }
        .config-field {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding: 8px 0;
        }
        .config-field label {
            color: #bbb;
            font-size: 0.9em;
            flex: 1;
        }
        .config-field input[type="number"] {
            width: 100px;
            background: #0f0f1a;
            border: 1px solid #3a3a5a;
            color: #e0e0e0;
            padding: 8px 10px;
            border-radius: 6px;
            text-align: right;
            font-size: 0.9em;
        }
        .config-field input[type="number"]:focus {
            outline: none;
            border-color: #4caf50;
        }

        /* Toggle Switch */
        .toggle {
            position: relative;
            width: 48px;
            height: 26px;
        }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .toggle .slider {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: #3a3a5a;
            border-radius: 26px;
            cursor: pointer;
            transition: 0.3s;
        }
        .toggle .slider:before {
            content: "";
            position: absolute;
            width: 20px; height: 20px;
            left: 3px; bottom: 3px;
            background: #ccc;
            border-radius: 50%;
            transition: 0.3s;
        }
        .toggle input:checked + .slider { background: #4caf50; }
        .toggle input:checked + .slider:before { transform: translateX(22px); }

        /* Buttons */
        .btn-save {
            display: block;
            width: 100%;
            max-width: 300px;
            margin: 25px auto 0;
            padding: 12px;
            background: #4caf50;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn-save:hover { background: #45a049; }
        .btn-save:active { background: #388e3c; }

        .save-status {
            text-align: center;
            margin-top: 12px;
            font-size: 0.9em;
            min-height: 1.5em;
        }
        .config-meta {
            text-align: center;
            color: #555;
            font-size: 0.8em;
            margin-top: 15px;
        }
        .refresh-info {
            text-align: center;
            color: #444;
            margin-top: 15px;
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <!-- ===== HEADER ===== -->
    <div class="header">
        <h1>&#x1f50b; BirdNET Battery &amp; Config</h1>
        <div class="subtitle">XIAO ESP32-S3 &middot; 21700 Li-Ion 5000mAh &middot; Solar 5W &middot; TP4056</div>
    </div>

    <!-- ===== STAT CARDS ===== -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" id="currentV">--</div>
            <div class="stat-label">Aktuelle Spannung (V)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="socPercent">--</div>
            <div class="stat-label">Ladezustand (%)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="minV">--</div>
            <div class="stat-label">Min</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="maxV">--</div>
            <div class="stat-label">Max</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="avgV">--</div>
            <div class="stat-label">Durchschnitt</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="countV">--</div>
            <div class="stat-label">Messungen</div>
        </div>
    </div>

    <!-- ===== CHART ===== -->
    <div class="chart-container">
        <div class="chart-header">
            <h2>&#x1f4c8; Spannungsverlauf</h2>
            <div class="time-buttons">
                <button onclick="setHours(6)" id="btn6h">6h</button>
                <button onclick="setHours(12)" id="btn12h">12h</button>
                <button onclick="setHours(24)" id="btn24h" class="active">24h</button>
                <button onclick="setHours(72)" id="btn72h">3 Tage</button>
                <button onclick="setHours(168)" id="btn168h">7 Tage</button>
            </div>
        </div>
        <canvas id="voltageChart"></canvas>
    </div>

    <!-- ===== CONFIG PANEL ===== -->
    <div class="config-panel">
        <h2>&#x2699;&#xfe0f; ESP32 Konfiguration (Remote)</h2>
        <div class="config-grid">
            <div class="config-section">
                <h3>&#x23f0; Zeitsteuerung</h3>
                <div class="config-field">
                    <label>Betrieb ab (Stunde)</label>
                    <input type="number" id="active_hour_start" min="0" max="23">
                </div>
                <div class="config-field">
                    <label>Betrieb bis (Stunde)</label>
                    <input type="number" id="active_hour_end" min="0" max="23">
                </div>
                <div class="config-field">
                    <label>Aufnahmedauer (Sek)</label>
                    <input type="number" id="record_duration_sec" min="5" max="67">
                </div>
                <div class="config-field">
                    <label>Deep Sleep (Sek)</label>
                    <input type="number" id="deep_sleep_sec" min="0" max="60">
                </div>
                <div class="config-field">
                    <label>WiFi Timeout (ms)</label>
                    <input type="number" id="wifi_timeout_ms" min="5000" max="30000" step="1000">
                </div>
                <div class="config-field">
                    <label>POST Timeout (ms)</label>
                    <input type="number" id="post_timeout_ms" min="3000" max="15000" step="1000">
                </div>
            </div>

            <div class="config-section">
                <h3>&#x1f3a4; Audio-Verarbeitung</h3>
                <div class="config-field">
                    <label>Gain (Verst\u00e4rkung)</label>
                    <input type="number" id="gain" min="0.5" max="8.0" step="0.1">
                </div>
                <div class="config-field">
                    <label>Noise Threshold</label>
                    <input type="number" id="noise_threshold" min="0" max="5000" step="50">
                </div>
                <div class="config-field">
                    <label>HP Filter Alpha</label>
                    <input type="number" id="hp_filter_alpha" min="0.90" max="0.99" step="0.01">
                </div>
                <div class="config-field">
                    <label>Noise Gate</label>
                    <div class="toggle">
                        <input type="checkbox" id="use_noise_gate">
                        <span class="slider"></span>
                    </div>
                </div>
                <div class="config-field">
                    <label>Hochpassfilter</label>
                    <div class="toggle">
                        <input type="checkbox" id="use_hp_filter">
                        <span class="slider"></span>
                    </div>
                </div>
            </div>
        </div>

        <button class="btn-save" onclick="saveConfig()">&#x1f4be; Konfiguration speichern</button>
        <div class="save-status" id="saveStatus"></div>
        <div class="config-meta" id="configMeta"></div>
    </div>

    <div class="refresh-info">Spannungsdaten: Auto-Refresh alle 60 Sekunden</div>

    <!-- ===== JAVASCRIPT ===== -->
    <script>
        let chart = null;
        let currentHours = 24;

        // ----- Hilfsfunktionen -----
        function voltageToColor(v) {
            if (v >= 4.1) return 'voltage-charge';
            if (v >= 3.7) return 'voltage-good';
            if (v >= 3.4) return 'voltage-warn';
            return 'voltage-crit';
        }

        function voltageToSoC(v) {
            // Li-Ion N\u00e4herungskurve (21700)
            if (v >= 4.18) return 100;
            if (v <= 3.00) return 0;
            if (v >= 4.00) return Math.round(80 + (v - 4.00) / (4.18 - 4.00) * 20);
            if (v >= 3.70) return Math.round(30 + (v - 3.70) / (4.00 - 3.70) * 50);
            if (v >= 3.50) return Math.round(10 + (v - 3.50) / (3.70 - 3.50) * 20);
            return Math.round((v - 3.00) / (3.50 - 3.00) * 10);
        }

        // ----- Spannungsdaten laden -----
        async function fetchVoltage() {
            try {
                const resp = await fetch(`/api/voltage?hours=${currentHours}`);
                const data = await resp.json();

                if (data.current) {
                    const v = data.current.voltage;
                    const el = document.getElementById('currentV');
                    el.textContent = v.toFixed(3);
                    el.className = 'stat-value ' + voltageToColor(v);

                    const soc = voltageToSoC(v);
                    const socEl = document.getElementById('socPercent');
                    socEl.textContent = soc + '%';
                    socEl.className = 'stat-value ' + voltageToColor(v);
                }

                if (data.stats) {
                    document.getElementById('minV').textContent =
                        data.stats.min != null ? data.stats.min.toFixed(3) : '--';
                    document.getElementById('maxV').textContent =
                        data.stats.max != null ? data.stats.max.toFixed(3) : '--';
                    document.getElementById('avgV').textContent =
                        data.stats.avg != null ? data.stats.avg.toFixed(3) : '--';
                    document.getElementById('countV').textContent =
                        data.stats.count != null ? data.stats.count : '--';
                }

                updateChart(data.entries);
            } catch (err) {
                console.error('Voltage fetch error:', err);
            }
        }

        function updateChart(entries) {
            if (!entries || entries.length === 0) return;

            const step = Math.max(1, Math.floor(entries.length / 300));
            const sampled = entries.filter((_, i) => i % step === 0);

            const labels = sampled.map(e => {
                if (currentHours > 24) {
                    return e.timestamp.slice(5, 16);
                }
                return e.timestamp.slice(11, 16);
            });
            const values = sampled.map(e => e.voltage);

            if (chart) {
                chart.data.labels = labels;
                chart.data.datasets[0].data = values;
                chart.update('none');
            } else {
                const ctx = document.getElementById('voltageChart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Batteriespannung (V)',
                            data: values,
                            borderColor: '#4caf50',
                            backgroundColor: 'rgba(76, 175, 80, 0.08)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 0,
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        animation: false,
                        interaction: { intersect: false, mode: 'index' },
                        scales: {
                            y: {
                                min: 2.8, max: 4.4,
                                grid: { color: '#1a1a2e' },
                                ticks: { color: '#888', callback: v => v.toFixed(1) + 'V' }
                            },
                            x: {
                                grid: { color: '#1a1a2e' },
                                ticks: { color: '#888', maxTicksLimit: 12, maxRotation: 0 }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: ctx => ctx.parsed.y.toFixed(3) + 'V (' + voltageToSoC(ctx.parsed.y) + '%)'
                                }
                            }
                        }
                    }
                });
            }
        }

        function setHours(h) {
            currentHours = h;
            document.querySelectorAll('.time-buttons button').forEach(b => b.classList.remove('active'));
            document.getElementById('btn' + h + 'h').classList.add('active');
            fetchVoltage();
        }

        // ----- Konfiguration laden -----
        async function loadConfig() {
            try {
                const resp = await fetch('/api/config');
                const cfg = await resp.json();

                const fields = [
                    'active_hour_start', 'active_hour_end',
                    'record_duration_sec', 'deep_sleep_sec',
                    'wifi_timeout_ms', 'post_timeout_ms',
                    'gain', 'noise_threshold', 'hp_filter_alpha',
                    'use_noise_gate', 'use_hp_filter'
                ];

                for (const key of fields) {
                    const el = document.getElementById(key);
                    if (!el) continue;
                    if (el.type === 'checkbox') {
                        el.checked = cfg[key];
                    } else {
                        el.value = cfg[key];
                    }
                }

                if (cfg.updated_at) {
                    document.getElementById('configMeta').textContent =
                        'Letzte Aenderung: ' + cfg.updated_at +
                        ' (wirksam ab naechstem ESP32-Zyklus)';
                }
            } catch (err) {
                console.error('Config load error:', err);
            }
        }

        // ----- Konfiguration speichern -----
        async function saveConfig() {
            const numFields = [
                'active_hour_start', 'active_hour_end',
                'record_duration_sec', 'deep_sleep_sec',
                'wifi_timeout_ms', 'post_timeout_ms',
                'noise_threshold'
            ];
            const floatFields = ['gain', 'hp_filter_alpha'];
            const boolFields = ['use_noise_gate', 'use_hp_filter'];

            const cfg = {};
            for (const key of numFields) {
                cfg[key] = parseInt(document.getElementById(key).value);
            }
            for (const key of floatFields) {
                cfg[key] = parseFloat(document.getElementById(key).value);
            }
            for (const key of boolFields) {
                cfg[key] = document.getElementById(key).checked;
            }

            if (cfg.active_hour_start >= cfg.active_hour_end) {
                showStatus('Startzeit muss vor Endzeit liegen!', false);
                return;
            }
            if (cfg.record_duration_sec > 67) {
                showStatus('Max. Aufnahmedauer: 67 Sekunden (PSRAM-Limit)', false);
                return;
            }

            try {
                const resp = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(cfg)
                });
                const result = await resp.json();

                if (result.status === 'ok') {
                    showStatus('Gespeichert! Wirksam ab naechstem ESP32-Zyklus.', true);
                    loadConfig();
                } else {
                    showStatus('Fehler: ' + (result.error || 'Unbekannt'), false);
                }
            } catch (err) {
                showStatus('Netzwerkfehler: ' + err.message, false);
            }
        }

        function showStatus(msg, success) {
            const el = document.getElementById('saveStatus');
            el.textContent = (success ? '\u2705 ' : '\u274c ') + msg;
            el.style.color = success ? '#4caf50' : '#f44336';
            setTimeout(() => { el.textContent = ''; }, 5000);
        }

        // ----- Init -----
        fetchVoltage();
        loadConfig();
        setInterval(fetchVoltage, 60000);
    </script>
</body>
</html>
"""

# ============================================================
# HILFSFUNKTIONEN
# ============================================================

import time


def load_config():
    """Konfiguration aus JSON laden."""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        logger.error("Config JSON fehlerhaft")
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """Konfiguration in JSON speichern."""
    cfg["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    logger.info("Config gespeichert")

# ============================================================
# ROUTEN
# ============================================================

@app.route('/')
def dashboard():
    """Haupt-Dashboard."""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/voltage', methods=['GET'])
def api_voltage():
    """Spannungsdaten mit Zeitfilter."""
    hours = request.args.get('hours', 24, type=int)

    if not VOLTAGE_LOG.exists():
        return jsonify({"entries": [], "current": None, "stats": None})

    try:
        entries = json.loads(VOLTAGE_LOG.read_text())
    except json.JSONDecodeError:
        return jsonify({"entries": [], "current": None, "stats": None})

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

    return jsonify({"entries": filtered, "current": current, "stats": stats})


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Aktuelle Config liefern."""
    return jsonify(load_config())


@app.route('/api/config', methods=['POST'])
def api_update_config():
    """Config aktualisieren."""
    new_cfg = request.get_json()
    if not new_cfg:
        return jsonify({"error": "Kein JSON"}), 400

    cfg = load_config()
    for key in DEFAULT_CONFIG:
        if key in new_cfg:
            cfg[key] = new_cfg[key]

    save_config(cfg)
    return jsonify({"status": "ok", "config": cfg})

# ============================================================
# START
# ============================================================

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("  BirdNET Battery & Config Dashboard")
    logger.info(f"  http://{HOST}:{PORT}")
    logger.info("=" * 50)

    app.run(host=HOST, port=PORT, debug=False)
