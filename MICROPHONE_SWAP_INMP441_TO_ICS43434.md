# Mikrofon-Tausch INMP441 zu ICS-43434

Projekt: Kauzohr
Erstellt: 14. September 2026

Uebersicht:
Der ICS-43434 ist ein Upgrade fuer dein Kauzohr-Projekt:
- Hoherer SNR (65 dB vs 61 dB)
- Groesserer Dynamikumfang (130 dB SPL vs 120 dB)
- Praezisere Sensitivitaet
- Guenstiger

Achtung: SD-Pin muss auf HIGH (3.3V) liegen!

Verdrahtung (Raspberry Pi):
VDD -> 3.3V (Pin 1)
GND -> GND (Pin 6)
SCLK -> GPIO18 (Pin 12)
SDATA -> GPIO20 (Pin 38)
L/R -> GPIO19 (Pin 35)
SD -> 3.3V (MUSS HIGH sein!)

BirdNET-Pi Konfiguration:
input_device = ics43434
sample_format = S32LE
sample_rate = 48000
channels = 1
gain = -3

Fazit: Wechsel lohnt sich!