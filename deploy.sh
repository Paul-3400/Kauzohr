#!/bin/bash
# ============================================================
# BirdNET Kauzohr – Deploy Script v1.1
# ============================================================
# Erstellt von Paul mit Claude (Anthropic Claude, 2026)
#
# Dieses Script deployed receiver.py v1.1 und dashboard.py
# auf den Raspberry Pi.
#
# Voraussetzung: Dateien liegen im gleichen Ordner wie dieses Script
# ============================================================

set -e  # Bei Fehler abbrechen

echo ""
echo "================================================"
echo "  🐦 BirdNET Kauzohr – Deploy v1.1"
echo "================================================"
echo ""

# ----- Verzeichnisse -----
RECEIVER_DIR="$HOME/birdnet-receiver"
VENV_DIR="$RECEIVER_DIR/venv"

echo "📁 Prüfe Verzeichnisse..."
mkdir -p "$RECEIVER_DIR"
mkdir -p "$HOME/BirdSongs/StreamData"

# ----- Virtual Environment -----
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Erstelle Python venv..."
    python3 -m venv "$VENV_DIR"
    echo "   ✅ venv erstellt"
fi

echo "📦 Installiere/aktualisiere Flask..."
"$VENV_DIR/bin/pip" install --quiet --upgrade flask
echo "   ✅ Flask installiert"

# ----- Dateien kopieren -----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "📄 Kopiere Dateien..."

if [ -f "$SCRIPT_DIR/receiver.py" ]; then
    cp "$SCRIPT_DIR/receiver.py" "$RECEIVER_DIR/receiver.py"
    echo "   ✅ receiver.py → $RECEIVER_DIR/"
else
    echo "   ❌ receiver.py nicht gefunden in $SCRIPT_DIR!"
    exit 1
fi

if [ -f "$SCRIPT_DIR/dashboard.py" ]; then
    cp "$SCRIPT_DIR/dashboard.py" "$RECEIVER_DIR/dashboard.py"
    echo "   ✅ dashboard.py → $RECEIVER_DIR/"
else
    echo "   ❌ dashboard.py nicht gefunden in $SCRIPT_DIR!"
    exit 1
fi

# ----- Systemd Services -----
echo ""
echo "⚙️  Installiere Systemd Services..."

# Receiver Service
sudo tee /etc/systemd/system/birdnet_receiver.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=BirdNET WAV Receiver v1.1
After=network.target

[Service]
Type=simple
User=paul-rppi
WorkingDirectory=/home/paul-rppi/birdnet-receiver
ExecStart=/home/paul-rppi/birdnet-receiver/venv/bin/python receiver.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICEEOF
echo "   ✅ birdnet_receiver.service"

# Dashboard Service
sudo tee /etc/systemd/system/birdnet_dashboard.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=BirdNET Battery & Config Dashboard
After=network.target birdnet_receiver.service

[Service]
Type=simple
User=paul-rppi
WorkingDirectory=/home/paul-rppi/birdnet-receiver
ExecStart=/home/paul-rppi/birdnet-receiver/venv/bin/python dashboard.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICEEOF
echo "   ✅ birdnet_dashboard.service"

# ----- Services starten -----
echo ""
echo "🔄 Lade Systemd und starte Services..."

sudo systemctl daemon-reload

sudo systemctl stop birdnet_receiver.service 2>/dev/null || true
sudo systemctl stop birdnet_dashboard.service 2>/dev/null || true

sudo systemctl enable birdnet_receiver.service
sudo systemctl enable birdnet_dashboard.service

sudo systemctl start birdnet_receiver.service
sudo systemctl start birdnet_dashboard.service

echo ""
echo "================================================"
echo "  ✅ Deploy erfolgreich!"
echo "================================================"
echo ""
echo "  📡 Receiver:  http://$(hostname -I | awk '{print $1}'):5000"
echo "  📊 Dashboard: http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "  Prüfe Status mit:"
echo "    sudo systemctl status birdnet_receiver"
echo "    sudo systemctl status birdnet_dashboard"
echo ""
echo "  Logs anschauen:"
echo "    journalctl -u birdnet_receiver -f"
echo "    journalctl -u birdnet_dashboard -f"
echo ""
