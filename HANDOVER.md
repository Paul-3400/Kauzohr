# HANDOVER.md – BirdNET-Pi Station "Kauzohr"

## Sitzung 15. Juli 2026

Built as a "brain gym" project – keeping the mind sharp through electronics and code. 🧠💪
by Paul and Claude, Anthropic 2026

---

## 🖥️ System-Übersicht

| Komponente     | Details                                  |
| -------------- | ---------------------------------------- |
| Hardware       | Raspberry Pi 4B                          |
| Hostname       | RpPi4B-002                               |
| OS             | Raspberry Pi OS (Bookworm)               |
| IP (LAN)       | 10.0.1.181                               |
| BirdNET-Modell | BirdNET_GLOBAL_6K_V2.4_Model_FP16 (2023) |
| Webserver      | Caddy                                    |
| PHP            | PHP 8.4-FPM                              |
| Datenbank      | SQLite3 (WAL-Modus)                      |

---

## 🔑 Zugangsdaten

| Zugang                     | Details                                              |
| -------------------------- | ---------------------------------------------------- |
| Dashboard                  | `http://10.0.1.181`                                  |
| SSH                        | `ssh paul-rppi@10.0.1.181`                           |
| Advanced Settings User     | `birdnet`                                            |
| Advanced Settings Passwort | `xxxxxx`                                             |
| Passwort in Config         | `~/BirdNET-Pi/birdnet.conf` → `CADDY_PWD=kauzohr4me` |

---

## 📂 Wichtige Verzeichnisse & Dateien

| Pfad                            | Inhalt                                    |
| ------------------------------- | ----------------------------------------- |
| `~/BirdNET-Pi/`                 | Hauptverzeichnis                          |
| `~/BirdNET-Pi/homepage/`        | Web-Frontend (PHP, JS, CSS)               |
| `~/BirdNET-Pi/scripts/`         | Backend-Skripte, config.php, overview.php |
| `~/BirdNET-Pi/scripts/birds.db` | SQLite-Datenbank (WAL-Modus!)             |
| `~/BirdNET-Pi/birdnet.conf`     | Hauptkonfiguration                        |
| `~/BirdNET-Pi/apprise.txt`      | Notification-Konfiguration                |
| `~/BirdNET-Pi/body.txt`         | Notification-Body                         |
| `~/BirdSongs/`                  | Aufnahmen (WAV-Dateien)                   |
| `~/BirdSongs/StreamData/`       | Live-Analysedaten                         |
| `/etc/caddy/Caddyfile`          | Webserver-Konfiguration                   |
| `/etc/birdnet/birdnet.conf`     | Symlink → `~/BirdNET-Pi/birdnet.conf`     |

---

## 🔗 Symlinks (heute erstellt)

| Symlink                              | Ziel                          | Zweck                              |
| ------------------------------------ | ----------------------------- | ---------------------------------- |
| `~/BirdNET-Pi/homepage/scripts`      | `→ ../scripts`                | PHP findet common.php, birds.db    |
| `~/BirdNET-Pi/homepage/overview.php` | `→ ../scripts/overview.php`   | Species-Grid API                   |
| `/etc/birdnet/birdnet.conf`          | `→ ~/BirdNET-Pi/birdnet.conf` | Settings speichern                 |
| `/root/BirdSongs`                    | `→ ~/BirdSongs`               | Analysis-Service findet StreamData |

---

## ⚙️ Services

| Service             | Funktion                            |
| ------------------- | ----------------------------------- |
| `birdnet_recording` | Nimmt Audio auf (alle 15 Sek.)      |
| `birdnet_analysis`  | Analysiert Aufnahmen mit BirdNET-KI |
| `birdnet_stats`     | Streamlit Dashboard (Port 8501)     |
| `birdnet_log`       | GoTTY Log-Viewer (Port 8080)        |
| `caddy`             | Webserver                           |
| `php8.4-fpm`        | PHP FastCGI                         |

### Alle Services sind `enabled` → Autostart nach Stromausfall ✅

---

## 🔧 Bedienungsbefehle

### Services verwalten

