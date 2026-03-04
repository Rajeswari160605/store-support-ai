from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Depends
from sqlalchemy.orm import Session
import os
if os.getenv("VERCEL") or os.getenv("VERCEL_URL"):
    DATABASE_URL = "sqlite:///:memory:"  # In-memory, works everywhere
else:
    DATABASE_URL = "mysql+pymysql://root:@localhost/store_support_ai"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
