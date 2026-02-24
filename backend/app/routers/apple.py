"""Apple/iCloud credentials and authentication API endpoints"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.apple_auth import AppleAuthService
from app.auth import get_current_user
from app.database import get_db
from app.models import (
    AppleAuth2FARequest,
    AppleAuth2FAResponse,
    AppleAuthInitiateRequest,
    AppleAuthSessionRead,
    AppleCredential,
    AppleCredentialCreate,
    AppleCredentialRead,
    AppleCredentialUpdate,
    User,
)

router = APIRouter(prefix="/api/apple", tags=["apple"])
apple_auth_service = AppleAuthService()


@router.post("/credentials", response_model=AppleCredentialRead)
async def create_apple_credential(
    credential_data: AppleCredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update Apple/iCloud credentials for the current user"""
    credential = apple_auth_service.create_credential(
        db=db,
        user_id=current_user.id,
        apple_id=credential_data.apple_id,
        password=credential_data.password,
    )
    return credential


@router.get("/credentials", response_model=List[AppleCredentialRead])
async def list_apple_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all Apple/iCloud credentials for the current user"""
    credentials = apple_auth_service.get_user_credentials(
        db=db, user_id=current_user.id
    )
    return credentials


@router.get("/credentials/{credential_id}", response_model=AppleCredentialRead)
async def get_apple_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific Apple/iCloud credential"""
    credential = apple_auth_service.get_credential(db=db, credential_id=credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Verify ownership
    if credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return credential


@router.patch("/credentials/{credential_id}", response_model=AppleCredentialRead)
async def update_apple_credential(
    credential_id: int,
    credential_data: AppleCredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an Apple/iCloud credential"""
    credential = apple_auth_service.get_credential(db=db, credential_id=credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Verify ownership
    if credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update fields
    if credential_data.password is not None:
        from app.apple_auth import AppleAuthService

        service = AppleAuthService()
        credential.encrypted_password = service._encrypt_password(
            credential_data.password
        )

    if credential_data.is_active is not None:
        credential.is_active = credential_data.is_active

    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


@router.delete("/credentials/{credential_id}")
async def delete_apple_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an Apple/iCloud credential"""
    credential = apple_auth_service.get_credential(db=db, credential_id=credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Verify ownership
    if credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    apple_auth_service.delete_credential(db=db, credential_id=credential_id)
    return {"message": "Credential deleted successfully"}


@router.post("/auth/initiate", response_model=AppleAuthSessionRead)
async def initiate_apple_auth(
    request: AppleAuthInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate Apple/iCloud authentication.
    Returns a session with awaiting_2fa_code=True if 2FA is required.
    """
    # Verify credential ownership
    credential = apple_auth_service.get_credential(
        db=db, credential_id=request.credential_id
    )
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    if credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Initiate authentication
    auth_session, api = apple_auth_service.initiate_authentication(
        db=db, credential_id=request.credential_id
    )

    if not auth_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please check your credentials.",
        )

    return auth_session


@router.post("/auth/2fa", response_model=AppleAuth2FAResponse)
async def submit_2fa_code(
    request: AppleAuth2FARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a 2FA code for an authentication session.
    """
    # Get the session to verify ownership
    auth_session = apple_auth_service.get_session_by_token(
        db=db, session_token=request.session_token
    )
    if not auth_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership via credential
    credential = apple_auth_service.get_credential(
        db=db, credential_id=auth_session.credential_id
    )
    if not credential or credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Submit the code
    success, error_message, updated_session = apple_auth_service.submit_2fa_code(
        db=db, session_token=request.session_token, code=request.code
    )

    if not success:
        return AppleAuth2FAResponse(
            success=False,
            message=error_message or "2FA validation failed",
            session=None,
        )

    return AppleAuth2FAResponse(
        success=True,
        message="Authentication successful",
        session=updated_session,
    )


@router.get("/auth/session/{session_token}", response_model=AppleAuthSessionRead)
async def get_auth_session(
    session_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the status of an authentication session"""
    auth_session = apple_auth_service.get_session_by_token(
        db=db, session_token=session_token
    )
    if not auth_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership via credential
    credential = apple_auth_service.get_credential(
        db=db, credential_id=auth_session.credential_id
    )
    if not credential or credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return auth_session