```bash
# Status aller BirdNET-Services
sudo systemctl status birdnet_recording birdnet_analysis birdnet_stats birdnet_log --no-pager

# Einzelnen Service neu starten
sudo systemctl restart birdnet_analysis

# Alle stoppen/starten
sudo systemctl stop birdnet_recording birdnet_analysis birdnet_stats birdnet_log
sudo systemctl start birdnet_recording birdnet_analysis birdnet_stats birdnet_log

# Autostart prüfen
sudo systemctl is-enabled birdnet_recording birdnet_analysis birdnet_stats birdnet_log
```

### Logs anschauen

```bash
# Live-Ticker der Analyse
journalctl -u birdnet_analysis -f

# Letzte 30 Zeilen
journalctl -u birdnet_analysis --no-pager -n 30

# Caddy-Logs
journalctl -u caddy --no-pager -n 20

# PHP-FPM Logs
sudo tail -20 /var/log/php8.4-fpm.log
```

### Mikrofon testen

```bash
# 5 Sekunden aufnehmen und abspielen
arecord -d 5 -f S16_LE -r 48000 /tmp/test.wav && aplay /tmp/test.wav
```

### Datenbank

```bash
# Anzahl Erkennungen
sqlite3 ~/BirdNET-Pi/scripts/birds.db "SELECT COUNT(*) FROM detections;"

# Heutige Arten
sqlite3 ~/BirdNET-Pi/scripts/birds.db "SELECT DISTINCT Com_Name FROM detections WHERE Date = date('now');"

# Tabellen anzeigen
sqlite3 ~/BirdNET-Pi/scripts/birds.db ".tables"

# Journal-Modus prüfen (muss "wal" sein!)
sqlite3 ~/BirdNET-Pi/scripts/birds.db "PRAGMA journal_mode;"
```

### Webserver

```bash
# Caddyfile bearbeiten
sudo nano -lmi /etc/caddy/Caddyfile

# Caddy neu laden (ohne Downtime)
sudo systemctl reload caddy

# Caddy-Status
sudo systemctl status caddy --no-pager
```

### Konfiguration

```bash
# birdnet.conf bearbeiten
nano -lmi ~/BirdNET-Pi/birdnet.conf

# Wichtige Parameter anzeigen
grep -E "CONFIDENCE|LATITUDE|LONGITUDE|CADDY_PWD" ~/BirdNET-Pi/birdnet.conf
```

### Netzwerk

```bash
# IP-Adresse anzeigen
hostname -I

# Erreichbarkeit testen (vom Mac)
ping 10.0.1.181

# HTTP-Antwort prüfen
curl -I http://localhost
```

### Wartung

```bash
# Speicherplatz
df -h

# RAM-Auslastung
free -h

# CPU-Temperatur
vcgencmd measure_temp

# System updaten
sudo apt update && sudo apt upgrade -y
```

---

## 🐛 Heute gelöste Probleme

### 1. Weisse Seite im Browser

**Ursache:** `file_server browse` stand VOR `php_fastcgi` im Caddyfile
**Fix:** Reihenfolge geändert – `php_fastcgi` zuerst

### 2. "File not found" (PHP-FPM)

**Ursache:** www-data hatte keinen Zugriff auf `/home/paul-rppi/`
**Fix:** `chmod 755 /home/paul-rppi` + User zur Gruppe hinzugefügt

### 3. require_once(scripts/common.php) Fatal Error

**Ursache:** `homepage/scripts/` Ordner fehlte
**Fix:** `ln -sf /home/paul-rppi/BirdNET-Pi/scripts /home/paul-rppi/BirdNET-Pi/homepage/scripts`

### 4. FileNotFoundError: /root/BirdSongs/StreamData/analyzing_now.txt

**Ursache:** Service läuft als root, sucht unter `/root/`
**Fix:** `sudo ln -sf /home/paul-rppi/BirdSongs /root/BirdSongs` + `mkdir -p ~/BirdSongs/StreamData`

### 5. "Species data unavailable" im Dashboard

**Ursache:** `overview.php` fehlte im homepage-Ordner + "Database is busy"
**Fix:**

- `ln -sf /home/paul-rppi/BirdNET-Pi/scripts/overview.php /home/paul-rppi/BirdNET-Pi/homepage/overview.php`
- `sudo sqlite3 ~/BirdNET-Pi/scripts/birds.db "PRAGMA journal_mode=WAL;"`

