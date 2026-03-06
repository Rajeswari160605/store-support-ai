from sqlalchemy import Column, Integer, String,Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))
    role = Column(String(50))
    store_id = Column(String(20), nullable=False, index=True)  # ✅ STRING!
