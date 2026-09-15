---
title: "README – BirdNET Kauzohr"
date: 2026-08-30
version: "v1.1"
author: "Paul mit Claude (Anthropic Claude, latest generation, 2026)"
---

# 🦉 BirdNET Kauzohr – 24/7 Vogelstimmen-Recorder

**Eine solarbetriebene Outdoor-Audiostation zur automatischen Aufnahme von Vogelstimmen.**

> Entwickelt von Paul (Paul-3400) in Burgdorf, Schweiz 🇨🇭  
> Als kreatives Brain-Gym-Projekt – Technik trifft Natur! 🧠💪

---

## 📋 Inhaltsverzeichnis

- [Überblick](#-überblick)
- [Systemarchitektur](#-systemarchitektur)
- [Hardware-Komponenten](#-hardware-komponenten)
- [Elektrische Verbindungen](#-elektrische-verbindungen)
- [Software-Komponenten](#-software-komponenten)
- [Installation Raspberry Pi](#-installation-raspberry-pi)
- [Installation ESP32-S3 Firmware](#-installation-esp32-s3-firmware)
- [Dashboard bedienen](#-dashboard-bedienen)
- [Betrieb & Wartung](#-betrieb--wartung)
- [Projektstruktur](#-projektstruktur)
- [Fehlerbehebung](#-fehlerbehebung)
- [Lizenz](#-lizenz)

---

## 🎯 Überblick

Das **Kauzohr** ist ein autonomes Aufnahmesystem für Vogelstimmen. Ein wetterfestes Mikrofon-Modul im Garten nimmt rund um die Uhr Audio auf und sendet die Aufnahmen per WLAN an einen Raspberry Pi im Haus. Dort werden die WAV-Dateien gespeichert und können später mit [BirdNET](https://birdnet.cornell.edu/) analysiert werden.

### ✨ Funktionen

| Funktion | Beschreibung |
|---|---|
| 🎙️ **Automatische Aufnahme** | 20-Sekunden-Zyklen mit konfigurierbarer Dauer (5–30s) |
| 🔋 **Batterie-Überwachung** | Spannungsmessung via Spannungsteiler, Live-Anzeige im Dashboard |
| ☀️ **Solarbetrieben** | 5W Solarpanel + TP4056 Laderegler + 21700 Li-Ion Akku |
| 📡 **Remote-Konfiguration** | Alle Parameter über Web-Dashboard einstellbar |
| 🔇 **Intelligente Stille-Erkennung** | Noise Gate filtert leere Aufnahmen aus |
| 🔧 **Audio-Processing** | Hochpassfilter + einstellbare Verstärkung direkt auf dem ESP |
| ⏰ **Zeitsteuerung** | Konfigurierbare Betriebszeiten (z.B. 04:00–22:00) |
| 💤 **Deep Sleep** | Minimaler Stromverbrauch zwischen den Aufnahmen |
| 📊 **Web-Dashboard** | Spannungsverlauf, Ladezustand, alle Einstellungen im Browser |

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
│   ┌────────────────────────────────────────────┐                    │
│   │  Raspberry Pi 4B                            │                    │
│   │                                              │                    │
│   │  📥 receiver.py (Port 5000)                  │                    │
│   │     └─ Empfängt WAV-Dateien                  │                    │
│   │     └─ Loggt Batteriespannung                │                    │
│   │     └─ Liefert Config an ESP32               │                    │
│   │                                              │                    │
│   │  📊 dashboard.py (Port 5001)                 │                    │
│   │     └─ Web-Dashboard im Browser              │                    │
│   │     └─ Spannungsverlauf (Chart)              │                    │
│   │     └─ Remote-Konfiguration                  │                    │
│   │                                              │                    │
│   │  💾 ~/BirdSongs/StreamData/*.wav             │                    │
│   └────────────────────────────────────────────┘                    │
│                                                                      │
│   Browser: http://<Pi-IP>:5001                                       │
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
| Server | **Raspberry Pi 4B** (2GB+ RAM) | Empfänger, Dashboard, Speicher | CHF 50.– |
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

Der ESP32 kann an seinen Analog-Eingängen nur Spannungen bis ca. 3.3V messen. Ein Li-Ion-Akku liefert aber bis zu 4.2V. Deshalb teilen wir die Spannung mit zwei gleichen Widerständen halbiert:

```
                    Spannungsteiler

BAT+ (3.0–4.2V) ───┤ 200kΩ ├───┬───┤ 200kΩ ├─── GND
                                │
                                └──▶ A3 (GPIO4)

Formel:  V_adc = V_batterie × 0.5
         V_batterie = V_adc × 2.0

Beispiel: Akku 3.9V → A3 misst 1.95V → Software rechnet ×2 = 3.9V
```

> 💡 **Warum 200kΩ?** Hohe Widerstandswerte minimieren den Stromfluss durch den Teiler. Bei 200kΩ + 200kΩ fliessen nur ~10µA – vernachlässigbar für den Akku.

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
└──────┬───────┘
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

| Endpoint | Methode | Funktion |
|---|---|---|
| `/upload` | POST | WAV-Datei empfangen und speichern |
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
# receiver.py, dashboard.py und deploy.sh dorthin kopieren
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
```

### Schritt 4: Dateien an den richtigen Ort kopieren

Falls du via Git geklont hast:

```bash
cp ~/Kauzohr/receiver.py ~/birdnet-receiver/
cp ~/Kauzohr/dashboard.py ~/birdnet-receiver/
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

1. **ESP32 per USB-C an den Computer anschliessen**
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

# Services neu starten
sudo systemctl restart birdnet-receiver
sudo systemctl restart birdnet-dashboard

# Anzahl gespeicherter WAV-Dateien
ls ~/BirdSongs/StreamData/*.wav | wc -l

# Speicherplatz der Aufnahmen
du -sh ~/BirdSongs/StreamData/

# Batterie-Log anschauen (letzte 10 Einträge)
tail -10 ~/birdnet-receiver/battery_log.csv
```

### Speichermanagement

Eine 20-Sekunden-Aufnahme benötigt ca. **1.9 MB**. Bei einem Zyklus alle 25 Sekunden (20s Aufnahme + 5s Sleep) ergibt das:

| Zeitraum | Aufnahmen (ca.) | Speicher (ca.) |
|---|---|---|
| 1 Stunde | 144 | 274 MB |
| 1 Tag (18h aktiv) | 2'592 | 4.9 GB |
| 1 Woche | 18'144 | 34.5 GB |

> ⚠️ **Empfehlung:** Regelmässig alte Aufnahmen archivieren oder löschen. Alternativ den Deep Sleep auf 30–60 Sekunden erhöhen für den Dauerbetrieb.

---

## 📁 Projektstruktur

```
Kauzohr/
├── README.md                          # Diese Datei
├── LICENSE                            # MIT Lizenz
│
├── main_cpp_v11.txt                   # ESP32 Firmware v1.1 (→ src/main.cpp)
├── platformio_ini_v11.txt             # PlatformIO Config (→ platformio.ini)
├── firmware v1.0_.txt                 # Alte Firmware v1.0 (Referenz)
│
├── receiver.py                        # Pi: WAV-Empfänger + Config-API (Port 5000)
├── dashboard.py                       # Pi: Web-Dashboard (Port 5001)
├── deploy.sh                          # Pi: Installations-Hilfsscript
│
├── HANDOVER.md                        # Projekt-Übergabe-Dokument
├── HANDOVER_2026-08-30_Kauz...md      # Session-Handover 30.08.2026
├── HANDOVER_20260722.md               # Session-Handover 22.07.2026
├── Handover_2026-08-11.md             # Session-Handover 11.08.2026
├── README_2026-08-11.md               # Frühere README-Version
└── .gitignore                         # Git-Ausschlüsse
```

---

## 🔍 Fehlerbehebung

### ESP32 verbindet sich nicht mit WiFi

| Prüfpunkt | Befehl / Aktion |
|---|---|
| SSID/Passwort korrekt? | In `main.cpp` prüfen |
| 2.4 GHz WLAN? | ESP32 unterstützt kein 5 GHz! |
| Pi erreichbar? | `ping <Pi-IP>` vom Computer |
| WiFi Timeout erhöhen | Im Dashboard auf 15000–20000 ms setzen |

### Receiver antwortet mit Fehler 500

```bash
# Log prüfen
sudo journalctl -u birdnet-receiver -n 30 --no-pager

# Häufigste Ursache: Verzeichnis fehlt
mkdir -p ~/BirdSongs/StreamData

# Service neu starten
sudo systemctl restart birdnet-receiver
```

### Dashboard nicht erreichbar

```bash
# Läuft der Service?
sudo systemctl status birdnet-dashboard

# Port 5001 belegt?
ss -tlnp | grep 5001

# Firewall prüfen (falls aktiv)
sudo ufw status
```

### PlatformIO erkennt falschen Port

- **Bluetooth am Computer ausschalten** (BT-Geräte werden als Serial Port erkannt)
- Port manuell angeben: `pio run --target upload --upload-port /dev/cu.usbmodemXXXXX`
- Verfügbare Ports auflisten: `ls /dev/cu.usb*`

### Batteriespannung zeigt 0V

- Verkabelung des Spannungsteilers prüfen (Mittenabgriff → A3/GPIO4)
- ADC-Pin in der Firmware prüfen (muss GPIO4 sein)
- Mit Multimeter gegenmessen

---

## 📜 Lizenz

MIT License – siehe [LICENSE](LICENSE)

---

## 🙏 Danksagung

- **[BirdNET](https://birdnet.cornell.edu/)** – Cornell Lab of Ornithology für die Vogelstimmen-KI
- **[Seeed Studio](https://www.seeedstudio.com/)** – für den grossartigen XIAO ESP32-S3
- **[PlatformIO](https://platformio.org/)** – für die komfortable Embedded-Entwicklung
- **Claude (Anthropic)** – KI-Unterstützung bei Entwicklung und Dokumentation

---

*Erstellt von Paul mit Claude (Anthropic Claude, latest generation, 2026)*  
*Letzte Aktualisierung: 30. August 2026*
