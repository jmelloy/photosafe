"""Authentication utilities for JWT-based auth"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.orm import Session
from sqlmodel import select

from .database import get_db
from .models import PersonalAccessToken, User

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hash string (stored in database as string)

    Returns:
        True if password matches the hash, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt hash as a string (suitable for database storage)
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify a refresh token and return the username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        # Validate token has required claims and is of correct type
        if username is None or token_type != "refresh":
            return None

        return username
    except ExpiredSignatureError:
        # Token is expired - log for security monitoring if needed
        return None
    except JWTError:
        # Other JWT errors (invalid signature, malformed token, etc.)
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password"""
    user = db.exec(select(User).where(User.username == username)).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token or Personal Access Token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # First try JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is not None:
            user = db.exec(select(User).where(User.username == username)).first()
            if user is not None:
                return user
    except JWTError:
        # Not a valid JWT, try as Personal Access Token
        pass
    
    # Try Personal Access Token
    pat = verify_personal_access_token(db, token)
    if pat is not None:
        # Update last_used_at
        pat.last_used_at = datetime.now(timezone.utc)
        db.add(pat)
        db.commit()
        
        user = db.exec(select(User).where(User.id == pat.user_id)).first()
        if user is not None:
            return user
    
    raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ============= PERSONAL ACCESS TOKEN FUNCTIONS =============


def generate_personal_access_token() -> str:
    """Generate a secure random token for Personal Access Tokens
    
    Returns a URL-safe token string of 32 bytes (43 characters in base64)
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token using bcrypt for secure storage
    
    Args:
        token: The plain text token to hash
        
    Returns:
        The bcrypt hash as a string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(token.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_personal_access_token(
    db: Session, 
    user: User, 
    name: str, 
    expires_in_days: Optional[int] = None
) -> tuple[PersonalAccessToken, str]:
    """Create a new Personal Access Token for a user
    
    Args:
        db: Database session
        user: User to create token for
        name: User-friendly name for the token
        expires_in_days: Optional expiration in days from now
        
    Returns:
        Tuple of (PersonalAccessToken object, plain text token)
        The plain text token is only available at creation time!
    """
    # Generate token
    token = generate_personal_access_token()
    token_hash = hash_token(token)
    
    # Calculate expiration if specified
    expires_at = None
    if expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    
    # Create PAT record
    pat = PersonalAccessToken(
        user_id=user.id,
        name=name,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    
    db.add(pat)
    db.commit()
    db.refresh(pat)
    
    return pat, token


def verify_personal_access_token(db: Session, token: str) -> Optional[PersonalAccessToken]:
    """Verify a Personal Access Token and return the PAT record if valid
    
    Args:
        db: Database session
        token: Plain text token to verify
        
    Returns:
        PersonalAccessToken object if valid, None otherwise
    """
    # Get all PATs (we need to check each one since tokens are hashed with bcrypt)
    # 
    # Performance Note: This loads all PATs to check each hash. This is acceptable
    # because users typically have only a few PATs (5-20 max). Bcrypt verification
    # is fast enough for this scale (~10ms per token).
    #
    # For systems with hundreds of tokens per user, consider optimizations like:
    # - Store first 8 chars of token unhashed for quick lookup
    # - Use a faster hash like SHA256 with HMAC
    # - Implement token caching
    pats = db.exec(select(PersonalAccessToken)).all()
    
    for pat in pats:
        try:
            # Check if token matches this PAT's hash
            if bcrypt.checkpw(token.encode("utf-8"), pat.token_hash.encode("utf-8")):
                # Check if token is expired
                if pat.expires_at is not None and datetime.now(timezone.utc) > pat.expires_at:
                    return None
                return pat
        except (ValueError, UnicodeDecodeError):
            # Invalid hash format, malformed token, or encoding error - skip this token
            continue
    
    return None


def revoke_personal_access_token(db: Session, user: User, token_id: int) -> bool:
    """Revoke (delete) a Personal Access Token
    
    Args:
        db: Database session
        user: User who owns the token
        token_id: ID of the token to revoke
        
    Returns:
        True if token was revoked, False if not found or not owned by user
    """
    pat = db.exec(
        select(PersonalAccessToken)
        .where(PersonalAccessToken.id == token_id)
        .where(PersonalAccessToken.user_id == user.id)
    ).first()
    
    if pat is None:
        return False
    
    db.delete(pat)
    db.commit()
    return True
