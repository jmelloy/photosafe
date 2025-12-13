# Refresh Token Implementation

This document describes the refresh token implementation in PhotoSafe.

## Overview

The application now uses a dual-token authentication system:
- **Access Token**: Short-lived token (default: 30 minutes) used for API requests
- **Refresh Token**: Long-lived token (default: 7 days) used to obtain new access tokens

## Backend Implementation

### Configuration

Refresh token expiration can be configured via environment variables:

```bash
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Default: 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS=7     # Default: 7 days
```

### API Endpoints

#### Login - `/api/auth/login`

Returns both access and refresh tokens:

**Request:**
```bash
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user&password=pass
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### Refresh Token - `/api/auth/refresh`

Exchanges a valid refresh token for new access and refresh tokens:

**Request:**
```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Error Response (401):**
```json
{
  "detail": "Invalid refresh token"
}
```

### Token Structure

Both tokens are JWT tokens with the following claims:
- `sub`: Username of the authenticated user
- `exp`: Expiration timestamp
- `type`: Token type ("access" or "refresh")

The `type` claim ensures that refresh tokens cannot be used as access tokens and vice versa.

## Frontend Implementation

### Token Storage

Tokens are stored in localStorage:
- Access token: `photosafe_auth_token`
- Refresh token: `photosafe_refresh_token`

### Automatic Token Refresh

The frontend automatically handles token refresh when receiving a 401 error:

1. When an API request returns 401 (Unauthorized)
2. The response interceptor checks if a refresh token exists
3. If yes, it calls `/api/auth/refresh` to get new tokens
4. The new tokens are stored and the original request is retried
5. Multiple concurrent requests during refresh are queued and replayed

### Usage in Components

The automatic refresh is transparent to components. Just use the API normally:

```typescript
import { getCurrentUser } from '../api/auth';

// This will automatically refresh if the access token expired
const user = await getCurrentUser();
```

### Manual Token Refresh

You can also manually refresh tokens:

```typescript
import { refreshAccessToken } from '../api/auth';

try {
  await refreshAccessToken();
  console.log('Token refreshed successfully');
} catch (error) {
  console.error('Failed to refresh token', error);
  // Handle logout
}
```

## Security Considerations

1. **Token Expiration**: Access tokens expire after 30 minutes (configurable), limiting the window of vulnerability if a token is compromised.

2. **Refresh Token Rotation**: Each refresh operation returns a new refresh token, implementing refresh token rotation to enhance security.

3. **Token Type Validation**: The backend validates that refresh tokens have `type: "refresh"` to prevent access tokens from being used as refresh tokens.

4. **HTTPS**: In production, always use HTTPS to prevent token interception.

5. **Storage**: Tokens are stored in localStorage. For enhanced security in high-risk environments, consider:
   - Using httpOnly cookies for token storage
   - Implementing token revocation
   - Storing refresh tokens in a more secure location

## Testing

### Automated Tests

Run the backend tests:

```bash
cd backend
pytest test_auth_photos.py::test_login
pytest test_auth_photos.py::test_refresh_token
pytest test_auth_photos.py::test_refresh_token_invalid
```

### Manual Testing

A manual test script is provided for testing with a running server:

```bash
cd backend
# Start the server first
uvicorn app.main:app --reload

# In another terminal
python test_refresh_manual.py
```

### Testing Token Expiration

To test the automatic refresh functionality:

1. Set a very short access token expiration (e.g., 1 minute):
   ```bash
   export ACCESS_TOKEN_EXPIRE_MINUTES=1
   ```

2. Start the backend server

3. Login through the frontend

4. Wait for the access token to expire

5. Make an API request (e.g., navigate to photos)

6. The frontend should automatically refresh the token and retry the request

## Migration Notes

### For Existing Users

- Existing users will receive both tokens on their next login
- Old sessions with only access tokens will continue to work until the access token expires
- After expiration, users will need to log in again

### Backward Compatibility

- The `/api/auth/login` endpoint now returns an additional `refresh_token` field
- Clients that ignore the `refresh_token` field will continue to work with the access token
- However, they will need to re-authenticate when the access token expires

## Future Enhancements

Potential improvements for future versions:

1. **Token Revocation**: Maintain a blacklist of revoked tokens
2. **Device Tracking**: Associate refresh tokens with devices
3. **Session Management**: Allow users to view and revoke active sessions
4. **Sliding Sessions**: Extend refresh token expiration on use
5. **httpOnly Cookies**: Move tokens to httpOnly cookies for enhanced security
