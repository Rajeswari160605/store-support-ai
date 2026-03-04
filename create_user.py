from database import get_db
from models.user import User
from utils.security import get_password_hash

db = next(get_db())

# Clean existing users
db.query(User).delete()
db.commit()

# ADMIN (matches your ENUM)
admin = User(
    email="admin@store.com",
    password=get_password_hash("password123"),
    role="admin",        # ✅ Matches your ENUM
    name="Admin User",
    store_id=1
)
db.add(admin)

# STORE MANAGER (matches your ENUM)  
manager = User(
    email="store1@healthglow.com",
    password=get_password_hash("store123"),
    role="manager",      # ✅ Matches your ENUM ('manager')
    name="Store Manager",
    store_id=1
)

db.add(manager)

db.commit()
print("✅ USERS CREATED WITH CORRECT ENUM VALUES!")
print("👑 ADMIN: admin@store.com / password123")
print("🏪 STORE MANAGER: store1@healthglow.com / store123")
