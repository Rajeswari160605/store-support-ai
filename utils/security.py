from passlib.context import CryptContext
from passlib.hash import sha256_crypt
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# FIXED CryptContext - supports BCrypt + SHA256_Crypt
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt"], 
    default="bcrypt",
    deprecated="auto"
)

# 🔐 HASH NEW PASSWORDS (always BCrypt)
def get_password_hash(password: str):
    """Generate secure BCrypt hash for new users"""
    return pwd_context.hash(password)

# 🔍 VERIFY PASSWORD - BOTH FORMATS
def verify_password(plain_password: str, hashed_password: str):
    """
    Handles:
    - BCrypt ($2b$...) ✅ New users
    - SHA256_Crypt ($5$...) ✅ Store manager
    """
    if not plain_password or not hashed_password:
        return False
    
    # SHA256_Crypt first ($5$ hashes from your DB)
    if hashed_password.startswith('$5$'):
        return sha256_crypt.verify(plain_password, hashed_password)
    
    # BCrypt fallback ($2b$ hashes)
    return pwd_context.verify(plain_password, hashed_password)

# 🔑 CREATE ACCESS TOKEN
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=10)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
