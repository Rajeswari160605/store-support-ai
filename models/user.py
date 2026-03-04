from sqlalchemy import Column, Integer, String, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    password = Column(String(255))
    
    role = Column(Enum('manager','support','admin'))
    store_id = Column(Integer)
