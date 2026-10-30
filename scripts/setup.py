"""
Einrichtungs-Assistent für JARVIS.

Erstellt bzw. aktualisiert die Datei `.env`:
  - fragt deinen Anthropic-API-Key ab
  - fragt dein JARVIS-Passwort ab und speichert nur den Hash (nie das Passwort selbst)
  - erzeugt einen zufälligen geheimen Schlüssel für die Login-Cookies

Aufruf im Projektordner:  python scripts/setup.py
Du kannst das Skript jederzeit erneut ausführen, z. B. um das Passwort zu ändern.
"""
import re
import secrets
import shutil
from getpass import getpass
from pathlib import Path

from argon2 import PasswordHasher

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
EXAMPLE_FILE = BASE_DIR / ".env.example"


def read_value(text: str, key: str) -> str:
    match = re.search(rf"^{key}=(.*)$", text, flags=re.MULTILINE)
    return match.group(1).strip().strip("'\"") if match else ""


def set_value(text: str, key: str, value: str) -> str:
    """Ersetzt die Zeile KEY=... oder hängt sie an, falls sie fehlt."""
    line = f"{key}={value}"
    if re.search(rf"^{key}=", text, flags=re.MULTILINE):
        return re.sub(rf"^{key}=.*$", lambda _: line, text, flags=re.MULTILINE)
    return text.rstrip("\n") + "\n" + line + "\n"


def main() -> None:
    print("=== JARVIS Einrichtung ===\n")

    if not ENV_FILE.exists():
        shutil.copy(EXAMPLE_FILE, ENV_FILE)
        print("Neue .env aus der Vorlage erstellt.")
    text = ENV_FILE.read_text(encoding="utf-8")

    # 1) API-Key
    if read_value(text, "ANTHROPIC_API_KEY"):
        answer = input("Ein API-Key ist schon hinterlegt. Ersetzen? (j/N): ").strip().lower()
        replace_key = answer == "j"
    else:
        replace_key = True
    if replace_key:
        key = getpass("Anthropic API-Key einfügen (Eingabe bleibt unsichtbar): ").strip()
        if not key.startswith("sk-ant-"):
            print("Hinweis: Der Key beginnt normalerweise mit 'sk-ant-'. Bitte prüfen.")
        text = set_value(text, "ANTHROPIC_API_KEY", key)

    # 2) Passwort
    if read_value(text, "JARVIS_PASSWORD_HASH"):
        answer = input("Ein Passwort ist schon gesetzt. Ändern? (j/N): ").strip().lower()
        set_password = answer == "j"
    else:
        set_password = True
    if set_password:
        while True:
            pw = getpass("Neues JARVIS-Passwort (mind. 10 Zeichen): ")
            if len(pw) < 10:
                print("Zu kurz – bitte mindestens 10 Zeichen.")
                continue
            if getpass("Passwort wiederholen: ") != pw:
                print("Die Passwörter stimmen nicht überein.")
                continue
            break
        # In einfachen Anführungszeichen, damit die $-Zeichen im Hash nicht umgedeutet werden.
        text = set_value(text, "JARVIS_PASSWORD_HASH", f"'{PasswordHasher().hash(pw)}'")

    # 3) Geheimer Schlüssel für Cookies (nur beim ersten Mal)
    if not read_value(text, "JARVIS_SECRET_KEY"):
        text = set_value(text, "JARVIS_SECRET_KEY", secrets.token_urlsafe(48))

    ENV_FILE.write_text(text, encoding="utf-8")
    print("\nFertig! Die .env ist eingerichtet. Starte JARVIS jetzt mit start.bat")


if __name__ == "__main__":
    main()
