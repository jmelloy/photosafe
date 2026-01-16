# Email Notifications for 500 Errors

This document describes the email notification system for 500 Internal Server Errors in PhotoSafe.

## Overview

PhotoSafe now automatically sends email notifications when 500 errors occur in the backend API. This helps with monitoring and quick response to production issues.

## Features

- **Automatic Detection**: Catches both HTTPException with 500+ status codes and unhandled exceptions
- **Detailed Information**: Includes error type, message, request context (URL, method, client IP), and full traceback
- **Configurable**: SMTP settings and recipient email are configurable via environment variables
- **Safe**: If SMTP is not configured or email sending fails, the application continues to work normally
- **Default Recipient**: Emails are sent to jmelloy@gmail.com by default (configurable)

## Configuration

Add these environment variables to configure email notifications:

```bash
# SMTP Server Configuration
SMTP_HOST=smtp.gmail.com          # Your SMTP server hostname
SMTP_PORT=587                      # SMTP port (usually 587 for TLS)
SMTP_USER=your-email@gmail.com    # SMTP username (usually your email)
SMTP_PASSWORD=your-app-password   # SMTP password or app-specific password
SMTP_FROM=photosafe@example.com   # Optional: sender email (defaults to SMTP_USER)

# Error Notification Recipient
ERROR_EMAIL_TO=jmelloy@gmail.com  # Email address to receive error notifications (default: jmelloy@gmail.com)
```

### Gmail Configuration

If using Gmail:
1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password at https://myaccount.google.com/apppasswords
3. Use the app-specific password as `SMTP_PASSWORD`

Example:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcd-efgh-ijkl-mnop  # App-specific password from Google
ERROR_EMAIL_TO=jmelloy@gmail.com
```

## Email Content

When a 500 error occurs, the email includes:

**Subject**: `PhotoSafe 500 Error: <ErrorType>`

**Body**:
```
A 500 Internal Server Error occurred in PhotoSafe at <timestamp>

Error Type: <exception class name>
Error Message: <error message>

Request Context:
  method: <HTTP method>
  url: <full request URL>
  client: <client IP address>

Traceback:
<full Python traceback>
```

## Testing

The email notification system includes comprehensive tests:

### Unit Tests
Located in `tests/unit/test_email.py`:
- SMTP configuration handling
- Email content generation
- Context and traceback inclusion
- Default recipient verification
- Error handling

### Integration Tests
Located in `tests/integration/test_error_handling.py`:
- HTTPException 500 handling
- Non-500 HTTPException (no email)
- Unhandled exception handling
- Operation without SMTP configuration

Run tests:
```bash
# Unit tests
pytest tests/unit/test_email.py -v

# Integration tests
pytest tests/integration/test_error_handling.py -v

# All tests
pytest tests/unit/test_email.py tests/integration/test_error_handling.py -v
```

## Implementation Details

### Exception Handlers

Two exception handlers in `app/main.py`:

1. **HTTPException Handler**: Catches HTTPException and sends email only for 500+ status codes
2. **Global Exception Handler**: Catches all other unhandled exceptions and sends email

### Email Module

The `app/email.py` module provides the `send_error_email()` function:
- Checks for SMTP configuration
- Builds email with context and traceback
- Handles SMTP errors gracefully
- Returns boolean indicating success/failure

## Disabling Email Notifications

To disable email notifications, simply don't set the SMTP environment variables. The application will work normally without attempting to send emails.

## Troubleshooting

**Emails not being sent?**
- Verify SMTP environment variables are set correctly
- Check SMTP credentials are valid
- Ensure SMTP server allows connections from your host
- Check application logs for "Failed to send error email" messages

**Using Gmail and getting authentication errors?**
- Make sure 2-factor authentication is enabled
- Use an app-specific password, not your regular password
- Verify the SMTP settings: host=smtp.gmail.com, port=587

**Want to test email sending?**
- Trigger a test error endpoint (in development/staging only)
- Check that SMTP environment variables are configured
- Monitor application logs for email sending status
