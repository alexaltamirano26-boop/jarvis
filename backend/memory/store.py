"""
Lesen und Schreiben in die Datenbank.

Alle anderen Teile von JARVIS greifen nur über diese Funktionen auf die Datenbank zu.
So bleibt der restliche Code unabhängig davon, ob SQLite oder später Postgres läuft.
"""
import json
from datetime import datetime, timezone

from sqlmodel import Session, func, select

from backend.config import MODEL_PRICES
from backend.memory.models import ActionLog, Conversation, Message, UsageLog, engine


# ---------- Gespräche ----------

def get_current_conversation_id() -> int:
    """Gibt das neueste Gespräch zurück und legt eins an, falls es noch keins gibt."""
    with Session(engine) as session:
        conv = session.exec(select(Conversation).order_by(Conversation.id.desc())).first()
        if conv is None:
            conv = Conversation()
            session.add(conv)
            session.commit()
            session.refresh(conv)
        return conv.id


def start_new_conversation() -> int:
    with Session(engine) as session:
        conv = Conversation()
        session.add(conv)
        session.commit()
        session.refresh(conv)
        return conv.id


# ---------- Nachrichten ----------

def add_message(conversation_id: int, role: str, content: str, channel: str = "web") -> Message:
    with Session(engine) as session:
        msg = Message(conversation_id=conversation_id, role=role, content=content, channel=channel)
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg


def get_recent_messages(conversation_id: int, limit: int) -> list[Message]:
    """Die letzten `limit` Nachrichten eines Gesprächs, älteste zuerst."""
    with Session(engine) as session:
        rows = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
        ).all()
        return list(reversed(rows))


# ---------- Protokolle ----------

def log_action(channel: str, action: str, details: dict | None = None, status: str = "ok") -> None:
    with Session(engine) as session:
        session.add(
            ActionLog(
                channel=channel,
                action=action,
                details=json.dumps(details or {}, ensure_ascii=False),
                status=status,
            )
        )
        session.commit()


def log_usage(model: str, input_tokens: int, output_tokens: int) -> float:
    """Speichert den Verbrauch eines KI-Aufrufs und gibt die Kosten in USD zurück."""
    price_in, price_out = MODEL_PRICES.get(model, (0.0, 0.0))
    cost = input_tokens / 1_000_000 * price_in + output_tokens / 1_000_000 * price_out
    with Session(engine) as session:
        session.add(
            UsageLog(model=model, input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost)
        )
        session.commit()
    return cost


def get_month_cost_usd() -> float:
    """Summe der KI-Kosten im laufenden Kalendermonat."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    with Session(engine) as session:
        total = session.exec(
            select(func.sum(UsageLog.cost_usd)).where(UsageLog.created_at >= month_start)
        ).one()
        return float(total or 0.0)
