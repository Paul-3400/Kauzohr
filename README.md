# 🦉 Kauzohr – Vogelstimmen-Erkennungsstation

Eine 24/7-Vogelstimmen-Erkennungsstation basierend auf BirdNET-Pi Enhanced,
betrieben auf einem Raspberry Pi 4B.

Built as a "brain gym" project – keeping the mind sharp through electronics and code. 🧠💪
by Paul and Claude, Anthropic 2026

---

## 🎯 Projektziel

Automatische Erkennung und Dokumentation von Vogelstimmen in meiner Umgebung.
Langfristig: Saisonale Muster erkennen, Artenvielfalt dokumentieren und
mit der Community teilen.

---

## 🛠️ Hardware

| Komponente  | Modell                       | Bemerkung                 |
| ----------- | ---------------------------- | ------------------------- |
| Computer    | Raspberry Pi 4B (RpPi4B-002) | 64-bit RaspiOS            |
| Mikrofon    | EM272Z1 Lavalier (micverve)  | 3.5mm Klinke              |
| Soundkarte  | UGREEN US205 USB 2.0         | Extern                    |
| USV         | Waveshare UPS HAT            | Für Pi                    |
| Solarregler | Waveshare MPPT               | Mit Akkus                 |
| Solarpanel  | 10W                          | Für spätere Outdoor-Phase |

---

## 💾 Software

| Komponente | Version                                  | Quelle                                                       |
| ---------- | ---------------------------------------- | ------------------------------------------------------------ |
| OS         | Debian GNU/Linux 13 (trixie) 64-bit      | DEBIAN_VERSION_FULL=13.6                                     |
| Kernel     | 6.18.38-v8+ #1989 SMP PREEMPT aarch64    | Mon Jul 13 13:54:48 BST 2026                                 |
| Firmware   | f68405bcf704b03511bf1656e86924e8cd6398b4 | Jul 1 2026                                                   |
| Erkennung  | BirdNET-Pi Enhanced                      | [GitHub](https://github.com/zach7036/BirdNET-Pi-Enhanced-Version) |

---

## 📡 Aufbau

### Phase 1: Indoor-Testbetrieb (aktuell)

- Pi steht drinnen
- Mikrofon via USB-Kabel direkt angeschlossen
- Ziel: System kennenlernen, Software konfigurieren

### Phase 2: Outdoor mit Kabel

- Mikrofon draussen im Wetterschutz
- Verbindung via geschirmtem Kabel / aktiver USB-Verlängerung
- Pi bleibt drinnen

### Phase 3: Outdoor mit Funk (geplant)

- Pi Zero 2W als WiFi-Audio-Streamer draussen
- Solarbetrieb mit Waveshare MPPT + 10W Panel
- Pi 4B drinnen empfängt Audio-Stream

---

## 📂 Repository-Struktur

```
kauzohr/
├── README.md
├── docs/           # Dokumentation, Anleitungen
├── config/         # Konfigurationsdateien
├── scripts/        # Hilfs-Skripte
└── logs/           # Checkpoint-Zusammenfassungen
```

---

## 📝 Logbuch

| Datum      | Aktion                                                       |
| ---------- | ------------------------------------------------------------ |
| 2026-07-14 | Projekt gestartet, Pi4B-002 ins Netz gebracht, System aktualisiert |

---

## 🔗 Ressourcen

- [BirdNET-Pi Enhanced](https://github.com/zach7036/BirdNET-Pi-Enhanced-Version)
- [BirdNET Team](https://github.com/birdnet-team)
- [Synature AI](https://synature.ai/de/)

---

## 📜 Lizenz

Dieses Projekt dient ausschliesslich privaten, nicht-kommerziellen Zwecken.
