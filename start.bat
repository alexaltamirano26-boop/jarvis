@echo off
REM Startet JARVIS unter Windows. Doppelklick genuegt.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [JARVIS] Erster Start: richte Python-Umgebung ein ...
    py -m venv .venv || goto :error
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)

if not exist ".env" (
    echo [JARVIS] Keine .env gefunden - starte Einrichtung ...
    ".venv\Scripts\python.exe" scripts\setup.py || goto :error
)

echo [JARVIS] Starte auf http://localhost:8000  (Beenden mit Strg+C)
start "" http://localhost:8000
".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
exit /b 0

:error
echo [JARVIS] Es ist ein Fehler aufgetreten. Siehe Meldung oben.
pause
exit /b 1
