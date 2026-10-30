"""
Web-Zugang: die API, mit der die Web-App (PWA) spricht.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from backend import auth
from backend.brain import agent
from backend.config import settings
from backend.memory import store

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    password: str = Field(max_length=200)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


# ---------- Login ----------

@router.post("/login")
def login(body: LoginRequest, request: Request):
    if auth.is_locked_out(request):
        store.log_action("web", "login_blocked", status="failed")
        raise HTTPException(429, "Zu viele Fehlversuche. Bitte 15 Minuten warten.")
    if not auth.check_password(request, body.password):
        store.log_action("web", "login_failed", status="failed")
        raise HTTPException(401, "Falsches Passwort.")
    request.session["user"] = "owner"
    store.log_action("web", "login")
    return {"ok": True}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", dependencies=[Depends(auth.require_login)])
def me():
    return {"name": settings.user_name, "model": settings.model}


# ---------- Chat ----------

@router.get("/conversation", dependencies=[Depends(auth.require_login)])
def get_conversation():
    conversation_id = store.get_current_conversation_id()
    messages = store.get_recent_messages(conversation_id, limit=200)
    return {
        "conversation_id": conversation_id,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ],
    }


@router.post("/conversation/new", dependencies=[Depends(auth.require_login)])
def new_conversation():
    return {"conversation_id": store.start_new_conversation()}


@router.post("/chat", dependencies=[Depends(auth.require_login)])
async def chat(body: ChatRequest):
    try:
        # Der Claude-Aufruf dauert ein paar Sekunden – im Hintergrund-Thread blockiert er den Server nicht.
        answer = await run_in_threadpool(agent.reply, body.message.strip(), "web")
    except agent.JarvisError as e:
        raise HTTPException(502, str(e))
    return {"reply": answer}


@router.get("/usage", dependencies=[Depends(auth.require_login)])
def usage():
    return {"month_cost_usd": round(store.get_month_cost_usd(), 4), "model": settings.model}
