---
title: "HANDOVER – BirdNET-Go Integration & RTSP-Pipeline"
date: 2026-09-01
author: Paul mit Claude (Anthropic Claude 4, 2026)
project: Kauzohr
session: "BirdNET-Go + Digitales Kabel (RTSP)"
status: "✅ Vollständig funktional"
---

# HANDOVER – BirdNET-Go & RTSP-Pipeline

> **Session vom 1. September 2026**
> Erstellt von Paul mit Claude (Anthropic Claude 4, 2026)

---

## 🎯 Ziel der Session

BirdNET-Go (Docker) soll die vom ESP32 aufgenommenen und via `receiver.py` empfangenen WAV-Dateien **live analysieren** und Vogelarten erkennen. Dazu musste ein "digitales Kabel" zwischen `receiver.py` und BirdNET-Go gelegt werden.

---

## 📊 Ausgangslage

| Komponente | Status vor Session |
|---|---|
| **ESP32 (Kauzohr)** | ✅ Firmware v1.1 – nimmt auf, sendet WAV + Batteriespannung |
| **receiver.py v1.1** | ✅ Empfängt WAVs, speichert als .wav |
| **BirdNET-Go** | ✅ Docker-Container läuft, aber **keine Audio-Quelle** |
| **Verbindung receiver → BirdNET-Go** | ❌ Fehlte komplett |

---

## 🧠 Lösungsweg – Drei Ansätze

### Ansatz 1: ALSA Loopback (snd-aloop) ❌ gescheitert

**Idee:** Virtuelles ALSA-Sounddevice als Brücke.

```
receiver.py → aplay → snd-aloop (hw:3) → BirdNET-Go (ALSA capture)
```

**Warum gescheitert:**

| Schritt | Status | Problem |
|---|---|---|
| snd-aloop Kernel-Modul laden | ✅ | – |
| aplay → Loopback | ✅ | – |
| receiver.py v1.2 → aplay → Loopback | ✅ | – |
| receiver.py v1.3 (persistent aplay) | ✅ | – |
| BirdNET-Go Docker → ALSA | ❌ | **Docker verbietet Mount von `/proc/asound`** |

> **Erkenntnis:** Docker blockiert aus Sicherheitsgründen Mounts nach `/proc/*`.
> BirdNET-Go im Container kann ohne `/proc/asound` die ALSA-Karten nicht enumerieren.
> Das `--privileged` Flag wäre ein Workaround, aber unsauber.

### Ansatz 2: RTSP-Stream ✅ ERFOLGREICH

**Idee:** Audio als Netzwerk-Stream – braucht kein ALSA im Container.

```
receiver.py v1.4 → ffmpeg → mediaMTX (RTSP) → BirdNET-Go
```

**Warum erfolgreich:**
- BirdNET-Go unterstützt **nativ** RTSP-Streams als Audio-Quelle
- Kein Kernel-Modul, kein `/proc`-Mount nötig
- Docker-Container braucht nur Netzwerkzugang (hat er sowieso)

### Ansatz 3: Nicht versucht (Alternativen)
- HTTP Audio-Stream
- BirdNET-Go Analyse-API direkt mit WAV füttern
- `--privileged` Docker Flag

---

## 🏗️ Finale Architektur

```
┌─────────────┐     WAV POST      ┌──────────────────┐
│  ESP32-S3   │ ──────────────────>│  receiver.py v1.4│
│  Kauzohr    │  HTTP + Header     │  (Flask, Port    │
│  FW v1.1    │  X-Battery-Voltage │   5000)          │
└─────────────┘                    └────────┬─────────┘
                                            │
                                   PCM via stdin (pipe:0)
                                            │
                                            ▼
                                   ┌──────────────────┐
                                   │  ffmpeg           │
                                   │  (persistent)     │
                                   │  Opus 48kHz       │
                                   └────────┬─────────┘
                                            │
                                   RTSP publish
                                            │
                                            ▼
                                   ┌──────────────────┐
                                   │  mediaMTX v1.9.3  │
                                   │  RTSP Server      │
                                   │  Port 8554        │
                                   │  Pfad: /birds     │
                                   └────────┬─────────┘
                                            │
                                   RTSP subscribe
                                   rtsp://10.0.1.196:8554/birds
                                            │
                                            ▼
                                   ┌──────────────────┐
                                   │  BirdNET-Go       │
                                   │  Docker Container  │
                                   │  Port 8080         │
                                   │  BirdNET_V2.4     │
                                   │  180 Arten (CH)   │
                                   └──────────────────┘
```

