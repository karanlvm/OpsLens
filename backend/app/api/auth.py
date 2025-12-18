"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    get_api_key
)
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class APIKeyCreate(BaseModel):
    name: str
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only shown once
    created_at: str
    expires_at: Optional[str] = None


@router.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get access token (OAuth2 password flow)."""
    # In production, verify against database
    # For now, return a token (implement proper user auth)
    access_token_expires = timedelta(minutes=60 * 24)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    # Optional auth - in production, require authentication
    # current_api_key: str = Depends(get_api_key)
):
    """Create a new API key."""
    from app.auth.models import APIKey
    import secrets
    
    # Generate API key
    api_key = secrets.token_urlsafe(32)
    key_hash = get_password_hash(api_key)
    
    # Create API key record
    db_api_key = APIKey(
        key_hash=key_hash,
        name=api_key_data.name,
        is_active=True
    )
    
    if api_key_data.expires_days:
        from datetime import datetime, timedelta
        db_api_key.expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_days)
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return {
        "id": str(db_api_key.id),
        "name": db_api_key.name,
        "key": api_key,  # Only shown once
        "created_at": db_api_key.created_at.isoformat(),
        "expires_at": db_api_key.expires_at.isoformat() if db_api_key.expires_at else None
    }


@router.get("/auth/verify")
async def verify_auth(current_api_key: str = Depends(get_api_key)):
    """Verify API key is valid."""
    return {
        "status": "valid",
        "message": "API key is valid"
    }

