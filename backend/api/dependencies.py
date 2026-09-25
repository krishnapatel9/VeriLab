from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from constants import settings
from db.models.core_models import User

# Database setup
SQLALCHEMY_DATABASE_URL = settings.database_url
_is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    **({"pool_pre_ping": True} if not _is_sqlite else {}),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Auth setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

import uuid

def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.status != "active":
        raise credentials_exception
    return user

def require_role(required_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != "admin" and current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker
