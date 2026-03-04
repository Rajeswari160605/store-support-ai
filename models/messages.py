# models/messages.py - NO IMPORT ISSUES
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()  # Local Base - works everywhere

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    store_id = Column(String(50), nullable=False)
    role = Column(Enum("user", "assistant"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
