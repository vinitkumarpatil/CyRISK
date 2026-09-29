"""Database engine, session factory and declarative base."""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from . import config

_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    config.DATABASE_URL,
    connect_args=_connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Import models for side-effect registration."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_lightweight()


def _migrate_lightweight():
    """Additive, idempotent column back-fills for pre-existing SQLite databases.

    create_all() never ALTERs existing tables, so a database created before
    multi-tenancy lacks users.org_id. Add it in place (nullable) so existing
    demo rows and reports are preserved rather than dropped.
    """
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "org_id" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN org_id INTEGER"))
