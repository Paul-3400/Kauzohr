# 🦉 BirdNET-Pi Enhanced – Handover & Betriebsanleitung

## Projekt: Kauzohr – Vogelstimmen-Erkennung auf Raspberry Pi 4B

*Built as a "brain gym" project – keeping the mind sharp through electronics and code. 🧠💪*  
*by Paul and Claude, Anthropic 2026*

---

## 📋 System-Übersicht

| Komponente     | Details                                   |
| -------------- | ----------------------------------------- |
| Hardware       | Raspberry Pi 4B ("RpPi4B-002")            |
| OS             | Raspberry Pi OS (Trixie, aarch64, 64-bit) |
| Python         | 3.13                                      |
| BirdNET-Modell | BirdNET_GLOBAL_6K_V2.4_Model_FP16         |
| Webserver      | Caddy                                     |
| Streaming      | Icecast2                                  |
| PHP            | 8.4-FPM                                   |
| Zugang         | Raspberry Pi Connect (Remote Shell)       |
| Standort       | Burgdorf BE (47.056640, 7.61539)          |

---

## 🌐 Zugriff auf das Dashboard

| Zugang      | Adresse                                              |
| ----------- | ---------------------------------------------------- |
| Lokal (LAN) | `http://10.0.1.181`                                  |
| Hostname    | `http://RpPi4B-002.local` (falls avahi funktioniert) |

---

## 📂 Wichtige Verzeichnisse & Dateien

| Pfad                        | Inhalt                              |
| --------------------------- | ----------------------------------- |
| `~/BirdNET-Pi/`             | Hauptverzeichnis (Repo)             |
| `~/BirdNET-Pi/birdnet.conf` | Konfigurationsdatei                 |
| `~/BirdNET-Pi/homepage/`    | Web-Interface (PHP)                 |
| `~/BirdNET-Pi/scripts/`     | Alle Skripte                        |
| `~/BirdNET-Pi/model/`       | KI-Modell & Labels                  |
| `~/BirdNET-Pi/templates/`   | Service-Templates                   |
| `~/BirdSongs/`              | Aufgenommene Audio-Dateien          |
| `~/BirdSongs/Extracted/`    | Erkannte Vogelstimmen-Clips         |
| `/etc/caddy/Caddyfile`      | Webserver-Konfiguration             |
| `/birdnet.conf`             | Symlink → ~/BirdNET-Pi/birdnet.conf |

---

## 🔧 Wichtige Befehle zur Bedienung

### 🟢 Services starten / stoppen / Status

```bash
# Status aller BirdNET-Dienste
sudo systemctl status birdnet* --no-pager

# Einzelnen Service neu starten
sudo systemctl restart birdnet_recording
sudo systemctl restart birdnet_analysis
sudo systemctl restart birdnet_stats
sudo systemctl restart birdnet_log

# Alle BirdNET-Dienste stoppen
sudo systemctl stop birdnet_recording birdnet_analysis birdnet_stats birdnet_log

# Alle BirdNET-Dienste starten
sudo systemctl start birdnet_recording birdnet_analysis birdnet_stats birdnet_log

# Webserver
sudo systemctl restart caddy
sudo systemctl restart php8.4-fpm
sudo systemctl restart icecast2
```

### 📊 Logs & Diagnose

```bash
# BirdNET-Analyse-Log live verfolgen
journalctl -u birdnet_analysis -f

# Recording-Log
journalctl -u birdnet_recording -f

# Caddy-Fehler
sudo journalctl -u caddy --no-pager -n 30

# PHP-FPM Fehler
sudo tail -30 /var/log/php8.4-fpm.log

# Allgemeine System-Logs
journalctl --since "1 hour ago" --no-pager
```

### 🎙️ Mikrofon testen

```bash
# Verfügbare Aufnahmegeräte anzeigen
arecord -l

# 5 Sekunden Testaufnahme
arecord -d 5 -f S16_LE -r 48000 /tmp/test.wav

# Testaufnahme abspielen (nur mit angeschlossenem Audio-Ausgang)
aplay /tmp/test.wav

# Aufnahme-Pegel live beobachten
arecord -f S16_LE -r 48000 -d 10 -vv /dev/null
```

### ⚙️ Konfiguration ändern

```bash
# Konfigdatei bearbeiten
nano -lmi ~/BirdNET-Pi/birdnet.conf

# Nach Änderungen: Services neu starten
sudo systemctl restart birdnet_recording birdnet_analysis
```

