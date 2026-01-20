import os
from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer, BadSignature

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
serializer = URLSafeSerializer(SECRET_KEY, salt="wms-session")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def sign_session(data: dict) -> str:
    return serializer.dumps(data)

def unsign_session(token: str) -> dict | None:
    try:
        return serializer.loads(token)
    except BadSignature:
        return None
