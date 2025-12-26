"""Email notification utilities for error reporting."""

import os
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional


def send_error_email(
    error: Exception,
    context: Optional[dict] = None,
    traceback_str: Optional[str] = None
) -> bool:
    """
    Send an email notification when a 500 error occurs.
    
    Args:
        error: The exception that was raised
        context: Optional dictionary with additional context (request info, etc.)
        traceback_str: Optional traceback string
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get SMTP configuration from environment
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)
    error_email_to = os.getenv("ERROR_EMAIL_TO", "jmelloy@gmail.com")
    
    # Skip if SMTP is not configured
    if not smtp_host or not smtp_user or not smtp_password:
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = error_email_to
        msg["Subject"] = f"PhotoSafe 500 Error: {type(error).__name__}"
        
        # Build email body
        body_parts = [
            f"A 500 Internal Server Error occurred in PhotoSafe at {datetime.now().isoformat()}",
            "",
            f"Error Type: {type(error).__name__}",
            f"Error Message: {str(error)}",
            "",
        ]
        
        # Add context information if provided
        if context:
            body_parts.append("Request Context:")
            for key, value in context.items():
                body_parts.append(f"  {key}: {value}")
            body_parts.append("")
        
        # Add traceback if provided
        if traceback_str:
            body_parts.append("Traceback:")
            body_parts.append(traceback_str)
        
        body = "\n".join(body_parts)
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        # Log the error but don't raise it to avoid interfering with error handling
        print(f"Failed to send error email: {str(e)}")
        return False
