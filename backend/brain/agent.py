"""
Das "Gehirn" von JARVIS: schickt das Gespräch an Claude und gibt die Antwort zurück.

Phase 1: reiner Text-Chat mit Gesprächsverlauf.
Ab Phase 3 kommt hier die Tool-Schleife dazu (Claude ruft Werkzeuge auf).
"""
import logging

import anthropic

from backend.brain.persona import build_system_prompt
from backend.config import settings
from backend.memory import store

logger = logging.getLogger("jarvis.agent")

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class JarvisError(Exception):
    """Fehler mit einer Meldung, die direkt im Chat angezeigt werden darf."""


def _build_messages(conversation_id: int, user_text: str) -> list[dict]:
    """Baut die Nachrichtenliste für Claude: bisheriger Verlauf + neue Nachricht."""
    history = store.get_recent_messages(conversation_id, settings.history_limit)
    messages = [{"role": m.role, "content": m.content} for m in history]
    # Claude erwartet, dass das Gespräch mit einer Nutzer-Nachricht beginnt.
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    messages.append({"role": "user", "content": user_text})
    return messages


def reply(user_text: str, channel: str = "web") -> str:
    """Beantwortet eine Nachricht und speichert beide Seiten im Gesprächsverlauf."""
    conversation_id = store.get_current_conversation_id()
    messages = _build_messages(conversation_id, user_text)

    try:
        response = client.messages.create(
            model=settings.model,
            max_tokens=8000,
            system=build_system_prompt(),
            output_config={"effort": settings.effort},
            messages=messages,
        )
    except anthropic.AuthenticationError:
        raise JarvisError("Mein API-Key wird nicht akzeptiert. Bitte ANTHROPIC_API_KEY in der .env prüfen.")
    except anthropic.PermissionDeniedError:
        raise JarvisError("Der API-Key hat keine Berechtigung – ist Guthaben in der Anthropic Console aufgeladen?")
    except anthropic.RateLimitError:
        raise JarvisError("Zu viele Anfragen auf einmal. Einen Moment, dann bitte nochmal.")
    except anthropic.BadRequestError as e:
        logger.error("Ungültige Anfrage an Claude: %s", e.message)
        if "credit" in e.message.lower():
            raise JarvisError("Das API-Guthaben ist aufgebraucht. Bitte in der Anthropic Console aufladen.")
        raise JarvisError("Die Anfrage wurde abgelehnt. Details stehen im Server-Log.")
    except anthropic.APIConnectionError:
        raise JarvisError("Keine Verbindung zu Claude. Ist das Internet da?")
    except anthropic.APIStatusError as e:
        logger.error("Claude-API-Fehler %s: %s", e.status_code, e.message)
        raise JarvisError("Claude ist gerade nicht erreichbar. Bitte gleich nochmal versuchen.")

    store.log_usage(settings.model, response.usage.input_tokens, response.usage.output_tokens)

    if response.stop_reason == "refusal":
        raise JarvisError("Dazu kann ich leider nichts sagen.")

    # Die Antwort kann aus mehreren Blöcken bestehen (z. B. Denk-Blöcke) – wir nehmen nur Text.
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if response.stop_reason == "max_tokens":
        text += "\n\n_(Antwort wurde wegen Längenlimit abgeschnitten.)_"
    if not text:
        text = "Verzeihung, mir fehlen gerade die Worte. Versuch es bitte noch einmal."

    # Erst nach erfolgreicher Antwort speichern – so bleibt der Verlauf sauber.
    store.add_message(conversation_id, "user", user_text, channel)
    store.add_message(conversation_id, "assistant", text, channel)
    return text
