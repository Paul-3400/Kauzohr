---
title: "HANDOVER – BirdNET Kauzohr v1.1"
date: 2026-08-30
session: "Post-Bug Recovery + Pi-Installation + Firmware v1.1 + Inbetriebnahme"
author: "Paul mit Claude (Anthropic Claude, latest generation, 2026)"
status: "✅ SYSTEM OPERATIONAL"
---

# 🦉 HANDOVER – BirdNET Kauzohr v1.1

## 📅 Session: 30. August 2026

---

## 🎯 Was wurde erreicht

### 1. Pi-Installation (Raspberry Pi 4B – RpPi4B-002)
- **IP:** 10.0.1.196
- **User:** paul-rppi (Home: `/home/paul-rppi`)
- **Hostname:** RpPi4B-002
- **Zugang:** Raspberry Pi Connect (Remote Shell)
- **Python:** 3.13.5 mit venv unter `~/birdnet-receiver/venv/`
- **Flask:** 3.1.3 (im venv installiert)
- **Dateien via scp** auf den Pi kopiert (User: `paul-rppi`, NICHT der Hostname)

### 2. Systemd Services eingerichtet
- `birdnet-receiver.service` → Port **5000** ✅ active
- `birdnet-dashboard.service` → Port **5001** ✅ active
- Beide nutzen: `/home/paul-rppi/birdnet-receiver/venv/bin/python`
- Services manuell via `sudo tee` angelegt (deploy.sh brach ab wegen "same file" Fehler)

### 3. Firmware v1.1 erstellt & geflasht (XIAO ESP32-S3)
- **PlatformIO** auf Mac, Build SUCCESS
- RAM: 14.0%, Flash: 26.9%
- ArduinoJson 7.4.3 als neue Dependency
- Upload via USB-C (⚠️ JBL Bluetooth-Kopfhörer wurde als Port erkannt → Bluetooth aus!)