### 💾 Datenbank

```bash
# Datenbank neu erstellen (VORSICHT: löscht Erkennungen!)
sudo bash ~/BirdNET-Pi/scripts/createdb.sh

# Datenbank-Grösse prüfen
ls -lh ~/BirdNET-Pi/scripts/birds.db 2>/dev/null || find ~/BirdNET-Pi -name "*.db" -exec ls -lh {} \;
```

### 🔄 System-Wartung

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Speicherplatz prüfen
df -h

# Alte Aufnahmen aufräumen (älter als 30 Tage)
find ~/BirdSongs/Extracted -mtime +30 -delete

# Raspberry Pi Temperatur prüfen
vcgencmd measure_temp

# Uptime & Last
uptime

# Neustart
sudo reboot
```

### 🌐 Netzwerk

```bash
# IP-Adresse anzeigen
hostname -I

# Netzwerk-Status
ip addr show

# Pi von aussen erreichbar? (auf anderem Gerät im LAN)
ping RpPi4B-002.local
```

---

## 📝 Konfigurations-Parameter (birdnet.conf)

| Parameter        | Aktueller Wert                    | Beschreibung                         |
| ---------------- | --------------------------------- | ------------------------------------ |
| LATITUDE         | 47.056640                         | Breitengrad Burgdorf                 |
| LONGITUDE        | 7.61539                           | Längengrad Burgdorf                  |
| CONFIDENCE       | 0.7                               | Min. Erkennungs-Sicherheit (0.0–1.0) |
| SENSITIVITY      | 1.25                              | Mikrofon-Empfindlichkeit (0.5–1.5)   |
| RECORDING_LENGTH | 15                                | Aufnahme-Chunks in Sekunden          |
| DATABASE_LANG    | de                                | Artnamen auf Deutsch                 |
| MODEL            | BirdNET_GLOBAL_6K_V2.4_Model_FP16 | KI-Modell                            |

### Tipps zur Feinabstimmung:

| Situation                | Anpassung                                             |
| ------------------------ | ----------------------------------------------------- |
| Zu viele Fehlerkennungen | CONFIDENCE erhöhen (z.B. 0.8)                         |
| Zu wenige Erkennungen    | CONFIDENCE senken (z.B. 0.5) oder SENSITIVITY erhöhen |
| Laute Umgebung (Strasse) | SENSITIVITY senken (z.B. 1.0)                         |
| Leise Umgebung (Wald)    | SENSITIVITY erhöhen (z.B. 1.5)                        |

---

## ⚡ Autostart nach Stromausfall

Alle Services sind **enabled** – sie starten automatisch mit dem Pi:

```bash
# Prüfen ob Autostart aktiv
sudo systemctl is-enabled birdnet_recording birdnet_analysis birdnet_stats birdnet_log
# Erwartete Ausgabe: 4x "enabled"
```

---

## 🛠️ Bekannte Workarounds (aus der Installation)

| Problem                        | Lösung                                                       |
| ------------------------------ | ------------------------------------------------------------ |
| dpkg hängt bei rpi-connect     | `nohup sudo dpkg --configure rpi-connect &` (killt Shell!)   |
| Pfade unter /root fehlen       | Symlinks: `sudo ln -sf ~/BirdNET-Pi /root/BirdNET-Pi`        |
| PHP "File not found"           | `chmod 755 /home/paul-rppi` + www-data zur Gruppe hinzufügen |
| homepage findet scripts/ nicht | `ln -sf ~/BirdNET-Pi/scripts ~/BirdNET-Pi/homepage/scripts`  |
| Caddy zeigt weisse Seite       | Caddyfile: `php_fastcgi` VOR `file_server` + `try_files` Direktive |

---

## 🔗 Ressourcen

| Link                            | Beschreibung              |
| ------------------------------- | ------------------------- |
| https://github.com/birdnet-team | BirdNET Original-Team     |
| https://synature.ai/de/         | synature.ai               |
| https://github.com/Paul-3400    | Paul's GitHub-Profil      |
| https://rpltd.co/rpi-connect    | Raspberry Pi Connect Doku |

---

## 📅 Installations-Datum

**14. Juli 2026**

---

## 🦉 Viel Freude mit deiner Vogelstation!

> "Your station is still learning what a normal day sounds like here."  
> – BirdNET-Pi Dashboard

Die Station lauscht. Die Vögel singen. Das Gehirn bleibt fit. 🧠💪🎙️
