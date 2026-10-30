"""
Datenbank-Tabellen von JARVIS.

- Conversation: ein Gesprächsverlauf
- Message:      eine einzelne Nachricht (von dir oder von JARVIS)
- ActionLog:    Protokoll aller Aktionen (Logins, später Tool-Ausführungen)
- UsageLog:     Token-Verbrauch und Kosten jedes KI-Aufrufs
"""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel, create_engine

from backend.config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str  # "user" oder "assistant"
    content: str
    channel: str = "web"  # über welchen Zugang die Nachricht kam (web, telegram, ...)
    created_at: datetime = Field(default_factory=utcnow)


class ActionLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    channel: str
    action: str  # z. B. "login", "login_failed", später "send_email"
    details: str = ""  # JSON-Text mit Zusatzinfos
    status: str = "ok"  # ok | failed | cancelled | pending


class UsageLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


# Bei SQLite muss der Zugriff aus mehreren Threads erlaubt werden (FastAPI nutzt Threads).
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)


def init_db() -> None:
    """Legt alle Tabellen an, falls sie noch nicht existieren."""
    SQLModel.metadata.create_all(engine)
