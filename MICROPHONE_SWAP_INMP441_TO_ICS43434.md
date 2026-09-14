# 🎤 Mikrofon-Tausch: INMP441 → ICS-43434 (Kauzohr-Projekt)

> **Erstellt am**: 14. September 2026
> **Projekt**: [Kauzohr (BirdNET-Pi Enhanced)](https://github.com/Paul-3400/Kauzohr)
> **Zweck**: Anleitung für den Austausch des INMP441 gegen ICS-43434 in der Vogelstimmen-Erkennungsstation.
> **Konfidenz**: Hoch (basierend auf Datenblättern, BirdNET-Pi-Erfahrung und typischen MEMS-Fallstricken).

---

## 📌 Übersicht
Der **ICS-43434** ist ein **besseres Upgrade** für dein Kauzohr-Projekt:
✅ **Höherer SNR** (65 dB vs. 61 dB) → bessere Erkennung leiser Vogelstimmen.
✅ **Größerer Dynamikumfang** (130 dB SPL vs. 120 dB) → verträgt lautere Geräusche.
✅ **Präzisere Sensitivität** (±1 dB vs. ±3 dB) → konstantere Lautstärke.
✅ **Günstiger** (~3–7 € vs. 5–10 €).
✅ **Flexibler** (unterstützt **PDM UND I²S**).

⚠️ **Achtung**: **SD-Pin (Shutdown) muss auf HIGH (3.3V) liegen, sonst ist das Mikrofon AUS!**

---

## 🔍 Technischer Vergleich

| Kriterium | INMP441 | ICS-43434 | Hinweise |
|----------|---------|-----------|---------|
| **Typ** | Digitales MEMS-Mikrofon | Digitales MEMS-Mikrofon | Beide unterstützen I²S/PDM, aber ICS-43434 ist flexibler. |
| **Sensitivität** | -26 dBFS ±3 dB | -26 dBFS ±1 dB | ICS-43434 ist präziser. |
| **Max. Schalldruck** | 120 dB SPL | 130 dB SPL | ICS-43434 verträgt lautere Geräusche. **INMP441 verzerrt ab 120 dB!** |
| **SNR (A-gewichtet)** | 61 dB | 65 dB | ICS-43434 ist rauschärmer → bessere Erkennung von Zaunkönig, Rotkehlchen etc. |
| **Frequenzbereich** | 20 Hz – 20 kHz | 20 Hz – 20 kHz | ICS-43434 hat bessere Hochfrequenz-Response. |
| **Stromverbrauch** | 1.6 mA | 1.7 mA | Minimal höher, aber vernachlässigbar. |
| **Spannungsversorgung** | 3.3V | 1.6V – 3.6V | ICS-43434 ist flexibler, aber 3.3V sind kompatibel. |
| **I²S-Modus** | Nur PDM | PDM ODER I²S | **WICHTIG**: ICS-43434 unterstützt beide Modi! INMP441 nur PDM. |
| **Datenformat** | 24 Bit (PDM) | 16/24/32 Bit (I²S) | Software-Anpassung nötig, falls I²S-Modus genutzt wird. |
| **Pinbelegung** | L/R, CLK, DATA, GND, VDD | L/R, SCLK, SDATA, GND, VDD, SD | **NEU: SD-Pin (Shutdown) muss auf HIGH liegen!** |
| **Abmessungen** | 3.5 × 2.65 × 0.98 mm | 3.76 × 2.95 × 1.1 mm | ICS-43434 ist etwas größer → mechanische Passform prüfen! |

---

## ⚠️ Die 5 größten Fallstricke

### 🔴 1. Shutdown-Pin (SD) des ICS-43434
- **Problem**: Der ICS-43434 hat einen **aktiven LOW-Shutdown-Pin (SD)**. Standardmäßig ist das Mikrofon **AUS**, wenn SD nicht auf **HIGH (3.3V)** liegt!
- **Lösung**:
  - SD mit **3.3V verbinden** (einfachste Lösung, z. B. direkt an VDD).
  - Oder: SD mit einem **GPIO-Pin** verbinden und per Software auf HIGH setzen.
  - ACHTUNG: Wenn SD offen (floating) bleibt, kann das Mikrofon unvorhersehbar ein/ausgeschaltet werden!

### 🔴 2. I²S vs. PDM – Kompatibilität mit BirdNET-Pi
- **Problem**: INMP441 gibt nur **PDM** aus. ICS-43434 unterstützt **PDM ODER I²S**. BirdNET-Pi erwartet standardmäßig **PDM**.
- **Lösung**:
  - **Option 1 (empfohlen)**: ICS-43434 im **PDM-Modus** betreiben → **keine Code-Anpassung nötig**.
  - **Option 2**: ICS-43434 im **I²S-Modus** betreiben (effizienter, aber Anpassungen nötig):
    - In ~/.asoundrc oder /etc/asound.conf:
      pcm.ics43434 {
          type hw
          card 1
          device 0
          format S32_LE
          rate 48000
          channels 1
      }
    - In BirdNET-Pi config.ini:
      [audio]
      input_device = ics43434
      sample_format = S32LE
    - Raspberry Pi: I²S-Treiber aktivieren:
      sudo raspi-config -> Interface Options -> I2S Audio -> Enable

### 🔴 3. Sensitivitätsunterschiede
- **Problem**: ICS-43434 kann lauter aufnehmen (130 dB SPL vs. 120 dB SPL). Folge: Aufzeichnungen können zu laut (Clipping) oder zu leise sein.
- **Lösung**:
  - Testaufnahme machen:
    arecord -D plughw:1,0 -f S32_LE -r 48000 -c 1 -d 10 test.wav
    aplay test.wav
  - Gain anpassen in BirdNET-Pi config.ini:
    [audio]
    gain = -3

### 🔴 4. Pinbelegung – Falsche Verdrahtung!
- **Problem**: Die Pinbelegung ist nicht 1:1 kompatibel! ICS-43434 hat zusätzlich den SD-Pin.
- **Lösung**: Doppelt prüfen, ob SD mit 3.3V verbunden ist, L/R korrekt ist, CLK und DATA nicht vertauscht sind.

### 🔴 5. Mechanische Passform
- **Problem**: ICS-43434 ist etwas größer (3.76 × 2.95 mm vs. 3.5 × 2.65 mm).
- **Lösung**: Prüfe, ob der Footprint auf deiner Platine passt.

---

## ✅ Schritt-für-Schritt-Anleitung

### Vorbereitung
1. Backup deiner aktuellen Konfiguration:
   cp ~/.asoundrc ~/.asoundrc_backup
   cp /etc/asound.conf /etc/asound.conf_backup
   cp /home/pi/BirdNET-Pi/config.ini /home/pi/BirdNET-Pi/config.ini_backup

### Schritt 1: Verdrahtung (Raspberry Pi)

ICS-43434 Pin | Raspberry Pi Pin (BCM) | Funktion
---|---|---
VDD | 3.3V (Pin 1) | Stromversorgung
GND | GND (Pin 6) | Masse
SCLK | GPIO18 (Pin 12) | I²S-Takt
SDATA | GPIO20 (Pin 38) | I²S-Daten
L/R | GPIO19 (Pin 35) | Linkes/Rechtes Signal
SD | 3.3V (Pin 1) | Shutdown (MUSS HIGH sein!)

### Schritt 2: I²S-Treiber aktivieren (falls I²S-Modus)
Raspberry Pi:
   sudo raspi-config
   Interface Options -> I2S Audio -> Enable -> Reboot

### Schritt 3: ALSA-Konfiguration (falls I²S-Modus)
Bearbeite ~/.asoundrc:
pcm.ics43434 {
    type hw
    card 1
    device 0
    format S32_LE
    rate 48000
    channels 1
}

Teste mit:
arecord -D ics43434 -f S32_LE -r 48000 -c 1 -d 10 test.wav

### Schritt 4: BirdNET-Pi Konfiguration
Bearbeite /home/pi/BirdNET-Pi/config.ini:

audio
input_device = ics43434
sample_format = S32LE
sample_rate = 48000
channels = 1
gain = -3

Neustart:
sudo systemctl restart birdnet

### Schritt 5: Testen und Kalibrieren
1. Aufnahme testen:
   arecord -D ics43434 -f S32_LE -r 48000 -c 1 -d 10 test.wav
2. BirdNET-Pi-Logs prüfen:
   journalctl -u birdnet -f

---

## 🎯 Praktische Tipps für Kauzohr

### Outdoor-Einsatz
- Windschutz: Nutze eine Windschutz-Kappe oder Röhrchen mit Löchern.
- Positionierung: 1-2 Meter über Boden, Mikrofon nach Süden ausrichten.

### Stromversorgung
- Nutze einen stabilen 3.3V-Regler (z. B. AMS1117-3.3).
- Kondensatoren (10 µF + 0.1 µF) zwischen VDD und GND des Mikrofons.

### Rauschen reduzieren
- Kurze, abgeschirmte Kabel verwenden.

---

## 📊 Performance-Vergleich

Metrik | INMP441 | ICS-43434 | Besser für Kauzohr?
---|---|---|---
SNR | 61 dB | 65 dB | Ja
Max. Schalldruck | 120 dB | 130 dB | Ja
Sensitivität | ±3 dB | ±1 dB | Ja
Preis | ~5-10 EUR | ~3-7 EUR | Ja

Fazit: Der ICS-43434 ist in fast allen Belangen besser für Vogelstimmen-Erkennung!

---

## Häufige Probleme und Lösungen

Problem | Ursache | Lösung
---|---|---
Kein Sound | SD-Pin auf LOW/floating | SD auf 3.3V oder GPIO-HIGH
Rauschen | Falsche Gain | Gain in config.ini auf -3 bis -6 dB
Clipping | Zu laute Umgebung | Mikrofon weiter weg oder Gain reduzieren
Keine Erkennung | Falsches Datenformat | ALSA-Konfig auf S32_LE/S16_LE anpassen
Mikrofon nicht erkannt | Falsche I2S-Pins | Pinbelegung prüfen

---

## Ressourcen
- [INMP441 Datasheet](https://www.invensense.com/products/audio/inmp441/)
- [ICS-43434 Datasheet](https://www.ti.com/lit/ds/symlink/ics-43434.pdf)
- [BirdNET-Pi GitHub](https://github.com/mcguirepr89/BirdNET-Pi)
- [Adafruit ICS-43434 Breakout](https://www.adafruit.com/product/4696)

---

Notiz für [Paul Simmen](https://github.com/Paul-3400) – Kauzohr-Projekt.