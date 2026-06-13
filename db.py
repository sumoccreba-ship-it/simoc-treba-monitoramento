from __future__ import annotations

import os
from contextlib import contextmanager
from urllib.parse import urlparse, urlunparse

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool


def _secret(name: str, default: str | None = None) -> str | None:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


def normalize_database_url(url: str) -> str:
    if not url:
        raise RuntimeError("DATABASE_URL nao configurada nos Secrets do Streamlit ou no ambiente.")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    database_url = normalize_database_url(_secret("DATABASE_URL", ""))
    return create_engine(
        database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
        future=True,
    )


@contextmanager
def db_session():
    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def run_schema() -> None:
    schema_path = os.path.join(os.path.dirname(__file__), "sql", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with db_session() as conn:
        for statement in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(text(statement))


def q(sql: str, **params):
    with db_session() as conn:
        return conn.execute(text(sql), params)
