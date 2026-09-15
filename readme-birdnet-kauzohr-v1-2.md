# 🦉 BirdNET Kauzohr – 24/7 Vogelstimmen-Recorder

**Eine solarbetriebene Outdoor-Audiostation zur automatischen Aufnahme und Analyse von Vogelstimmen.**

> Entwickelt von Paul Simmen (Paul-3400) in Burgdorf, Schweiz 🇨🇭
> Als kreatives Brain-Gym-Projekt – Technik trifft Natur! 🧠💪
> **Autor:** Paul Simmen mit Vibe (GLM-5-2), 15.09.2026

---

## 📋 Inhaltsverzeichnis

- [Überblick](#-überblick)
- [Systemarchitektur](#-systemarchitektur)
- [Hardware-Komponenten](#-hardware-komponenten)
- [Elektrische Verbindungen](#-elektrische-verbindungen)
- [Software-Komponenten](#-software-komponenten)
- [Installation Raspberry Pi](#-installation-raspberry-pi)
- [Installation ESP32-S3 Firmware](#-installation-esp32-s3-firmware)
- [BirdNET-Go Integration](#-birdnet-go-integration)
- [Dashboard bedienen](#-dashboard-bedienen)
- [Betrieb & Wartung](#-betrieb--wartung)
- [Automatische Speicherbereinigung (Wochenputz)](#-automatische-speicherbereinigung-wochenputz)
- [Projektstruktur](#-projektstruktur)
- [Fehlerbehebung](#-fehlerbehebung)
- [Lizenz](#-lizenz)

---

## 🎯 Überblick

Das **Kauzohr** ist ein **autonomes Aufnahmesystem für Vogelstimmen**. Ein wetterfestes Mikrofon-Modul im Garten nimmt rund um die Uhr Audio auf und sendet die Aufnahmen per WLAN an einen Raspberry Pi im Haus. Dort werden die WAV-Dateien gespeichert und in **Echtzeit an BirdNET-Go (Docker)** weitergegeben. BirdNET-Go analysiert die Aufnahmen und erkennt Vogelarten.

### ✨ Funktionen

| Funktion | Beschreibung |
|---|---|
| 🎙️ **Automatische Aufnahme** | 20-Sekunden-Zyklen mit konfigurierbarer Dauer (5–30s) |
| 🔋 **Batterie-Überwachung** | Spannungsmessung via Spannungsteiler, Live-Anzeige im Dashboard, **kalibriert** (Faktor 1.0548) |
| ☀️ **Solarbetrieben** | 5W Solarpanel + TP4056 Laderegler + 21700 Li-Ion Akku (5000mAh) |
| 📡 **Remote-Konfiguration** | Alle Parameter über Web-Dashboard einstellbar |
| 🔇 **Intelligente Stille-Erkennung** | Noise Gate filtert leere Aufnahmen aus |
| 🔧 **Audio-Processing** | Hochpassfilter + einstellbare Verstärkung direkt auf dem ESP |
| ⏰ **Zeitsteuerung** | Konfigurierbare Betriebszeiten (z.B. 04:00–22:00) |
| 💤 **Deep Sleep** | Minimaler Stromverbrauch zwischen den Aufnahmen |
| 📊 **Web-Dashboard** | Spannungsverlauf, Ladezustand, alle Einstellungen im Browser |
| 🐳 **BirdNET-Go Integration** | Echtzeit-Vogelerkennung mit Docker |
| 🗑️ **Automatischer Wochenputz** | Löscht alte WAV-Dateien (>7 Tage) via Cronjob |

---

## 🏗️ Systemarchitektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OUTDOOR (Garten)                             │
│                                                                     │
│   ☀️ Solarpanel 5W                                                  │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────┐     ┌───────────────────────────────────┐           │
│   │  TP4056  │────▶│  21700 Li-Ion Akku (5000mAh)     │           │
│   │  Lader   │     └──────────┬────────────────────────┘           │
│   └──────────┘                │                                     │
│                               │ 3.0V – 4.2V                        │
│                               ▼                                     │
│                    ┌─────────────────────┐                          │
│                    │  XIAO ESP32-S3      │                          │
│                    │                     │                          │
│                    │  🎙️ INMP441 (I2S)   │                          │
│                    │  🔋 ADC auf A3      │                          │
│                    │  📶 WiFi 2.4GHz     │                          │
│                    └─────────┬───────────┘                          │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ WiFi (HTTP)
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        INDOOR (Haus)                                 │
│                                                                      │
│   ┌───────────────────────┐    ┌─────────────────────────────────┐  │
│   │  Raspberry Pi 4B       │    │  Docker Container: BirdNET-Go   │  │
│   │                       │    │  (Port 8080)                     │  │
│   │  📥 receiver.py        │    │  🔍 Vogelarten-Erkennung        │  │
│   │    (Port 5000)         │    │  📊 Dashboard (Port 8080/ui)     │  │
│   │                       │    │  💾 /data/clips/                 │  │
│   │  📊 dashboard.py       │    │  (Analysierte Dateien)           │  │
│   │    (Port 5001)         │    └─────────────────────────────────┘  │
│   │                       │                                        │
│   │  💾 ~/BirdSongs/      │                                        │
│   │    StreamData/*.wav   │──────────────────────────────────────▶│
│   └───────────────────────┘                                        │
│                                                                      │
│   Browser: http://<Pi-IP>:5001 (Dashboard) / :8080/ui (BirdNET-Go)     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Hardware-Komponenten

### Einkaufsliste

| Komponente | Typ | Funktion | ca. Preis |
|---|---|---|---|
| Mikrocontroller | **Seeed XIAO ESP32-S3** | Aufnahme, Processing, WiFi | CHF 10.– |
| Mikrofon | **INMP441** (I2S MEMS) | Digitales Mikrofon | CHF 5.– |
| Akku | **21700 Li-Ion** (5000mAh) | Energiespeicher | CHF 8.– |
| Laderegler | **TP4056** (USB-C Variante) | Solar-Lademanagement | CHF 3.– |
| Solarpanel | **5W, 6V** | Energiequelle | CHF 15.– |
| Widerstände | **2× 200kΩ** (1% Toleranz empfohlen) | Spannungsteiler für ADC | CHF 1.– |
| Server | **Raspberry Pi 4B** (2GB+ RAM) | Empfänger, Dashboard, Speicher, Docker-Host | CHF 50.– |
| Gehäuse | Wetterfeste Box (IP65+) | Schutz der Elektronik | CHF 10.– |
| Kleinmaterial | Kabel, Lötzinn, Stecker | Verbindungen | CHF 5.– |

**Gesamtkosten: ca. CHF 100.–**

---

## ⚡ Elektrische Verbindungen

### INMP441 Mikrofon → XIAO ESP32-S3

Das INMP441 ist ein digitales I2S-MEMS-Mikrofon. Es liefert die Audiodaten digital an den ESP32.

```
INMP441          XIAO ESP32-S3
────────         ──────────────
VDD    ────────▶ 3V3
GND    ────────▶ GND
SD     ────────▶ GPIO7  (I2S Data In)
SCK    ────────▶ GPIO8  (I2S Bit Clock)
WS     ────────▶ GPIO9  (I2S Word Select / LR Clock)
L/R    ────────▶ GND    (Linker Kanal = Low)
```

> 💡 **Erklärung für Einsteiger:** I2S ist ein digitales Audio-Protokoll. Anders als ein analoges Mikrofon liefert das INMP441 bereits digitale Daten – kein Rauschen durch analoge Leitungen!

### Spannungsteiler (Batterie-Messung) → A3

Der ESP32 kann an seinen Analog-Eingängen nur Spannungen bis ca. 3.3V messen. Ein Li-Ion-Akku liefert aber bis zu 4.2V. Deshalb teilen wir die Spannung mit zwei gleichen Widerständen:

```
                    Spannungsteiler

BAT+ (3.0–4.2V) ───┤ 200kΩ ├───┬───┤ 200kΩ ├─── GND
                                │
                                └──▶ A3 (GPIO4)

Formel:  V_adc = V_batterie × 0.5
         V_batterie = V_adc × 2.0 × 1.0548 (kalibrierter Faktor)

Beispiel: Akku 3.9V → A3 misst 1.95V → Software rechnet: 1.95V × 2.0 × 1.0548 = 4.11V
```

> 💡 **Warum 200kΩ?** Hohe Widerstandswerte minimieren den Stromfluss durch den Teiler. Bei 200kΩ + 200kΩ fließen nur ~10µA – vernachlässigbar für den Akku.

### TP4056 Laderegler

```
Solarpanel 6V ──▶ TP4056 IN+ / IN-
                  TP4056 BAT+ ──▶ Akku (+)
                  TP4056 BAT- ──▶ Akku (–)
                  TP4056 OUT+ ──▶ XIAO ESP32-S3 (BAT+ oder 5V)
                  TP4056 OUT- ──▶ XIAO ESP32-S3 (GND)
```

> ⚠️ **Wichtig:** Der TP4056 hat einen eingebauten Tiefentladeschutz (ca. 2.5V). Trotzdem sollte die Firmware bei <3.3V den Deep Sleep verlängern.

### Gesamtverkabelung (Übersicht)

```
┌──────────────┐
│  Solarpanel  │
│  6V / 5W     │
└─────┬───────┘
       │ + / -
       ▼
┌──────────────┐      ┌──────────────┐
│   TP4056     │─BAT─▶│  21700 Akku  │
│   Laderegler │      │  3.7V/5000mAh│
└──────┬───────┘      └──────────────┘
       │ OUT+ / OUT-
       ▼
┌──────────────────────────────────────┐
│  XIAO ESP32-S3                       │
│                                      │
│  3V3 ──▶ INMP441 VDD                │
│  GND ──▶ INMP441 GND + L/R          │
│  GPIO7 ◀── INMP441 SD  (Data)       │
│  GPIO8 ──▶ INMP441 SCK (Clock)      │
│  GPIO9 ──▶ INMP441 WS  (Word Sel.)  │
│                                      │
│  A3/GPIO4 ◀── Spannungsteiler Mitte  │
│               (2×200kΩ an BAT+/GND)  │
└──────────────────────────────────────┘
```

---

## 💾 Software-Komponenten

### Übersicht

| Datei | Läuft auf | Port | Funktion |
|---|---|---|---|
| `main_cpp_v11.txt` | ESP32-S3 (als `main.cpp`) | – | Firmware: Aufnahme, Processing, Upload |
| `receiver.py` | Raspberry Pi | 5000 | WAV-Empfang, Batterie-Logging, Config-API |
| `dashboard.py` | Raspberry Pi | 5001 | Web-Dashboard mit Charts und Config-Panel |
| `deploy.sh` | Raspberry Pi | – | Installations-Script (Setup-Hilfe) |
| `platformio_ini_v11.txt` | Mac/PC (Build) | – | PlatformIO Build-Konfiguration |
| `clean_birdsongs.sh` | Raspberry Pi | – | Wochenputz-Skript (löscht alte WAVs) |

### Firmware v1.1 – Ablauf eines Zyklus

```
1. 🔄 Wake up aus Deep Sleep
2. 🔋 Batteriespannung messen (ADC, 32× Mehrfachmessung, Mittelwert)
3. 📶 WiFi verbinden
4. ⚙️ Config vom Pi abrufen (GET http://<Pi-IP>:5000/config)
5. ⏰ Betriebszeit prüfen (z.B. 04:00–22:00)
   └─ Ausserhalb → Deep Sleep bis zur nächsten aktiven Stunde
6. 📴 WiFi ausschalten (spart Strom während Aufnahme)
7. 🎙️ Audio aufnehmen (konfigurierbare Dauer, z.B. 20 Sekunden)
8. 🔧 Audio-Processing:
   └─ Hochpassfilter (entfernt Wind-/Infraschall-Rumpeln)
   └─ Gain/Verstärkung (leise Signale anheben)
   └─ Noise Gate (prüft ob relevanter Sound vorhanden)
9. 🔇 Falls Stille erkannt → zurück zu Deep Sleep (spart Speicher & Strom)
10. 📶 WiFi wieder einschalten
11. 📤 WAV-Datei an Pi senden (HTTP POST mit Batteriespannung im Header)
12. 💤 Deep Sleep (konfigurierbar, z.B. 5 Sekunden)
```

### Receiver (receiver.py) – API-Endpunkte

| Endpunkt | Methode | Funktion |
|---|---|---|
| `/upload` | POST | WAV-Datei empfangen und speichern in ~/BirdSongs/StreamData/ |
| `/config` | GET | Aktuelle Konfiguration als JSON liefern |
| `/config` | POST | Konfiguration aktualisieren (vom Dashboard) |

### Dashboard (dashboard.py) – Features

- **Batterie-Übersicht:** Aktuelle Spannung, Min/Max, Durchschnitt, Ladezustand (%)
- **Spannungsverlauf:** Interaktiver Chart (6h / 12h / 24h / 3 Tage / 7 Tage)
- **Remote-Konfiguration:** Alle ESP32-Parameter live ändern (wirksam ab nächstem Zyklus)
- **Auto-Refresh:** Spannungsdaten werden alle 60 Sekunden aktualisiert

---

## 🍓 Installation Raspberry Pi

### Voraussetzungen

- Raspberry Pi 4B (oder 3B+) mit Raspberry Pi OS (Bookworm oder neuer)
- Zugang via SSH, Raspberry Pi Connect oder direkt mit Monitor/Tastatur
- WLAN-Verbindung im gleichen Netzwerk wie der ESP32
- **Docker** installiert für BirdNET-Go

### Schritt 1: Dateien herunterladen

Klone das Repository oder lade die Dateien manuell herunter:

```bash
# Option A: Git Clone
cd ~
git clone https://github.com/Paul-3400/Kauzohr.git
cd Kauzohr
```

```bash
# Option B: Dateien manuell in ~/birdnet-receiver/ ablegen
mkdir -p ~/birdnet-receiver
# receiver.py, dashboard.py, deploy.sh und clean_birdsongs.sh dorthin kopieren
```

### Schritt 2: Python Virtual Environment einrichten

Neuere Raspberry Pi OS Versionen (Bookworm+) erlauben kein globales `pip install` mehr (PEP 668). Deshalb verwenden wir ein Virtual Environment:

```bash
# Virtual Environment erstellen
python3 -m venv ~/birdnet-receiver/venv

# Aktivieren (du siehst dann "(venv)" vor dem Prompt)
source ~/birdnet-receiver/venv/bin/activate

# Flask installieren
pip install flask

# Prüfen
python -c "import flask; print(flask.__version__)"
# Erwartete Ausgabe: 3.1.3 (oder neuer)
```

### Schritt 3: Verzeichnisse erstellen

```bash
# Verzeichnis für WAV-Dateien
mkdir -p ~/BirdSongs/StreamData

# Verzeichnis für BirdNET-Go Daten
mkdir -p ~/birdnet-go-data/clips
```

### Schritt 4: Dateien an den richtigen Ort kopieren

Falls du via Git geklont hast:

```bash
cp ~/Kauzohr/receiver.py ~/birdnet-receiver/
cp ~/Kauzohr/dashboard.py ~/birdnet-receiver/
cp ~/Kauzohr/clean_birdsongs.sh ~/
```

### Schritt 5: Systemd Services einrichten

Damit Receiver und Dashboard automatisch beim Booten starten, legen wir zwei Systemd Services an.

> ⚠️ **Wichtig:** Ersetze `paul-rppi` durch deinen Pi-Benutzernamen! Finde ihn mit: `whoami`

**Receiver Service:**

```bash
sudo tee /etc/systemd/system/birdnet-receiver.service << 'EOF'
[Unit]
Description=BirdNET Kauzohr Receiver
After=network.target

[Service]
Type=simple
User=paul-rppi
WorkingDirectory=/home/paul-rppi/birdnet-receiver
ExecStart=/home/paul-rppi/birdnet-receiver/venv/bin/python receiver.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**Dashboard Service:**

```bash
sudo tee /etc/systemd/system/birdnet-dashboard.service << 'EOF'
[Unit]
Description=BirdNET Kauzohr Dashboard
After=network.target

[Service]
Type=simple
User=paul-rppi
WorkingDirectory=/home/paul-rppi/birdnet-receiver
ExecStart=/home/paul-rppi/birdnet-receiver/venv/bin/python dashboard.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**Services aktivieren und starten:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable birdnet-receiver birdnet-dashboard
sudo systemctl start birdnet-receiver
sudo systemctl start birdnet-dashboard
```

### Schritt 6: Prüfen

```bash
# Beide Services müssen "active (running)" zeigen
sudo systemctl status birdnet-receiver
sudo systemctl status birdnet-dashboard

# Ports prüfen (5000 und 5001 müssen belegt sein)
ss -tlnp | grep -E '500[01]'
```

### Schritt 7: Dashboard im Browser öffnen

Öffne im Browser auf einem beliebigen Gerät im gleichen Netzwerk:

```
http://<Pi-IP-Adresse>:5001
```

Beispiel: `http://10.0.1.196:5001`

> 💡 **Pi-IP herausfinden:** `hostname -I` auf dem Pi eingeben.

---

## ⚡ Installation ESP32-S3 Firmware

### Voraussetzungen

- **Visual Studio Code** mit **PlatformIO Extension** installiert
- USB-C Kabel zum Anschluss des XIAO ESP32-S3
- Die Dateien `main_cpp_v11.txt` und `platformio_ini_v11.txt` aus diesem Repository

### Schritt 1: PlatformIO-Projekt erstellen

```bash
# Neues Projekt anlegen (oder bestehendes verwenden)
mkdir -p ~/birdnet-outdoor-mic/src
cd ~/birdnet-outdoor-mic
```

### Schritt 2: Dateien einfügen

1. Öffne `main_cpp_v11.txt` aus dem Repository
2. Kopiere den gesamten Inhalt nach `src/main.cpp`
3. Öffne `platformio_ini_v11.txt` aus dem Repository
4. Kopiere den gesamten Inhalt nach `platformio.ini`

### Schritt 3: WiFi-Daten anpassen

Öffne `src/main.cpp` und suche nach diesen Zeilen (am Anfang der Datei):

```cpp
const char* WIFI_SSID = "DEIN_WLAN_NAME";
const char* WIFI_PASS = "DEIN_WLAN_PASSWORT";
const char* SERVER_URL = "http://DEINE_PI_IP:5000";
```

Ersetze die Platzhalter mit deinen tatsächlichen Daten:

```cpp
const char* WIFI_SSID = "MeinWLAN";          // Dein WLAN-Name
const char* WIFI_PASS = "MeinPasswort123";    // Dein WLAN-Passwort
const char* SERVER_URL = "http://10.0.1.196:5000";  // IP deines Pi
```

### Schritt 4: Build (Kompilieren)

In VS Code:
- Klicke auf das **✓ Häkchen** in der PlatformIO-Leiste (unten)
- Oder im Terminal: `pio run`

Erwartete Ausgabe:
```
SUCCESS
RAM:   14.0% (used 45916 bytes from 327680 bytes)
Flash: 26.9% (used 898753 bytes from 3342336 bytes)
```

> 💡 **Erster Build dauert länger** – die Library ArduinoJson wird automatisch heruntergeladen.

### Schritt 5: Upload (Firmware flashen)

1. **ESP32 per USB-C an den Computer anschließen**
2. **Bluetooth am Computer ausschalten** (verhindert dass BT-Geräte als Serial Port erkannt werden)
3. Klicke auf den **→ Pfeil** (Upload) in der PlatformIO-Leiste
4. Oder im Terminal: `pio run --target upload`

> ⚠️ **Falls der Upload fehlschlägt:** ESP32 in den Bootloader-Modus bringen:
> 1. **BOOT-Taste gedrückt halten**
> 2. Kurz **RESET drücken**
> 3. **BOOT loslassen**
> 4. Upload erneut versuchen

### Schritt 6: Serial Monitor prüfen

```bash
pio device monitor
```

Erwartete Ausgabe:
```
BirdNET Outdoor-Mikrofon v1.1
PSRAM: 8.00 MB
Batterie: ADC=1892 (avg), V_adc=1.929V, V_bat=3.859V
WiFi verbinde zu: MeinWLAN
...verbunden! IP: 10.0.1.22
Config laden von http://10.0.1.196:5000/config
Aufnahme: 960000 Samples (20.0s)
HP-Filter angewendet (alpha=0.98)
Gain angewendet (2.0x)
Noise Gate: Peak=28960 > Threshold=500 → Audio aktiv
WAV Upload: 1920044 Bytes → HTTP 200
Deep Sleep: 5 Sekunden
```

---

## 🐳 BirdNET-Go Integration

BirdNET-Go ist eine Docker-basierte Anwendung zur Echtzeit-Erkennung von Vogelarten. Sie analysiert die aufgenommenen WAV-Dateien und liefert detaillierte Analysen.

### Voraussetzungen

- Docker installiert auf dem Raspberry Pi
- Mindestens 2GB RAM (Raspberry Pi 4B empfohlen)
- Port 8080 frei

### Installation BirdNET-Go

```bash
# Docker Container starten
# Ersetze /path/to/config durch deinen Pfad
# und /path/to/data durch das Verzeichnis für die Analysedaten

docker run -d \
  --name birdnet-go \
  --restart unless-stopped \
  -p 8080:8080 \
  -v /home/paul-rppi/birdnet-go-data:/data \
  -v /home/paul-rppi/birdnet-go-config:/config \
  -e TZ=Europe/Zurich \
  ghcr.io/tphakala/birdnet-go:nightly
```

### Konfiguration

1. **Dashboard öffnen:** `http://<Pi-IP>:8080/ui`
2. **Datenverzeichnis einstellen:**
   - **Input Directory:** `/data/clips` (hier werden die WAV-Dateien erwartet)
   - **Output Directory:** `/data/results` (hier werden die Analysen gespeichert)
3. **Analyse-Parameter:**
   - **Sensitivity:** 1.0 (Standard)
   - **Minimum Confidence:** 0.7 (nur Erkennungen mit mind. 70% Sicherheit)
   - **Species List:** Europe (für Schweizer Vogelarten)

### Integration mit Kauzohr

Damit BirdNET-Go die Aufnahmen des ESP32 analysieren kann, müssen die WAV-Dateien in das `/data/clips` Verzeichnis kopiert werden. Dies kann auf zwei Arten geschehen:

**Option 1: Direkter Upload an BirdNET-Go (empfohlen)**
Ändere in `receiver.py` den Upload-Endpunkt:

```python
# Statt an receiver.py zu senden:
# POST an BirdNET-Go API
import requests

birdnet_url = "http://localhost:8080/api/analyze"
with open(wav_path, 'rb') as f:
    files = {'audio': f}
    response = requests.post(birdnet_url, files=files)
```

**Option 2: Cronjob zum Kopieren der Dateien**

```bash
# Alle 5 Minuten neue WAV-Dateien nach /data/clips kopieren
*/5 * * * * cp /home/paul-rppi/BirdSongs/StreamData/*.wav /home/paul-rppi/birdnet-go-data/clips/ 2>/dev/null
```

### Dashboard-Features

- **Echtzeit-Analyse:** Vogelarten werden sofort nach der Aufnahme erkannt
- **Statistiken:** Anzahl Erkennungen, häufigste Arten, Durchschnittliche Konfidenz
- **Zeitverlauf:** Erkennungen pro Stunde/Tag/Woche
- **Top-Arten:** Rangliste der am häufigsten erkannten Vogelarten

---

## 📊 Dashboard bedienen

### Batterie-Übersicht (oberer Bereich)

| Anzeige | Bedeutung |
|---|---|
| **Aktuelle Spannung (V)** | Letzte gemessene Batteriespannung |
| **Ladezustand (%)** | Geschätzter Ladezustand (3.0V=0%, 4.2V=100%) |
| **Min / Max** | Niedrigste / höchste gemessene Spannung im Zeitraum |
| **Durchschnitt** | Mittlere Spannung |
| **Messungen** | Anzahl empfangener Spannungswerte |

### Spannungsverlauf (Chart)

- Zeigt die Batteriespannung über die Zeit
- Wählbare Zeiträume: **6h, 12h, 24h, 3 Tage, 7 Tage**
- Ideal zur Beobachtung des Solar-Lade-/Entladezyklus

### Konfiguration (unterer Bereich)

| Parameter | Bereich | Beschreibung |
|---|---|---|
| **Betrieb ab (Stunde)** | 0–23 | Ab welcher Stunde der ESP aufnimmt |
| **Betrieb bis (Stunde)** | 0–23 | Bis welche Stunde der ESP aufnimmt |
| **Aufnahmedauer (Sek)** | 5–30 | Länge einer einzelnen Aufnahme |
| **Deep Sleep (Sek)** | 1–300 | Pause zwischen zwei Aufnahmezyklen |
| **WiFi Timeout (ms)** | 1000–30000 | Max. Wartezeit für WiFi-Verbindung |
| **POST Timeout (ms)** | 1000–30000 | Max. Wartezeit für WAV-Upload |
| **Gain (Verstärkung)** | 0.5–10.0 | Audio-Verstärkungsfaktor |
| **Noise Threshold** | 0–10000 | Schwellwert für die Stille-Erkennung |
| **HP Filter Alpha** | 0.9–0.999 | Stärke des Hochpassfilters |
| **Noise Gate** | An/Aus | Stille Aufnahmen verwerfen |
| **Hochpassfilter** | An/Aus | Tieffrequentes Rauschen entfernen |

> 💡 **Änderungen werden wirksam ab dem nächsten ESP32-Zyklus.** Der ESP holt sich die neue Config beim nächsten Aufwachen aus dem Deep Sleep.

---

## 🔧 Betrieb & Wartung

### Nützliche Befehle auf dem Pi

```bash
# Service-Status prüfen
sudo systemctl status birdnet-receiver
sudo systemctl status birdnet-dashboard

# Logs anschauen (letzte 50 Zeilen)
sudo journalctl -u birdnet-receiver -n 50 --no-pager
sudo journalctl -u birdnet-dashboard -n 50 --no-pager

# BirdNET-Go Container Status
docker ps | grep birdnet-go

# BirdNET-Go Logs
docker logs birdnet-go --tail 50

# Services neu starten
sudo systemctl restart birdnet-receiver
sudo systemctl restart birdnet-dashboard

# BirdNET-Go neu starten
docker restart birdnet-go

# Anzahl gespeicherter WAV-Dateien
ls ~/BirdSongs/StreamData/*.wav | wc -l

# Speicherplatz der Aufnahmen
du -sh ~/BirdSongs/StreamData/

# Speicherplatz von BirdNET-Go
du -sh ~/birdnet-go-data/
```

### Speicherplatz überwachen

```bash
# Gesamtüberblick
df -h /

# Verzeichnisgrößen anzeigen
du -sh ~/BirdSongs/ ~/birdnet-go-data/ 2>/dev/null
```

---

## 🗑️ Automatische Speicherbereinigung (Wochenputz)

Um zu verhindern, dass der Speicher voll läuft und BirdNET-Go nicht mehr startet, wurde ein **automatischer Wochenputz** implementiert.

### Problem

Am 15.09.2026 war der Speicher voll:
- **Fehler:** "STARTUP ERROR: Insufficient disk space"
- **Benötigt:** 1024MB in /data
- **Verfügbar:** nur 275MB
- **Lösung:** Alte WAV-Dateien löschen

### Lösung: clean_birdsongs.sh

Ein Skript, das WAV-Dateien älter als 7 Tage aus ~/BirdSongs/StreamData/ löscht:

```bash
#!/bin/bash
# BirdNET Wochenputz - Löscht WAVs älter als 7 Tage
# Autor: Paul Simmen mit Vibe (GLM-5-2), 15.09.2026

LOG_FILE="/home/paul-rppi/clean_birdsongs.log"
DATA_DIR="/home/paul-rppi/BirdSongs/StreamData"

echo "=== BirdNET Wochenputz $(date) ===" >> "$LOG_FILE"
echo "Lösche WAVs älter als 7 Tage in $DATA_DIR..." >> "$LOG_FILE"

# Finde und lösche Dateien älter als 7 Tage
find "$DATA_DIR" -name "*.wav" -type f -mtime +7 -delete -print >> "$LOG_FILE" 2>&1

echo "Fertig." >> "$LOG_FILE"
```

**Speicherort:** `/home/paul-rppi/clean_birdsongs.sh`

### Cronjob einrichten

Damit das Skript automatisch jeden Tag um 03:00 Uhr läuft:

```bash
# Crontab bearbeiten
crontab -e
```

Füge folgende Zeile hinzu:

```bash
# BirdNET Wochenputz - täglich um 03:00 Uhr
0 3 * * * /home/paul-rppi/clean_birdsongs.sh >> /home/paul-rppi/clean_birdsongs.log 2>&1
```

### Manuell ausführen

```bash
# Skript ausführbar machen
chmod +x ~/clean_birdsongs.sh

# Testlauf (zeigt was gelöscht würde, ohne zu löschen)
find ~/BirdSongs/StreamData -name "*.wav" -type f -mtime +7

# Echten Lauf starten
~/clean_birdsongs.sh

# Log prüfen
tail -n 20 ~/clean_birdsongs.log
```

### Alternative für BirdNET-Go Daten

Falls BirdNET-Go in Docker läuft und die Daten in `/data/clips` speichert:

```bash
# In den Container und alte Dateien löschen
docker exec birdnet-go find /data/clips -type f -mtime +7 -delete

# Oder als Cronjob für Docker:
0 3 * * * docker exec birdnet-go find /data/clips -type f -mtime +7 -delete >> /home/paul-rppi/docker_clean.log 2>&1
```

---

## 📁 Projektstruktur

```
Kauzohr/
├── README.md                    # Diese Hauptdokumentation
├── LICENSE                      # Lizenz (MIT)
├── HANDOVER_*.md                # Sitzungsprotokolle
├── main_cpp_v11.txt            # ESP32-S3 Firmware (main.cpp)
├── platformio_ini_v11.txt       # PlatformIO Konfiguration
├── receiver.py                  # WAV-Empfänger für Raspberry Pi
├── dashboard.py                 # Web-Dashboard
├── deploy.sh                   # Installationsskript
├── clean_birdsongs.sh          # Wochenputz-Skript
└── docs/                       # Zusätzliche Dokumentation
    ├── hardware/               # Schaltpläne, Fotos
    └── software/               # Code-Dokumentation

# Auf dem Raspberry Pi:
/home/paul-rppi/
├── birdnet-receiver/           # Receiver & Dashboard
│   ├── venv/                   # Python Virtual Environment
│   ├── receiver.py
│   ├── dashboard.py
│   └── deploy.sh
├── BirdSongs/                  # Aufnahmedaten
│   └── StreamData/             # WAV-Dateien
├── birdnet-go-data/            # BirdNET-Go Daten
│   ├── clips/                  # Zu analysierende Dateien
│   └── results/                # Analyseergebnisse
└── clean_birdsongs.sh          # Wochenputz-Skript
```

---

## 🚨 Fehlerbehebung

### Häufige Probleme und Lösungen

#### 1. BirdNET-Go startet nicht

**Symptom:** Container zeigt "STARTUP ERROR: Insufficient disk space"

**Ursache:** Speicher voll (wie am 15.09.2026)

**Lösung:**
```bash
# Speicher prüfen
df -h /

# Alte WAV-Dateien löschen
~/clean_birdsongs.sh

# Oder manuell:
find ~/BirdSongs/StreamData -name "*.wav" -type f -mtime +7 -delete

# BirdNET-Go neu starten
docker restart birdnet-go
```

#### 2. ESP32 verbindet sich nicht mit WiFi

**Symptom:** Serielle Ausgabe zeigt "WiFi Verbindung fehlgeschlagen"

**Lösung:**
- Prüfe WLAN-Name und Passwort in `main.cpp`
- Prüfe, ob ESP32 im gleichen Netzwerk wie der Pi ist
- WiFi Timeout in Dashboard erhöhen (z.B. auf 15000ms)

#### 3. Keine Aufnahmen im Dashboard

**Symptom:** Dashboard zeigt keine WAV-Dateien an

**Lösung:**
```bash
# Prüfe ob receiver.py läuft
sudo systemctl status birdnet-receiver

# Prüfe Logs
sudo journalctl -u birdnet-receiver -n 50

# Prüfe ob Dateien ankommen
ls -la ~/BirdSongs/StreamData/
```

#### 4. BirdNET-Go erkennt keine Vogelarten

**Symptom:** Dashboard zeigt 0 Erkennungen

**Lösung:**
- Prüfe ob WAV-Dateien in `/data/clips` sind:
  ```bash
  docker exec birdnet-go ls /data/clips
  ```
- Prüfe BirdNET-Go Logs:
  ```bash
  docker logs birdnet-go
  ```
- Prüfe Konfiguration (Sensitivity, Confidence Threshold)

#### 5. Batteriespannung wird nicht angezeigt

**Symptom:** Dashboard zeigt 0V oder unrealistische Werte

**Lösung:**
- Prüfe Spannungsteiler-Verbindungen (2×200kΩ, A3)
- Prüfe Kalibrierungsfaktor in Firmware (aktuell: 1.0548)
- Messen mit Multimeter direkt am Akku und vergleichen

#### 6. Docker Container stürzt ab

**Symptom:** `docker ps` zeigt birdnet-go nicht an

**Lösung:**
```bash
# Container neu starten
docker start birdnet-go

# Logs prüfen
docker logs birdnet-go

# Container neu erstellen (falls nötig)
docker rm birdnet-go
docker run -d --name birdnet-go --restart unless-stopped -p 8080:8080 -v /home/paul-rppi/birdnet-go-data:/data ghcr.io/tphakala/birdnet-go:nightly
```

---

## 📜 Lizenz

Dieses Projekt steht unter der **MIT-Lizenz**. Siehe [LICENSE](LICENSE) für Details.

---

## 📞 Support & Kontakt

- **Projekt:** [GitHub - Paul-3400/Kauzohr](https://github.com/Paul-3400/Kauzohr)
- **Autor:** Paul Simmen (Paul-3400)
- **Standort:** Burgdorf, Schweiz 🇨🇭
- **E-Mail:** (über GitHub)

---

**Letzte Aktualisierung:** 15.09.2026  
**Version:** v1.2  
**Autor:** Paul Simmen mit Vibe (GLM-5-2), 15.09.2026