# Personal Access Tokens (PATs)

Personal Access Tokens provide a way to authenticate with the PhotoSafe API without using your password. They are useful for:

- API integrations and automation
- Third-party applications
- Long-running scripts
- CLI tools that need persistent authentication

## Features

- **Long-lived authentication**: Create tokens that don't expire or set custom expiration periods
- **Named tokens**: Give each token a descriptive name to track its purpose
- **Revocable**: Delete tokens at any time to revoke access
- **Secure**: Tokens are hashed using bcrypt before storage (same as passwords)
- **Usage tracking**: See when each token was last used

## Creating a Token

### Via API

**POST** `/api/auth/tokens`

**Authentication Required**: Yes (JWT token)

**Request Body**:
```json
{
  "name": "My API Token",
  "expires_in_days": 90  // Optional, omit for no expiration
}
```

**Response**:
```json
{
  "id": 1,
  "user_id": 1,
  "name": "My API Token",
  "token": "abc123...",  // Only shown once!
  "created_at": "2024-01-15T10:00:00Z",
  "expires_at": "2024-04-15T10:00:00Z"
}
```

⚠️ **Important**: The token value is only shown once during creation. Store it securely!

### Via CLI

```bash
# Create a token that never expires
photosafe user create-token USERNAME --name "My Token"

# Create a token that expires in 90 days
photosafe user create-token USERNAME --name "Temporary Token" --expires-in-days 90
```

## Using a Token

Once you have a token, use it in the `Authorization` header just like a JWT token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8000/api/photos/
```

The token works with all API endpoints that require authentication.

## Listing Tokens

### Via API

**GET** `/api/auth/tokens`

**Authentication Required**: Yes

**Response**:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "My API Token",
    "created_at": "2024-01-15T10:00:00Z",
    "last_used_at": "2024-01-16T14:30:00Z",
    "expires_at": null
  }
]
```

Note: Token values are never returned in list responses.

### Via CLI

```bash
photosafe user list-tokens USERNAME
```

Example output:
```
Personal Access Tokens for 'john':

ID     Name                           Created              Last Used            Expires             
----------------------------------------------------------------------------------------------------
1      My API Token                   2024-01-15 10:00     2024-01-16 14:30     Never              
2      Temporary Token                2024-01-15 11:00     Never                2024-04-15 11:00    
```

## Revoking a Token

### Via API

**DELETE** `/api/auth/tokens/{token_id}`

**Authentication Required**: Yes

**Response**: 204 No Content

### Via CLI

```bash
photosafe user revoke-token USERNAME TOKEN_ID
```

You'll be prompted to confirm the revocation.

## Security Best Practices

1. **Treat tokens like passwords**: Never commit them to version control or share them publicly
2. **Use descriptive names**: This helps you identify and manage tokens later
3. **Set expiration dates**: For temporary access, use the `expires_in_days` parameter
4. **Revoke unused tokens**: Regularly audit and delete tokens you're no longer using
5. **One token per use case**: Create separate tokens for different integrations
6. **Monitor usage**: Check the `last_used_at` timestamp to identify inactive tokens

## Token Expiration

- Tokens without an expiration date remain valid indefinitely (until revoked)
- Expired tokens are automatically rejected by the API
- The CLI's `list-tokens` command shows "(EXPIRED)" next to expired tokens
- Consider setting expiration dates for tokens used by temporary integrations

## Troubleshooting

**Q: I get a 401 error when using my token**
- Verify the token wasn't expired or revoked
- Check that you're using the correct format: `Authorization: Bearer YOUR_TOKEN`
- Ensure your user account is still active

**Q: I lost my token value**
- Tokens cannot be recovered once lost
- Create a new token and revoke the old one

**Q: Can I rename a token?**
- Not currently. Delete the old token and create a new one with the desired name.