---

## 📦 Installierte Komponenten

### 1. ffmpeg

```bash
sudo apt install -y ffmpeg
```

- **Zweck:** Konvertiert raw PCM (pipe:0) → Opus-kodierter RTSP-Stream
- **Wird gestartet von:** receiver.py v1.4 (als Subprozess)

### 2. mediaMTX v1.9.3

```bash
# Binary
/usr/local/bin/mediamtx

# Config
/usr/local/etc/mediamtx.yml

# Service
/etc/systemd/system/mediamtx.service
```

- **Zweck:** Leichtgewichtiger RTSP/RTMP/HLS/WebRTC Server
- **Ports:**
  - **8554** – RTSP Server
  - **9997** – REST API (`http://localhost:9997/v3/paths/list`)
- **Pfad:** `/birds` (wird automatisch erstellt wenn ffmpeg publisht)
- **User:** paul-rppi

```ini
# /etc/systemd/system/mediamtx.service
[Unit]
Description=MediaMTX RTSP Server
After=network.target

[Service]
ExecStart=/usr/local/bin/mediamtx /usr/local/etc/mediamtx.yml
Restart=always
RestartSec=5
User=paul-rppi

[Install]
WantedBy=multi-user.target
```

### 3. receiver.py v1.4 (RTSP-Stream)

**Pfad:** `/home/paul-rppi/birdnet-receiver/receiver.py`

**Änderungen gegenüber v1.1:**

| Feature | v1.1 | v1.4 |
|---|---|---|
| WAV empfangen | ✅ | ✅ |
| WAV speichern | ✅ | ✅ |
| ffmpeg → RTSP | ❌ | ✅ NEU |
| Stille-Generator | ❌ | ✅ NEU (hält Stream offen) |
| Batterie-Kalibrierung | ❌ | ✅ NEU |
| Header-Auswertung | ❌ | ✅ NEU (X-Battery-Voltage) |

**Funktionsweise RTSP-Pipeline in receiver.py:**

1. **Beim Start:** ffmpeg wird als persistenter Subprozess gestartet
   ```
   ffmpeg -f s16le -ar 48000 -ac 1 -i pipe:0 -acodec libopus -b:a 96k -f rtsp rtsp://127.0.0.1:8554/birds
   ```
2. **Stille-Generator:** Thread sendet kontinuierlich Null-Bytes (Stille) an ffmpeg stdin → hält den RTSP-Stream offen
3. **Bei WAV-Empfang:** PCM-Daten werden statt Stille an ffmpeg stdin gesendet → echtes Audio im Stream
4. **Ergebnis:** BirdNET-Go hat einen **permanenten** RTSP-Stream, der zwischen Stille und Vogelaudio wechselt

**Batterie-Kalibrierung:**

```python
# Config-Parameter (oben im File)
BATTERY_CAL_FACTOR = 1.0548     # Spannungsteiler-Korrektur
BATTERY_CAL_OFFSET = 0.0        # Feinkorrektur (Volt)

# Anwendung (in upload-Funktion)
battery_raw = request.headers.get("X-Battery-Voltage", "n/a")
v_raw = float(battery_raw)
battery_v = round(v_raw * BATTERY_CAL_FACTOR + BATTERY_CAL_OFFSET, 3)
```

| Parameter | Wert | Herkunft |
|---|---|---|
| CAL_FACTOR | 1.0548 | Ein-Punkt-Eichung: Voltmeter 4.079V / ESP32 3.867V |
| CAL_OFFSET | 0.0 | Für späteren 2. Messpunkt reserviert |
| Genauigkeit | ~0.6% | Validiert: 4.102V kalibriert vs. 4.079V Voltmeter |

### 4. BirdNET-Go Config

**Pfad:** `/home/paul-rppi/birdnet-go-app/config/config.yaml`

**Relevante Änderung:**

BirdNET-Go hat die RTSP-URL automatisch in die richtige Sektion verschoben:

```yaml
# Zeile ~398
rtsp:
    url: rtsp://10.0.1.196:8554/birds
    type: rtsp
```

> **Wichtig:** Nicht `127.0.0.1` sondern `10.0.1.196` – der Docker-Container
> erreicht den Host über die LAN-IP, nicht über localhost!

---

## 🧹 Aufräumarbeiten (erledigt)

