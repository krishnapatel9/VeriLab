import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from api.dependencies import get_db
from db.models.core_models import User
from core.security import verify_password, create_access_token

router = APIRouter()

# ponytail: in-process throttle (per email+IP); use Redis/gateway limits once there is more than one worker.
_MAX_FAILS, _WINDOW_S = 5, 15 * 60
_fails: dict[str, list[float]] = {}

@router.post("/login")
def login_for_access_token(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    key = f"{form_data.username.lower()}|{request.client.host if request.client else '-'}"
    now = time.monotonic()
    recent = [t for t in _fails.get(key, []) if now - t < _WINDOW_S]
    if len(recent) >= _MAX_FAILS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")
    user = db.query(User).filter(User.email == form_data.username).first()
    if (
        not user
        or user.status != "active"
        or not verify_password(form_data.password, user.hashed_password)
    ):
        _fails[key] = recent + [now]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    _fails.pop(key, None)
    access_token = create_access_token(
        subject=user.id, role=user.role, tenant_id=user.tenant_id
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}
