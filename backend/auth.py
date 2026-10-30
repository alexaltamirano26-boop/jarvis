"""
Login-Schutz: Nur du (mit deinem Passwort) kannst JARVIS benutzen.

- Das Passwort selbst wird nirgends gespeichert, nur ein Argon2-Hash in der .env.
- Nach dem Login merkt sich der Browser ein signiertes Session-Cookie (30 Tage).
- Zu viele Fehlversuche von derselben Adresse werden für 15 Minuten gesperrt.
"""
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException, Request, status

from backend.config import settings

_hasher = PasswordHasher()

MAX_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60
_failed_attempts: dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def is_locked_out(request: Request) -> bool:
    attempts = _failed_attempts[_client_ip(request)]
    now = time.time()
    while attempts and now - attempts[0] > LOCK_SECONDS:
        attempts.popleft()
    return len(attempts) >= MAX_ATTEMPTS


def check_password(request: Request, password: str) -> bool:
    try:
        _hasher.verify(settings.password_hash, password)
        _failed_attempts.pop(_client_ip(request), None)
        return True
    except (VerificationError, InvalidHashError):
        _failed_attempts[_client_ip(request)].append(time.time())
        return False


def require_login(request: Request) -> None:
    """FastAPI-Abhängigkeit: blockt jede Anfrage ohne gültigen Login."""
    if request.session.get("user") != "owner":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht eingeloggt")