| Altlast | Aktion | Status |
|---|---|---|
| `snd-aloop` in `/etc/modules` | Zeile entfernt | ✅ |
| `snd-aloop` in `/etc/modules-load.d/snd-aloop.conf` | Datei gelöscht | ✅ |
| `snd-aloop` Kernel-Modul | `modprobe -r` entladen | ✅ |
| `--device /dev/snd` in birdnet-go.service | Zeile entfernt | ✅ |

---

## ✅ Validierung

### Erster erfolgreicher Test (01.09.2026, 12:21 Uhr)

| Erkennung | Art | Konfidenz |
|---|---|---|
| 🐦 Kernbeisser | *Coccothraustes coccothraustes* | 86% |
| 🐦 Haussperling | *Passer domesticus* | 78% |

**Pipeline-Stats:** 112 Inferenzen, 1120 Raw-Results, 3 Detektionen

### Batterie-Kalibrierung (01.09.2026, 12:48 Uhr)

```
Batterie: 4.102V (roh: 3.889V, Faktor: 1.0548)
```

---

## 🔧 Services-Übersicht (nach Session)

| Service | Befehl | Port | Status |
|---|---|---|---|
| `birdnet_receiver` | `sudo systemctl status birdnet_receiver` | 5000 | ✅ active |
| `mediamtx` | `sudo systemctl status mediamtx` | 8554, 9997 | ✅ active |
| `birdnet-go` | `sudo systemctl status birdnet-go` | 8080 | ✅ active |

**Startrefenfolge (automatisch via systemd):**
1. mediaMTX (RTSP Server)
2. birdnet_receiver (startet ffmpeg → publisht auf mediaMTX)
3. birdnet-go (subscribed RTSP von mediaMTX)

---

## 🔮 Offene Punkte / Nächste Schritte

| Thema | Priorität | Beschreibung |
|---|---|---|
| **Zwei-Punkt-Eichung** | Mittel | Bei niedrigerem Akku (~3.3V) zweiten Messpunkt nehmen → BATTERY_CAL_OFFSET berechnen |
| **Batterie-Warnschwelle** | Niedrig | z.B. Log-Warnung bei < 3.4V |
| **Service-Beschreibung** | Kosmetisch | birdnet_receiver.service zeigt noch "v1.1" statt "v1.4" |
| **RTSP Reconnect** | Prüfen | Was passiert wenn mediaMTX neustartet? Reconnect-Logik in receiver.py? |
| **Dashboard Batterie** | Feature | Batteriespannung im BirdNET-Go Dashboard anzeigen |
| **GitHub Update** | Pflege | receiver.py v1.4 + diese HANDOVER auf GitHub pushen |

---

## 🧠 Erkenntnisse für das Notizbuch

1. **Docker + `/proc` = No-Go:** Docker verbietet kategorisch Mounts nach `/proc/*`. Kein Workaround ohne `--privileged`.
2. **RTSP ist der saubere Weg:** Netzwerk-basierte Audio-Übertragung ist Docker-freundlicher als ALSA-Devices.
3. **mediaMTX ist ein Schweizer Taschenmesser:** Ein Binary, null Config nötig, akzeptiert jeden Stream automatisch.
4. **Opus > PCMA für Vogelstimmen:** PCMA (8kHz, G.711) ist Telefonqualität – Vogelstimmen brauchen 48kHz für Frequenzen bis 24kHz.
5. **ESP32 ADC braucht Kalibrierung:** Systematische Abweichung von ~5.5% durch Spannungsteiler-Toleranzen und ADC-Referenzspannung.
6. **Batteriespannung kommt als HTTP-Header:** `X-Battery-Voltage`, nicht als Query-Parameter – wichtig für receiver.py!

---

## 📋 Briefing für nächste Claude-Session

> Paul arbeitet am **Kauzohr**-Projekt: ESP32-S3 Outdoor-Mikrofon für Vogelstimmen-Erkennung.
> Die komplette Pipeline steht: ESP32 → receiver.py v1.4 → ffmpeg → mediaMTX (RTSP) → BirdNET-Go (Docker).
> Batterie-Kalibrierung ist implementiert (Ein-Punkt, Faktor 1.0548).
> Nächste Themen: Zwei-Punkt-Eichung, Dashboard-Batterie, GitHub-Update.
> **Kontext-Dokumente:** Dieses HANDOVER + INDEX.md + GitHub Repo (Paul-3400/Kauzohr).
