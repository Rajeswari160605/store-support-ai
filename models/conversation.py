from sqlalchemy import Column, Integer, String, Text
from database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    message = Column(Text)
    role = Column(String(20))  # user / assistant
