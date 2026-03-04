

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class SupportGroup(Base):
    __tablename__ = 'support_groups'
    
    id = Column(Integer, primary_key=True)
    store_id = Column(String(20), nullable=False)
    group_name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    members = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
