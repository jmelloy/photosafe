"""Authentication API endpoints"""

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlmodel import select

from ..auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    authenticate_user,
    create_access_token,
    create_personal_access_token,
    create_refresh_token,
    get_current_active_user,
    get_password_hash,
    revoke_personal_access_token,
    verify_refresh_token,
)
from ..database import get_db
from ..models import (
    PersonalAccessToken,
    PersonalAccessTokenCreate,
    PersonalAccessTokenRead,
    PersonalAccessTokenResponse,
    RefreshTokenRequest,
    Token,
    User,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    existing_user = db.exec(
        select(User).where(User.username == user_data.username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email already exists
    existing_email = db.exec(select(User).where(User.email == user_data.email)).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login and get access and refresh tokens"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    username = verify_refresh_token(request.refresh_token)
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Create new refresh token
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


# ============= PERSONAL ACCESS TOKEN ENDPOINTS =============


@router.post("/tokens", response_model=PersonalAccessTokenResponse, status_code=201)
async def create_token(
    token_data: PersonalAccessTokenCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new Personal Access Token

    The token value is only shown once in the response.
    Store it securely as it cannot be retrieved later.
    """
    pat, token = create_personal_access_token(
        db, current_user, token_data.name, token_data.expires_in_days
    )

    return PersonalAccessTokenResponse(
        id=pat.id,
        user_id=pat.user_id,
        name=pat.name,
        token=token,
        created_at=pat.created_at,
        expires_at=pat.expires_at,
    )


@router.get("/tokens", response_model=List[PersonalAccessTokenRead])
async def list_tokens(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all Personal Access Tokens for the current user"""
    tokens = db.exec(
        select(PersonalAccessToken).where(
            PersonalAccessToken.user_id == current_user.id
        )
    ).all()
    return tokens


@router.delete("/tokens/{token_id}", status_code=204)
async def delete_token(
    token_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke (delete) a Personal Access Token"""
    success = revoke_personal_access_token(db, current_user, token_id)
    if not success:
        raise HTTPException(status_code=404, detail="Token not found")
    return None
