# J.A.R.V.I.S. – Persönlicher KI-Assistent

Dein persönlicher Assistent mit Claude als Gehirn. Er läuft im Browser und auf dem Handy, später auch über Telegram und per Sprache.

**Aktueller Stand: Phase 1** – Text-Chat mit Login, Gesprächsverlauf und Kostenanzeige.

| Phase | Inhalt | Status |
|---|---|---|
| 1 | Text-Chat, Login, Gesprächsverlauf | ✅ |
| 2 | Gedächtnis (Fakten über dich) | ⏳ |
| 3 | Tools: Erinnerungen, Notizen, Wetter, Websuche | ⏳ |
| 4 | Notion, Google Kalender, Gmail | ⏳ |
| 5 | Sprache (Ein- und Ausgabe) | ⏳ |
| 6 | Telegram-Bot | ⏳ |
| 7 | Online-Deployment + PWA | ⏳ |

---

## Einrichtung unter Windows

### 1. Programme installieren (einmalig)

1. **Python 3.12 oder neuer**: <https://www.python.org/downloads/>
   ⚠️ Im Installer unbedingt **„Add python.exe to PATH“** anhaken.
2. **Git**: <https://git-scm.com/download/win> (Standardeinstellungen reichen)
3. Empfohlen: **VS Code** als Editor: <https://code.visualstudio.com/>

### 2. Anthropic-API-Key besorgen

1. Auf <https://console.anthropic.com> registrieren.
2. Unter **Billing** Guthaben aufladen. Der kleinste Betrag reicht für Monate.
3. Unter **API Keys** → **Create Key** einen Key erstellen und kopieren (beginnt mit `sk-ant-`).
   Der Key wird nur einmal angezeigt.

### 3. Projekt herunterladen

PowerShell öffnen (Windows-Taste → „PowerShell“) und eingeben:

```powershell
cd $HOME\Documents
git clone https://github.com/DEIN-NAME/DEIN-REPO.git jarvis
cd jarvis
```

### 4. Starten

Im Ordner `jarvis` auf **`start.bat`** doppelklicken.

Beim ersten Start passiert automatisch:
- Eine eigene Python-Umgebung (`.venv`) wird angelegt und alle Pakete installiert (dauert 1–2 Minuten).
- Der Einrichtungs-Assistent fragt nach deinem **API-Key** und einem **Passwort** für JARVIS.

Danach öffnet sich <http://localhost:8000> im Browser. Dort meldest du dich mit deinem Passwort an.

> Passwort ändern oder Key tauschen: `.venv\Scripts\python scripts\setup.py` im Projektordner ausführen.

---

## Einstellungen (`.env`)

Alle Einstellungen stehen in der Datei `.env`. Öffne sie mit VS Code oder dem Editor.

| Variable | Bedeutung |
|---|---|
| `ANTHROPIC_API_KEY` | Dein Claude-Key |
| `JARVIS_MODEL` | `claude-haiku-5-5` (günstig), `claude-sonnet-5-5` oder `claude-opus-5-5` (am stärksten) |
| `JARVIS_EFFORT` | Denktiefe `low` / `medium` / `high`. Höher heißt gründlicher, aber teurer. |
| `JARVIS_HISTORY_LIMIT` | Wie viele frühere Nachrichten JARVIS mitliest |
| `JARVIS_USER_NAME` | Wie JARVIS dich nennt |
| `JARVIS_TIMEZONE` | Deine Zeitzone |
| `JARVIS_PASSWORD_HASH` | Verschlüsseltes Passwort (wird vom Setup gesetzt) |
| `JARVIS_SECRET_KEY` | Schlüssel für Login-Cookies (wird vom Setup gesetzt) |
| `JARVIS_SECURE_COOKIES` | Erst beim Online-Betrieb mit HTTPS auf `true` setzen |

Nach Änderungen JARVIS neu starten: im Fenster **Strg+C** drücken, dann `start.bat` erneut ausführen.

**Die `.env` niemals hochladen oder weitergeben.** Sie steht deshalb in `.gitignore`.

---

## Projektaufbau

```
jarvis/
├── backend/
│   ├── main.py            # Startpunkt: Server, Sicherheits-Header, Login-Cookies
│   ├── config.py          # liest die .env, Modellpreise
│   ├── auth.py            # Passwortprüfung, Sperre nach Fehlversuchen
│   ├── brain/
│   │   ├── agent.py       # Gespräch an Claude schicken, Antwort zurückgeben
│   │   └── persona.py     # Persönlichkeit von JARVIS  ← hier anpassen!
│   ├── memory/
│   │   ├── models.py      # Datenbank-Tabellen
│   │   └── store.py       # Datenbank lesen/schreiben
│   ├── channels/
│   │   └── web.py         # API für die Web-App
│   └── tools/             # (ab Phase 3) ein Plugin pro Fähigkeit
├── frontend/              # Web-App (HTML/CSS/JS, kein Build nötig)
├── scripts/setup.py       # Einrichtungs-Assistent
├── data/jarvis.db         # deine Datenbank (wird automatisch angelegt)
├── logs/jarvis.log        # Server-Log
└── start.bat              # Start per Doppelklick
```

### Ablauf einer Nachricht

```
Browser ──POST /api/chat──▶ web.py ──Login prüfen──▶ agent.py
                                                       │ Persona + letzte Nachrichten laden
                                                       ▼
                                                 Claude API
                                                       │
            ◀──────── Antwort ◀── speichern (Verlauf + Kosten) ◀┘
```

---

## Sicherheit

- **Login:** Nur mit deinem Passwort. Gespeichert wird nur ein Argon2-Hash, nie das Passwort selbst.
- **Brute-Force-Schutz:** Nach 5 Fehlversuchen ist der Login 15 Minuten gesperrt.
- **Cookies:** signiert, `HttpOnly`, `SameSite=Strict`, 30 Tage gültig.
- **Keys:** stehen nur in der `.env`, nie im Code.
- **Protokoll:** Logins und Fehlversuche landen in der Tabelle `actionlog`. Ab Phase 3 kommen alle Tool-Aktionen dazu.
- **Lokal:** Der Server lauscht nur auf `127.0.0.1`. Andere Geräte im Netzwerk kommen nicht dran. Den Zugriff von unterwegs richten wir in Phase 7 sicher ein.

## Kosten

Oben rechts im Chat stehen die KI-Kosten des laufenden Monats in US-Dollar. Bei normaler Nutzung mit `claude-haiku-5-5` liegen sie bei etwa **1 $ pro Monat**.

## Probleme?

| Problem | Lösung |
|---|---|
| `py` wird nicht erkannt | Python neu installieren und „Add to PATH“ anhaken |
| „API-Key wird nicht akzeptiert“ | Key in `.env` prüfen (kein Leerzeichen, beginnt mit `sk-ant-`) |
| „Guthaben aufgebraucht“ | In der Anthropic Console unter Billing aufladen |
| Passwort vergessen | `.venv\Scripts\python scripts\setup.py` → Passwort ändern |
| Port 8000 belegt | In `start.bat` beide `8000` durch z. B. `8001` ersetzen |
