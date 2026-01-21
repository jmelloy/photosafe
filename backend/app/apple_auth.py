"""Apple/iCloud authentication service with 2FA support"""

import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from pyicloud import PyiCloudService
from requests.utils import dict_from_cookiejar
from sqlmodel import Session, select

from app.models import AppleAuthSession, AppleCredential


class AppleAuthService:
    """Service for managing Apple/iCloud authentication"""

    def __init__(self):
        # Get encryption key from environment or generate one
        # In production, this should be stored securely in environment variables
        encryption_key = os.getenv("APPLE_CREDENTIALS_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a key if not set (for development)
            # WARNING: This should be set in production to persist across restarts
            encryption_key = Fernet.generate_key().decode()

        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def _encrypt_password(self, password: str) -> str:
        """Encrypt a password for storage"""
        return self.cipher.encrypt(password.encode()).decode()

    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a stored password"""
        return self.cipher.decrypt(encrypted_password.encode()).decode()

    def _encrypt_session_data(self, session_data: dict) -> dict:
        """Encrypt session data (cookies, etc.)"""
        return {
            "encrypted": self.cipher.encrypt(json.dumps(session_data).encode()).decode()
        }

    def _decrypt_session_data(self, encrypted_data: dict) -> dict:
        """Decrypt session data"""
        if "encrypted" in encrypted_data:
            return json.loads(self.cipher.decrypt(encrypted_data["encrypted"].encode()).decode())
        return encrypted_data

    def create_credential(
        self, db: Session, user_id: int, apple_id: str, password: str
    ) -> AppleCredential:
        """Create a new Apple credential for a user"""
        # Check if credential already exists for this user and apple_id
        existing = db.exec(
            select(AppleCredential).where(
                AppleCredential.user_id == user_id,
                AppleCredential.apple_id == apple_id
            )
        ).first()

        if existing:
            # Update existing credential
            existing.encrypted_password = self._encrypt_password(password)
            existing.updated_at = datetime.now(timezone.utc)
            existing.is_active = True
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        # Create new credential
        credential = AppleCredential(
            user_id=user_id,
            apple_id=apple_id,
            encrypted_password=self._encrypt_password(password),
        )
        db.add(credential)
        db.commit()
        db.refresh(credential)
        return credential

    def get_credential(self, db: Session, credential_id: int) -> Optional[AppleCredential]:
        """Get a credential by ID"""
        return db.exec(
            select(AppleCredential).where(AppleCredential.id == credential_id)
        ).first()

    def get_user_credentials(self, db: Session, user_id: int) -> list[AppleCredential]:
        """Get all credentials for a user"""
        return list(db.exec(
            select(AppleCredential).where(AppleCredential.user_id == user_id)
        ).all())

    def delete_credential(self, db: Session, credential_id: int) -> bool:
        """Delete a credential and all its sessions"""
        credential = self.get_credential(db, credential_id)
        if not credential:
            return False

        db.delete(credential)
        db.commit()
        return True

    def initiate_authentication(
        self, db: Session, credential_id: int
    ) -> Tuple[Optional[AppleAuthSession], Optional[PyiCloudService]]:
        """
        Initiate authentication with Apple/iCloud.
        Returns (session, api) tuple.
        If 2FA is required, session.awaiting_2fa_code will be True.
        """
        credential = self.get_credential(db, credential_id)
        if not credential:
            return None, None

        # Decrypt password
        password = self._decrypt_password(credential.encrypted_password)

        # Create PyiCloudService instance
        try:
            api = PyiCloudService(credential.apple_id, password)
        except Exception as e:
            # Authentication failed
            return None, None

        # Create auth session
        session_token = secrets.token_urlsafe(32)
        auth_session = AppleAuthSession(
            credential_id=credential_id,
            session_token=session_token,
            session_data={},
            is_authenticated=False,
            requires_2fa=False,
            awaiting_2fa_code=False,
        )

        # Check if 2FA is required
        if api.requires_2fa:
            auth_session.requires_2fa = True
            auth_session.awaiting_2fa_code = True

            # For 2SA (two-step auth), get trusted devices
            if hasattr(api, 'trusted_devices') and api.trusted_devices:
                auth_session.trusted_devices = api.trusted_devices
        else:
            # No 2FA required, authentication successful
            auth_session.is_authenticated = True
            auth_session.awaiting_2fa_code = False
            credential.last_authenticated_at = datetime.now(timezone.utc)

            # Store session data (cookies)
            if hasattr(api, 'session') and hasattr(api.session, 'cookies'):
                cookies_dict = dict_from_cookiejar(api.session.cookies)
                auth_session.session_data = self._encrypt_session_data(cookies_dict)

        # Set expiration (7 days from now)
        auth_session.expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        db.add(auth_session)
        db.add(credential)
        db.commit()
        db.refresh(auth_session)
        db.refresh(credential)

        return auth_session, api

    def submit_2fa_code(
        self, db: Session, session_token: str, code: str
    ) -> Tuple[bool, Optional[str], Optional[AppleAuthSession]]:
        """
        Submit 2FA code for an authentication session.
        Returns (success, error_message, session)
        """
        # Find the session
        auth_session = db.exec(
            select(AppleAuthSession).where(
                AppleAuthSession.session_token == session_token
            )
        ).first()

        if not auth_session:
            return False, "Invalid session token", None

        if not auth_session.awaiting_2fa_code:
            return False, "Session is not awaiting 2FA code", None

        # Get the credential
        credential = self.get_credential(db, auth_session.credential_id)
        if not credential:
            return False, "Credential not found", None

        # Decrypt password
        password = self._decrypt_password(credential.encrypted_password)

        # Recreate PyiCloudService instance
        try:
            api = PyiCloudService(credential.apple_id, password)
        except Exception as e:
            return False, f"Authentication failed: {str(e)}", None

        # Validate 2FA code
        try:
            if not api.validate_2fa_code(code):
                return False, "Invalid 2FA code", None
        except Exception as e:
            return False, f"Failed to validate 2FA code: {str(e)}", None

        # Trust the session
        try:
            api.trust_session()
        except Exception as e:
            # Non-fatal, continue
            pass

        # Update session
        auth_session.is_authenticated = True
        auth_session.awaiting_2fa_code = False
        auth_session.last_used_at = datetime.now(timezone.utc)
        credential.last_authenticated_at = datetime.now(timezone.utc)
        credential.requires_2fa = True

        # Store session data (cookies)
        if hasattr(api, 'session') and hasattr(api.session, 'cookies'):
            cookies_dict = dict_from_cookiejar(api.session.cookies)
            auth_session.session_data = self._encrypt_session_data(cookies_dict)

        db.add(auth_session)
        db.add(credential)
        db.commit()
        db.refresh(auth_session)

        return True, None, auth_session

    def get_authenticated_api(
        self, db: Session, credential_id: int
    ) -> Optional[PyiCloudService]:
        """
        Get an authenticated PyiCloudService instance for a credential.
        Uses stored session if available, otherwise returns None.
        """
        credential = self.get_credential(db, credential_id)
        if not credential:
            return None

        # Find the most recent authenticated session
        auth_session = db.exec(
            select(AppleAuthSession)
            .where(
                AppleAuthSession.credential_id == credential_id,
                AppleAuthSession.is_authenticated == True,
                AppleAuthSession.awaiting_2fa_code == False,
            )
            .order_by(AppleAuthSession.last_used_at.desc())
        ).first()

        if not auth_session:
            return None

        # Check if session is expired
        if auth_session.expires_at and auth_session.expires_at < datetime.now(timezone.utc):
            return None

        # Decrypt password
        password = self._decrypt_password(credential.encrypted_password)

        # Create PyiCloudService instance
        try:
            api = PyiCloudService(credential.apple_id, password)

            # Restore session cookies if available
            if auth_session.session_data:
                session_data = self._decrypt_session_data(auth_session.session_data)
                if hasattr(api, 'session') and session_data:
                    for key, value in session_data.items():
                        api.session.cookies.set(key, value)

            # Update last used time
            auth_session.last_used_at = datetime.now(timezone.utc)
            db.add(auth_session)
            db.commit()

            return api
        except Exception as e:
            return None

    def get_session_by_token(
        self, db: Session, session_token: str
    ) -> Optional[AppleAuthSession]:
        """Get an auth session by its token"""
        return db.exec(
            select(AppleAuthSession).where(
                AppleAuthSession.session_token == session_token
            )
        ).first()
