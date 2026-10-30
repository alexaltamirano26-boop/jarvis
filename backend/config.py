"""
Zentrale Konfiguration von JARVIS.

Alle geheimen Werte (API-Keys, Passwort-Hash, ...) kommen ausschließlich aus der
Datei `.env` bzw. aus Umgebungsvariablen – niemals direkt aus dem Code.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Projekt-Hauptordner (eine Ebene über `backend/`)
BASE_DIR = Path(__file__).resolve().parent.parent

# .env laden (falls vorhanden). Echte Umgebungsvariablen haben Vorrang.
load_dotenv(BASE_DIR / ".env")

# Preise in US-Dollar pro 1 Mio. Token (Eingabe, Ausgabe) – nur für die Kostenanzeige.
# Stand: Oktober 2026. Bei neuen Modellen einfach hier ergänzen.
MODEL_PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}


def _required(name: str) -> str:
    """Liest eine Pflicht-Variable oder bricht mit einer verständlichen Meldung ab."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"'{name}' fehlt in der .env-Datei. Bitte zuerst 'python scripts/setup.py' ausführen."
        )
    return value


class Settings:
    def __init__(self) -> None:
        # --- KI ---
        self.anthropic_api_key = _required("ANTHROPIC_API_KEY")
        self.model = os.getenv("JARVIS_MODEL", "claude-haiku-5-5")
        # Wie gründlich das Modell nachdenkt: low | medium | high (höher = besser, aber teurer)
        self.effort = os.getenv("JARVIS_EFFORT", "low")
        # Wie viele frühere Nachrichten JARVIS bei jeder Antwort mitliest
        self.history_limit = int(os.getenv("JARVIS_HISTORY_LIMIT", "30"))

        # --- Persönliches ---
        self.user_name = os.getenv("JARVIS_USER_NAME", "Alex")
        self.timezone = os.getenv("JARVIS_TIMEZONE", "Europe/Berlin")

        # --- Sicherheit ---
        self.password_hash = _required("JARVIS_PASSWORD_HASH")
        self.secret_key = _required("JARVIS_SECRET_KEY")
        # Im Internet (HTTPS) auf "true" setzen, lokal "false" lassen
        self.secure_cookies = os.getenv("JARVIS_SECURE_COOKIES", "false").lower() == "true"

        # --- Datenbank ---
        default_db = (BASE_DIR / "data" / "jarvis.db").as_posix()
        self.database_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db}")


settings = Settings()
