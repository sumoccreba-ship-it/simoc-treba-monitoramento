from __future__ import annotations

from datetime import datetime, timedelta
import os
import streamlit as st
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def secret_key() -> str:
    try:
        return st.secrets.get("SECRET_KEY") or os.getenv("SECRET_KEY", "dev-secret-change-me")
    except Exception:
        return os.getenv("SECRET_KEY", "dev-secret-change-me")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(subject: str, minutes: int = 480) -> str:
    payload = {"sub": subject, "exp": datetime.utcnow() + timedelta(minutes=minutes)}
    return jwt.encode(payload, secret_key(), algorithm=ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        return jwt.decode(token, secret_key(), algorithms=[ALGORITHM]).get("sub")
    except Exception:
        return None
