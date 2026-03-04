from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Depends
from sqlalchemy.orm import Session

if os.getenv("VERCEL") or os.getenv("VERCEL_URL"):
    DATABASE_URL = "sqlite:///store_support_ai.db"  # Vercel
else:
    DATABASE_URL = "mysql+pymysql://root:@localhost/store_support_ai"  # Local

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
