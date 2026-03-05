# DB Setup + Base (Vercel/Railway compatible)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymysql
pymysql.install_as_MySQLdb() 
import os

Base = declarative_base()

DATABASE_URL = os.getenv("MYSQL_URL", "mysql+pymysql://root:@localhost/store_support_ai")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Your models
from .user import User
from .ticket import Ticket
from .conversation import Conversation
from .SupportGroup import SupportGroup
from .messages import Message

__all__ = ['User', 'Ticket', 'Conversation', 'SupportGroup', 'Message', 'Base', 'get_db']
