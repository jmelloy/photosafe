# Personal Access Tokens

Long-lived tokens for API integrations, scripts, and CLI tools.

## Create Token

**API:** `POST /api/auth/tokens` (requires JWT auth)
```json
{"name": "My Token", "expires_in_days": 90}  // expires_in_days optional
```
Response includes `token` - **only shown once, store securely!**

**CLI:**
```bash
photosafe user create-token USERNAME --name "My Token" [--expires-in-days 90]
```

## Use Token

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/photos/
```

## List Tokens

**API:** `GET /api/auth/tokens`

**CLI:** `photosafe user list-tokens USERNAME`

## Revoke Token

**API:** `DELETE /api/auth/tokens/{token_id}`

**CLI:** `photosafe user revoke-token USERNAME TOKEN_ID`

## Security

- Tokens are bcrypt-hashed before storage
- Set expiration for temporary access
- One token per use case
- Revoke unused tokens regularly
- Lost tokens cannot be recovered - create new one and revoke old
