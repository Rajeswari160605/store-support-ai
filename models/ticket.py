from sqlalchemy import Column, Integer, String, Text
from . import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(500))
    department = Column(String(100))   
    priority = Column(String(50))      
    description = Column(Text)
    store_id = Column(String(100))
    created_by = Column(String(100))
    status = Column(String(50))
    image = Column(String(500))
    ticket_number = Column(String(50))