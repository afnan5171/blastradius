import os, secrets, hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_db
from .models import User

router = APIRouter(prefix="/auth")


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("br_session", "")
    user = (
        db.scalar(select(User).where(User.token_hash == digest(token)))
        if token
        else None
    )
    if not user or user.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise HTTPException(401, "Start a demo session to continue.")
    return user


@router.post("/demo")
def demo_login(request: Request, response: Response, db: Session = Depends(get_db)):
    if os.getenv("DEMO_LOGIN_ENABLED", "true").lower() != "true":
        raise HTTPException(403, "Demo login is disabled.")
    try:
        user = current_user(request, db)
        return {"id": user.id}
    except HTTPException:
        pass
    token = secrets.token_urlsafe(32)
    user = User(
        token_hash=digest(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(user)
    db.commit()
    response.set_cookie(
        "br_session",
        token,
        httponly=True,
        samesite="strict",
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        max_age=30 * 86400,
        path="/",
    )
    return {"id": user.id}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id}
