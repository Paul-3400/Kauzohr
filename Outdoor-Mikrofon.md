# 🦉 Kauzohr – BirdNET Outdoor-Mikrofon

> Built as a "brain gym" project – keeping the mind sharp through electronics and code. 🧠💪  
> by Paul and Claude, Anthropic 2026

## 🎯 Projektziel

Ein solarbetriebenes, autonomes Outdoor-Mikrofon, das Vogelstimmen aufnimmt und zur Analyse an einen Raspberry Pi mit [BirdNET-Pi Enhanced Version](https://github.com/zach7036/BirdNET-Pi-Enhanced-Version) sendet.

**Kernidee:** Der ESP32-S3 nimmt 20 Sekunden Audio auf, verarbeitet es (Hochpass, Gain, Noise Gate) und sendet die WAV-Datei per WiFi/HTTP an den Raspberry Pi. BirdNET analysiert automatisch.

---

## 🏗️ Architektur

```
☀️ Solarpanel 5V/5W
        │
        ▼
┌───────────────┐
│   TP4056      │ ← Laderegler mit DW01 Schutzbeschaltung
│   + DW01      │   (Tiefentladung, Überladung, Kurzschluss)
└───────┬───────┘
        │ BAT+ / BAT-
        ▼
┌───────────────┐
│  21700 Li-Ion │ ← 5000 mAh, kälteresistent
│  3.7V/5000mAh│
└───────┬───────┘
        │ BAT+ / BAT-
        ▼
┌───────────────────────────────┐
│  Seeed XIAO ESP32-S3          │
│  - 240 MHz Dual-Core          │
│  - 8 MB PSRAM                 │
│  - WiFi 802.11 b/g/n          │
│                               │
│  GPIO1 (SCK) ──→ INMP441     │
│  GPIO2 (WS)  ──→ INMP441     │
│  GPIO3 (SD)  ──→ INMP441     │
│  3V3         ──→ INMP441 VDD │
│  GND         ──→ INMP441 GND │
│  GND         ──→ INMP441 L/R │
└───────────────────────────────┘
        │ WiFi (HTTP POST)
        ▼
┌───────────────────────────────┐
│  Raspberry Pi 4B              │
│  - BirdNET-Pi Enhanced        │
│  - Python Flask Empfänger     │
│  - Fixe IP: 10.0.1.196       │
│  - Port 5000                  │
│  - ~/BirdSongs/StreamData/    │
└───────────────────────────────┘
```

---

## 📦 Hardware – Stückliste (BOM)

| Komponente | Typ | Bezugsquelle | ca. Preis |
|---|---|---|---|
| Mikrocontroller | Seeed XIAO ESP32-S3 (8MB PSRAM) | Seeed Studio | CHF 12 |
| Mikrofon | INMP441 I2S MEMS Breakout | AliExpress/Amazon | CHF 5 |
| Laderegler | TP4056 mit DW01 Schutzschaltung | AliExpress | CHF 2 |
| Akku | 21700 Li-Ion, 3.7V, 5000 mAh | Akkushop | CHF 12 |
| Solarpanel | 5V / 5W | Amazon | CHF 15 |
| Kondensator | 100 nF (keramisch) | Elektronikladen | CHF 0.50 |
| Kabel | Dupont-Kabel / Litze | - | CHF 3 |
| Kleber | Araldit Rapid (Zugentlastung) | Baumarkt | CHF 8 |

**Gesamtkosten:** ~CHF 58

---

## 🔌 Verdrahtung ESP32-S3 ↔ INMP441

| XIAO ESP32-S3 Pin | INMP441 Pin | Kabelfarbe | Funktion |
|---|---|---|---|
| **3V3** | VDD | 🔴 Rot | Stromversorgung |
| **GND** | GND | ⚫ Schwarz | Masse |
| **GND** | L/R | ⚫ Schwarz | Links-Kanal (Mono) |
| **GPIO1 (D0)** | SCK | 🔵 Blau | Bit Clock (I2S) |
| **GPIO2 (D1)** | WS | 🟢 Grün | Word Select (I2S) |
| **GPIO3 (D2)** | SD | 🟠 Orange | Serial Data (I2S) |

> ⚠️ **Wichtig:** 100nF Kondensator zwischen VDD und GND direkt am INMP441 anlöten (Entkopplung).

### Stromversorgung

```
Solar 5V/5W ──→ TP4056 IN+ / IN-
TP4056 BAT+ / BAT- ──→ 21700 Akku (5000 mAh)
21700 Akku ──→ XIAO ESP32-S3 BAT+ / BAT- (Pads auf Unterseite)
```

> 💡 **Zugentlastung:** Batterie-Drähte am XIAO mit Araldit Rapid fixieren (Lötstellen entlasten).

---

## ⚙️ Firmware – Konfiguration

Alle anpassbaren Parameter stehen zentral am Anfang von `src/main.cpp`:

### Zeitsteuerung

| Konstante | Standardwert | Beschreibung |
|---|---|---|
| `ACTIVE_HOUR_START` | 4 | Betriebsbeginn (Stunde, 0-23) |
| `ACTIVE_HOUR_END` | 22 | Betriebsende (Stunde, 0-23) |
| `RECORD_DURATION_SEC` | 20 | Aufnahmedauer pro Zyklus (Sekunden) |
| `DEEP_SLEEP_SEC` | 5 | Pause zwischen Zyklen (Sekunden) |
| `WIFI_TIMEOUT_MS` | 10000 | Max. Wartezeit WiFi-Verbindung (ms) |
| `POST_TIMEOUT_MS` | 5000 | Max. Wartezeit HTTP-Antwort (ms) |

### Audio-Verarbeitung

| Konstante | Standardwert | Beschreibung |
|---|---|---|
| `GAIN` | 2.0 | Digitale Verstärkung (1.0 = neutral, 2.0 = doppelt) |
| `NOISE_THRESHOLD` | 500 | Noise Gate Schwelle (0 = deaktiviert) |
| `HP_FILTER_ALPHA` | 0.98 | Hochpassfilter (~150 Hz Grenzfrequenz bei 48 kHz) |
| `USE_NOISE_GATE` | true | Noise Gate ein/aus |
| `USE_HP_FILTER` | true | Hochpassfilter ein/aus (entfernt Wind/Verkehr) |

### Audio-Format

| Konstante | Standardwert | Beschreibung |
|---|---|---|
| `SAMPLE_RATE` | 48000 | Abtastrate in Hz |
| `SAMPLE_BITS` | 16 | Bit-Tiefe |
| `CHANNELS` | 1 | Mono |

### Netzwerk

| Konstante | Standardwert | Beschreibung |
|---|---|---|
| `WIFI_SSID` | "RoPa Net" | WLAN-Name |
| `WIFI_PASSWORD` | "..." | WLAN-Passwort |
| `PI_SERVER_IP` | "10.0.1.196" | IP-Adresse des Raspberry Pi (fest!) |
| `PI_SERVER_PORT` | 5000 | Port des Flask-Empfängers |
| `PI_ENDPOINT` | "/upload" | Upload-Pfad |

### NTP (Zeitserver)

| Konstante | Standardwert | Beschreibung |
|---|---|---|
| `NTP_SERVER` | "pool.ntp.org" | Zeitserver |
| `NTP_GMT_OFFSET` | 3600 | UTC+1 (MEZ Winterzeit) |
| `NTP_DAYLIGHT_OFFSET` | 3600 | +1h Sommerzeit (MESZ) |

### Hardware Pins

| Konstante | Standardwert | Beschreibung |
|---|---|---|
| `I2S_SCK` | GPIO_NUM_1 | I2S Bit Clock → INMP441 SCK |
| `I2S_WS` | GPIO_NUM_2 | I2S Word Select → INMP441 WS |
| `I2S_SD` | GPIO_NUM_3 | I2S Serial Data → INMP441 SD |

---

## 🔄 Betriebszyklus

```
Wake up → WiFi → NTP → Zeitcheck
                            │
              ┌─────────────┼─────────────┐
              │ Nacht       │ Tag         │
              │ (22-04)     │ (04-22)     │
              ▼             ▼             │
         Long Sleep    WiFi OFF           │
         bis 04:00     I2S Aufnahme 20s   │
                            │             │
                       Hochpassfilter      │
                       Gain ×2            │
                       Noise Gate         │
                            │             │
                    ┌───────┴───────┐     │
                    │ Stille        │ Audio│
                    ▼               ▼     │
               Deep Sleep      WiFi ON    │
               5 Sek           HTTP POST  │
                               WAV → Pi   │
                                    │     │
                               Deep Sleep │
                               5 Sek      │
```

---

## 🖥️ Raspberry Pi – Empfänger einrichten

### Voraussetzungen

- Raspberry Pi 4B mit Raspberry Pi OS (Bookworm)
- [BirdNET-Pi Enhanced Version](https://github.com/zach7036/BirdNET-Pi-Enhanced-Version) installiert
- WiFi-Verbindung im selben Netzwerk wie ESP32

### 1. Feste IP-Adresse einrichten

```bash
# Verbindungsnamen herausfinden
sudo nmcli con show

# Feste IP setzen (Verbindungsnamen anpassen!)
sudo nmcli con mod "netplan-wlan0-RoPa Net" \
  ipv4.addresses 10.0.1.196/24 \
  ipv4.gateway 10.0.1.1 \
  ipv4.dns "10.0.1.1" \
  ipv4.method manual

# Verbindung neu laden
sudo nmcli con up "netplan-wlan0-RoPa Net"

# Prüfen
ip addr show wlan0 | grep "inet "
```

### 2. Python-Empfänger installieren

```bash
# Verzeichnis erstellen
mkdir -p ~/birdnet-receiver
cd ~/birdnet-receiver

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Flask installieren
pip install flask
```

### 3. Empfänger-Skript erstellen

```bash
nano -lmi ~/birdnet-receiver/receiver.py
```

Inhalt von `receiver.py` – siehe [receiver.py](receiver.py) im Repository.

**Kernfunktion:**
- Lauscht auf Port 5000, Endpoint `/upload`
- Empfängt WAV-Daten vom ESP32
- Validiert WAV-Header
- Speichert mit Zeitstempel in `~/BirdSongs/StreamData/`
- BirdNET erkennt neue Dateien automatisch und analysiert sie

### 4. Systemd-Service (Autostart)

```bash
sudo nano -lmi /etc/systemd/system/birdnet_receiver.service
```

Inhalt:

```ini
[Unit]
Description=BirdNET WAV-Empfaenger (ESP32 Outdoor-Mikrofon)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=paul-rppi
WorkingDirectory=/home/paul-rppi/birdnet-receiver
ExecStart=/home/paul-rppi/birdnet-receiver/venv/bin/python receiver.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable birdnet_receiver
sudo systemctl start birdnet_receiver
sudo systemctl status birdnet_receiver --no-pager
```

### 5. Testen

```bash
# Health-Check
curl http://10.0.1.196:5000/health

# Statistiken
curl http://10.0.1.196:5000/stats

# Live-Log beobachten
sudo journalctl -u birdnet_receiver -f
```

---

## 🔋 Energiebilanz

### Stromverbrauch pro Phase

| Phase | Strom (mA) | Dauer |
|---|---|---|
| Deep Sleep | 0.01 | 5s |
| WiFi Connect + NTP | 120 | ~3s |
| Aufnahme (WiFi off) | 25 | 20s |
| Audio-Verarbeitung | 80 | <0.5s |
| WiFi POST | 120 | ~2s |

### Betriebsvarianten

| Variante | Zeiten | Aufnahme | Sleep | Audio-Abdeckung | Tagesverbrauch |
|---|---|---|---|---|---|
| **A** (24/7) | 00-24 | 15s | 12s | 51.7% | ~857 mAh |
| **B** (empfohlen) | 04-22 | 20s | 5s | 74.1% | ~840 mAh |
| **C** (max) | 04-22 | 20s | 0s | 90.9% | ~1031 mAh |

### Akku-Autonomie (5000 mAh, Variante B)

| Saison | Solar-Ertrag | Bilanz | Puffer ohne Sonne |
|---|---|---|---|
| Sommer | ~1000 mAh/Tag | +160 mAh | ∞ |
| Frühling/Herbst | ~600 mAh/Tag | -240 mAh | ~20 Tage |
| Winter | ~300 mAh/Tag | -540 mAh | ~9 Tage |

---

## 🛠️ Entwicklungsumgebung

| Tool | Verwendung |
|---|---|
| **VS Code + PlatformIO** | Firmware-Entwicklung (Mac) |
| **Raspberry Pi Connect** | Remote Shell zum Pi |
| **nano -lmi** | Editor auf dem Pi |
| **GitHub** | Versionskontrolle |
| **Typora** | Markdown-Dokumentation |

### PlatformIO Konfiguration (`platformio.ini`)

```ini
[env:seeed_xiao_esp32s3]
platform = espressif32
board = seeed_xiao_esp32s3
framework = arduino
monitor_speed = 115200
board_build.arduino.memory_type = qio_opi
```

---

## 📊 Speicherbedarf

| Parameter | Wert |
|---|---|
| Sample Rate | 48'000 Hz |
| Bit-Tiefe | 16 bit (2 Bytes) |
| Aufnahmedauer | 20 Sekunden |
| **Buffer-Grösse** | **1'920'000 Bytes (1.83 MB)** |
| PSRAM verfügbar | 8'386'295 Bytes (~8 MB) |
| **Auslastung** | **~23%** (inkl. 15% Reserve: ~29%) |
| Max. mögliche Aufnahme | ~67.9 Sekunden |

---

## 📁 Projektstruktur

```
birdnet-outdoor-mic/
├── src/
│   └── main.cpp              ← Firmware (alle Konstanten oben)
├── platformio.ini            ← Board-Konfiguration
├── README.md                 ← Diese Datei
├── receiver.py               ← Python-Empfänger für den Pi
└── docs/
    └── Handover.md           ← Übergabe-Dokumentation
```

---

## 🧪 Hardware-Tests (Reihenfolge)

Vor der Inbetriebnahme diese Tests durchführen:

1. **USB-Verbindung:** `ls /dev/cu.usb*` am Mac
2. **Blink-Test:** LED auf GPIO21 blinkt
3. **Serial Monitor:** 115200 Baud, Ausgabe sichtbar
4. **WiFi-Scan:** Netzwerke werden gefunden
5. **Mikrofon-Test:** I2S liefert Samples, Peak-Werte reagieren auf Geräusche
6. **Akku-Test:** ESP32 läuft ohne USB, nur via BAT-Pins
7. **Solar-Test:** TP4056 Lade-LED leuchtet bei Sonne

---

## 📜 Lizenz

Open Source – MIT License

---

## 🙏 Credits

- [BirdNET-Pi Enhanced Version](https://github.com/zach7036/BirdNET-Pi-Enhanced-Version) by zach7036
- [BirdNET](https://github.com/birdnet-team) by Cornell Lab of Ornithology
- [Seeed XIAO ESP32-S3](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)
- [INMP441 Datenblatt](https://invensense.tdk.com/products/digital/inmp441/)
