from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    service_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(40))
    email_or_username: Mapped[str] = mapped_column(String(254), default="")
    importance: Mapped[str] = mapped_column(String(20))
    has_mfa: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_type: Mapped[str] = mapped_column(String(40), default="None")
    has_passkey: Mapped[bool] = mapped_column(Boolean, default=False)
    recovery_phone: Mapped[str] = mapped_column(String(40), default="")
    recovery_email: Mapped[str] = mapped_column(String(254), default="")
    notes: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (UniqueConstraint("source_account_id", "target_account_id", "relationship_type"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    target_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(50))
    risk_weight: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(String(2000), default="")
