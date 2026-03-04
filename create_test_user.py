# save as create_admin.py
from database import get_db
from models.user import User
from utils.security import get_password_hash

db = next(get_db())
admin = User(
    email="admin@store.com",
    password=get_password_hash("password123"),
    role="admin", 
    name="Admin User",
    store_id=1
)
db.add(admin)
db.commit()
print("✅ Real login ready!")
