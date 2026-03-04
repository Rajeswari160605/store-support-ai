import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from contextlib import contextmanager

# Vercel-safe SQLite (works everywhere)
DATABASE_URL = "sqlite:///./healthglow.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # ✅ FIXES THREAD ERROR
        "timeout": 30,
    },
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