### 6. "Database is busy"

**Ursache:** SQLite im DELETE-Modus erlaubt kein gleichzeitiges Lesen+Schreiben
**Fix:** WAL-Modus aktiviert (Service stoppen → WAL setzen → Service starten)

### 7. Settings fwrite() Fatal Error

**Ursache:** `/etc/birdnet/birdnet.conf` nicht beschreibbar + `apprise.txt`/`body.txt` fehlten
**Fix:**

```bash
sudo mkdir -p /etc/birdnet
sudo ln -sf /home/paul-rppi/BirdNET-Pi/birdnet.conf /etc/birdnet/birdnet.conf
sudo touch ~/BirdNET-Pi/apprise.txt ~/BirdNET-Pi/body.txt
sudo chown www-data:www-data ~/BirdNET-Pi/birdnet.conf ~/BirdNET-Pi/apprise.txt ~/BirdNET-Pi/body.txt
sudo chmod 664 ~/BirdNET-Pi/birdnet.conf ~/BirdNET-Pi/apprise.txt ~/BirdNET-Pi/body.txt
```

### 8. Advanced Settings – Passwort ausgesperrt

**Ursache:** Username war `birdnet` (nicht `birdnetpi`) + Hash stimmte nicht
**Fix:** Hash neu generiert mit `caddy hash-password --plaintext "kauzohr4me"` und in Caddyfile eingesetzt

---

## 📊 Aktueller Stand (15. Juli 2026, ~12:00)

| Metrik               | Wert                                                    |
| -------------------- | ------------------------------------------------------- |
| Erkennungen heute    | 150+                                                    |
| Arten heute          | 13+                                                     |
| Lifetime Erkennungen | 187+                                                    |
| Lifetime Arten       | 15+                                                     |
| Top-Art              | Mauersegler (66 Erkennungen)                            |
| Neue Arten           | Hausrotschwanz, Flussuferläufer, Graureiher, Rabenkrähe |

---

## 🔧 Caddyfile (aktuell)

```
http:// {
    root * /home/paul-rppi/BirdNET-Pi/homepage

    encode gzip

    try_files {path} {path}/ /index.php?{query}
    php_fastcgi unix//run/php/php-fpm.sock

    handle /By_Date/* {
        file_server browse
    }
    handle /Charts/* {
        file_server browse
    }

    reverse_proxy /stream localhost:8000
    reverse_proxy /log* localhost:8080
    reverse_proxy /stats* localhost:8501
    reverse_proxy /terminal* localhost:8888

    file_server
}
```

---

## 💡 Feinabstimmungs-Tipps

| Parameter            | Aktuell   | Empfehlung                                   |
| -------------------- | --------- | -------------------------------------------- |
| Confidence Threshold | 0.7 (70%) | Gut zum Start; auf 0.5 senken für mehr Arten |
| Species Occurrence   | 0.03      | Standard OK für Mitteleuropa                 |
| Overlap              | 0.0       | Standard OK                                  |
| Recording Length     | 15 Sek.   | Standard OK                                  |

---

## 🎙️ Mikrofon-Tipps (Draussen)

- Windschutz (Schaumstoff/Fell) verwenden
- Regengeschützt montieren (unter Dachvorsprung)
- Weg von Strassen (Verkehrslärm vermirrt KI)
- USB-Kabel max. 3–5m (aktiver USB-Hub bei längerem Kabel)
- Richtung Garten/Bäume ausrichten

---

## 🔗 Ressourcen

- BirdNET-Team: https://github.com/birdnet-team
- Synature.ai: https://synature.ai/de/
- Paul's GitHub: https://github.com/Paul-3400

---

## 📝 Nächste Schritte

- [ ] Advanced Settings durchgehen (Audio-Gain, Storage)
- [ ] Confidence ggf. anpassen nach ersten Tagen
- [ ] HANDOVER.md auf GitHub pushen
- [ ] Checkpoint nach 1 Woche: Erkennungsrate bewerten
- [ ] Optional: Notifications einrichten (Telegram/Email)

---

*Letzte Aktualisierung: 15. Juli 2026, ~12:00 Uhr*