### 4. System End-to-End verifiziert
- ESP32 nimmt auf (20s, 960'000 Samples) ✅
- HP-Filter (alpha=0.98), Gain (2.0x), Noise Gate aktiv ✅
- WiFi-Verbindung (RSSI -43 dBm, IP 10.0.1.22) ✅
- WAV Upload → Pi Receiver (1'920'044 Bytes, HTTP 200) ✅
- Batteriespannung wird geloggt (3.859V – 3.906V) ✅
- Config-Abruf vom Pi (GET /config → 200) ✅
- Deep Sleep 5s → neuer Zyklus ✅
- Dashboard zeigt Spannungsverlauf + Config-Panel ✅

---

## 📁 Dateien auf dem Pi

```
~/birdnet-receiver/
├── receiver.py          # v1.1 – WAV-Empfang, Batterie-Log, Config-API (Port 5000)
├── dashboard.py         # v1.0 – Battery & Config Dashboard (Port 5001)
├── deploy.sh            # v1.1 – Setup-Script (teilweise ausgeführt)
├── venv/                # Python Virtual Environment (Flask 3.1.3)
├── config.json          # Runtime-Config (vom Dashboard geschrieben)
└── battery_log.csv      # Spannungs-Logdaten
```

```
~/BirdSongs/StreamData/
├── 2026-08-12-birdnet-11:52:53.wav   # Älteste Aufnahme
├── ...
└── 2026-08-30-birdnet-11:03:34.wav   # Neueste Aufnahme (heute)
```

## 📁 Dateien auf dem Mac (PlatformIO Projekt)

```
birdnet-outdoor-mic/
├── src/
│   └── main.cpp              # Firmware v1.1
├── platformio.ini            # Build-Config mit ArduinoJson
└── ...
```

---

## 🔧 Aktuelle Config (Dashboard-Werte)

| Parameter | Wert | Beschreibung |
|---|---|---|
| Betrieb ab | 4 Uhr | Aktive Stunde Start |
| Betrieb bis | 22 Uhr | Aktive Stunde Ende |
| Aufnahmedauer | 20 Sek | Recording Duration |
| Deep Sleep | 5 Sek | Pause zwischen Zyklen |
| WiFi Timeout | 10'000 ms | Max. WiFi-Verbindungszeit |
| POST Timeout | 5'000 ms | Max. Upload-Zeit |
| Gain | 2.0x | Verstärkung |
| Noise Threshold | 500 | Schwellwert für Noise Gate |
| HP Filter Alpha | 0.98 | Hochpass-Filterstärke |
| Noise Gate | ✅ An | Stille-Erkennung aktiv |
| Hochpassfilter | ✅ An | Tieffrequenz-Filterung aktiv |

---

## 🔋 Batterie-Status (30.08.2026, ~11:05)

| Wert | Messung |
|---|---|
| Aktuell | 3.904V |
| Ladezustand | 64% |
| Min | 3.859V |
| Max | 3.906V |
| Durchschnitt | 3.880V |
| Messungen | 17 |

---

## 🐛 Gelöste Probleme in dieser Session

| Problem | Ursache | Lösung |
|---|---|---|
| scp Permission denied | Falscher Username (Hostname statt User) | User = `paul-rppi` |
| deploy.sh Abbruch | Dateien bereits im Zielordner ("same file") | Services manuell angelegt |
| PlatformIO "no envs" | Copy-Paste Problem bei platformio.ini | Inhalt nochmal sauber eingefügt |
| Port Auto-Detect JBL | Bluetooth-Kopfhörer als Serial erkannt | Bluetooth aus, manueller Port |
| Port 5000 belegt | Alter Python-Prozess (PID 1522) | `kill -9` + systemctl restart |
| Permission denied StreamData | Einmaliger Schreibfehler (11:00:44) | Hat sich selbst gelöst |
| pip install blocked (PEP 668) | Raspberry Pi OS schützt System-Python | venv erstellt |

---

## 💡 Erkenntnisse für das Notizbuch

1. **myAI Bug-Hypothese:** `.py`-Dateien als Download blockieren möglicherweise den Chat. `.txt`/`.md`-Downloads funktionieren problemlos. → Ab jetzt immer `.txt` für Code-Downloads verwenden!
2. **Pi-User ≠ Hostname:** `paul-rppi` ist der User, `RpPi4B-002` ist der Hostname
3. **PEP 668:** Neues Raspberry Pi OS erfordert venv für pip – kein `pip install` global
4. **Bluetooth-Falle:** PlatformIO erkennt Bluetooth-Geräte als Serial Port → BT ausschalten beim Flashen
5. **Spannungsteiler:** 2×200kΩ auf A3 (GPIO4) liefert stabile Werte (3.86–3.91V)

---

## ❓ Offene Fragen / Nächste Schritte

- [ ] **Outdoor-Test:** System draussen mit Solar testen (Lade-/Entladekurve beobachten)
- [ ] **BirdNET-Analyse:** WAV-Dateien durch BirdNET-Analyzer laufen lassen
- [ ] **Credentials auslagern:** WiFi-Passwort in separate `credentials.h` (für GitHub)
- [ ] **GitHub-Upload:** Aktuellen Stand committen
- [ ] **Deep Sleep optimieren:** 5s ist für Tests gut, für Produktion evtl. 30-60s
- [ ] **Dashboard-Erweiterung:** Audio-Player für WAV-Dateien? Aufnahme-Liste?
- [ ] **Alarm:** Low-Battery-Warnung im Dashboard?

---

## 🔑 Briefing für Claude (nächste Session)

> Paul hat das BirdNET Kauzohr v1.1 System vollständig in Betrieb genommen.
> ESP32-S3 (XIAO) nimmt Audio auf, filtert es, und sendet WAV-Dateien an einen
> Raspberry Pi 4B. Das Dashboard auf Port 5001 zeigt Batteriespannung und
> erlaubt Remote-Konfiguration. Alles läuft als Systemd-Service im venv.
> Nächste Schritte: Outdoor-Test, BirdNET-Analyse, GitHub-Upload.
> WICHTIG: Code-Downloads als .txt liefern, NICHT als .py (Bug-Vermeidung)!
