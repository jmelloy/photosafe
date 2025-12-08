# JWT Authentication and User Photo Management

This document describes the JWT-based authentication system and user photo management features added to the PhotoSafe FastAPI backend.

## Overview

The FastAPI backend now includes:
- JWT-based authentication system
- User registration and login
- User-specific photo management
- Photo ownership verification
- Integration with Django User and Photo models

## Features

### Authentication

1. **User Registration** (`POST /api/auth/register`)
   - Create new user accounts
   - Validates unique username and email
   - Hashes passwords using bcrypt

2. **User Login** (`POST /api/auth/login`)
   - Authenticate with username and password
   - Returns JWT access token
   - Token expires after 30 minutes (configurable)

3. **Current User** (`GET /api/auth/me`)
   - Get information about the authenticated user
   - Requires valid JWT token

### Photo Management

All photo endpoints now require authentication:

1. **Create Photo** (`POST /api/photos/`)
   - Photos are automatically assigned to the authenticated user
   - Supports full photo metadata from Django model

2. **List Photos** (`GET /api/photos/`)
   - Users only see their own photos
   - Superusers can see all photos

3. **Get Photo** (`GET /api/photos/{uuid}/`)
   - Users can only view their own photos
   - Returns 403 Forbidden for unauthorized access

4. **Update Photo** (`PATCH /api/photos/{uuid}/`)
   - Users can only update their own photos
   - Superusers can update any photo

5. **Delete Photo** (`DELETE /api/photos/{uuid}/`)
   - Users can only delete their own photos
   - Superusers can delete any photo

## Configuration

### Environment Variables

Create a `.env` file in the backend directory (see `.env.example`):

```bash
# JWT Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://photosafe:photosafe@localhost:5432/photosafe
```

**Important**: Generate a secure SECRET_KEY:
```bash
openssl rand -hex 32
```

## Database Models

### User Model

Matches Django's User model:
```python
- id: Integer (Primary Key)
- username: String (Unique)
- email: String (Unique)
- hashed_password: String
- name: String (Optional)
- is_active: Boolean
- is_superuser: Boolean
- date_joined: DateTime
- last_login: DateTime
```

### Photo Model Updates

Added owner field:
```python
- owner_id: Integer (Foreign Key to User)
```

## API Usage Examples

### Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "name": "John Doe"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=johndoe&password=securepassword123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Access Protected Endpoint

```bash
curl -X GET http://localhost:8000/api/photos/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create a Photo

```bash
curl -X POST http://localhost:8000/api/photos/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "photo-uuid-123",
    "original_filename": "photo.jpg",
    "date": "2024-01-01T00:00:00",
    "title": "My Photo"
  }'
```

## Testing

Run the test suite:
```bash
cd backend
python -m pytest test_auth_photos.py -v
```

Run the demo script:
```bash
cd backend
python demo_auth.py
```

## Security Considerations

1. **Secret Key**: Always use a strong, randomly generated SECRET_KEY in production
2. **HTTPS**: Use HTTPS in production to protect JWT tokens in transit
3. **Token Expiration**: Configure appropriate token expiration times
4. **Password Hashing**: Passwords are hashed using bcrypt (via passlib)
5. **Input Validation**: All inputs are validated using Pydantic schemas

## Django Integration

The FastAPI models are designed to work with Django's database schema:

- User model mirrors Django's AbstractUser
- Photo model includes owner field as foreign key to User
- Compatible with Django's authentication system
- Can share the same PostgreSQL database

## Future Enhancements

Potential improvements:
- Refresh token support
- Password reset functionality
- Email verification
- Social authentication (OAuth2)
- Rate limiting
- Audit logging
