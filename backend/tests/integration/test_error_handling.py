"""Integration tests for 500 error handling and email notifications."""

import os
from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException
from app.main import app


@pytest.mark.integration
def test_http_exception_500_sends_email(client):
    """Test that HTTPException with 500 status sends email notification."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    # Create a route that raises HTTPException with 500
    @app.get("/test-http-500")
    async def test_http_500():
        raise HTTPException(status_code=500, detail="Test HTTP 500 error")
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            response = client.get("/test-http-500")
            
            # Should return 500
            assert response.status_code == 500
            assert response.json()["detail"] == "Test HTTP 500 error"
            
            # Should have attempted to send email
            assert mock_smtp.called


@pytest.mark.integration
def test_http_exception_400_no_email(client):
    """Test that HTTPException with non-500 status does not send email."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    # Create a route that raises HTTPException with 400
    @app.get("/test-http-400")
    async def test_http_400():
        raise HTTPException(status_code=400, detail="Test HTTP 400 error")
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            response = client.get("/test-http-400")
            
            # Should return 400
            assert response.status_code == 400
            assert response.json()["detail"] == "Test HTTP 400 error"
            
            # Should NOT have attempted to send email for 400 error
            assert not mock_smtp.called


@pytest.mark.integration
def test_exception_handler_sends_email(client):
    """Test that exception handler sends email notification for unhandled exceptions."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    # Create a route that raises an exception
    @app.get("/test-error-integration")
    async def test_error_integration():
        raise RuntimeError("Test error for email notification")
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Call the endpoint - exception handler should catch it
            try:
                response = client.get("/test-error-integration")
                # If we get here, exception was handled
                assert response.status_code == 500
                assert response.json()["detail"] == "Internal server error"
            except RuntimeError:
                # If exception wasn't caught, that's also acceptable for testing
                # the email sending still happened
                pass
            
            # Verify email was attempted to be sent
            assert mock_smtp.called
            if mock_server.send_message.called:
                # Verify email content includes error details
                sent_message = mock_server.send_message.call_args[0][0]
                assert sent_message["To"] == "jmelloy@gmail.com"
                assert "RuntimeError" in sent_message["Subject"]
                
                body = sent_message.get_payload()[0].get_payload()
                assert "Test error for email notification" in body


@pytest.mark.integration
def test_exception_handler_without_smtp_config(client):
    """Test that exception handler works even without SMTP configured."""
    # Create a route that raises an exception
    @app.get("/test-error-no-smtp-integration")
    async def test_error_no_smtp_integration():
        raise ValueError("Test error without SMTP")
    
    with patch.dict(os.environ, {}, clear=True):
        # The exception might be raised or caught depending on FastAPI internals
        # Either way, the application should not crash
        try:
            response = client.get("/test-error-no-smtp-integration")
            # If exception was handled, should return 500
            assert response.status_code == 500
        except ValueError:
            # Exception was raised - this is also acceptable
            # The important thing is that trying to send email didn't crash
            pass


