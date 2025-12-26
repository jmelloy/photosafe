"""Tests for email notification functionality."""

import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from app.email import send_error_email


@pytest.mark.unit
def test_send_error_email_without_smtp_config():
    """Test that email sending is skipped when SMTP is not configured."""
    with patch.dict(os.environ, {}, clear=True):
        error = ValueError("Test error")
        result = send_error_email(error)
        assert result is False


@pytest.mark.unit
def test_send_error_email_with_smtp_config():
    """Test that email is sent when SMTP is properly configured."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            error = ValueError("Test error message")
            result = send_error_email(error)
            
            assert result is True
            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test@example.com", "testpassword")
            mock_server.send_message.assert_called_once()


@pytest.mark.unit
def test_send_error_email_with_context():
    """Test that email includes context information."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    context = {
        "method": "GET",
        "url": "http://example.com/api/test",
        "client": "127.0.0.1",
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            error = ValueError("Test error")
            result = send_error_email(error, context=context)
            
            assert result is True
            # Verify that send_message was called
            assert mock_server.send_message.called
            # Get the message that was sent
            sent_message = mock_server.send_message.call_args[0][0]
            body = sent_message.get_payload()[0].get_payload()
            
            # Verify context is in the body
            assert "method: GET" in body
            assert "url: http://example.com/api/test" in body
            assert "client: 127.0.0.1" in body


@pytest.mark.unit
def test_send_error_email_with_traceback():
    """Test that email includes traceback information."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    traceback_str = "Traceback (most recent call last):\n  File test.py, line 1"
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            error = ValueError("Test error")
            result = send_error_email(error, traceback_str=traceback_str)
            
            assert result is True
            # Get the message that was sent
            sent_message = mock_server.send_message.call_args[0][0]
            body = sent_message.get_payload()[0].get_payload()
            
            # Verify traceback is in the body
            assert "Traceback:" in body
            assert traceback_str in body


@pytest.mark.unit
def test_send_error_email_smtp_failure():
    """Test that function handles SMTP failures gracefully."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP connection failed")
            
            error = ValueError("Test error")
            result = send_error_email(error)
            
            # Should return False but not raise exception
            assert result is False


@pytest.mark.unit
def test_send_error_email_default_recipient():
    """Test that default error recipient is jmelloy@gmail.com."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        # ERROR_EMAIL_TO not set, should use default
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            error = ValueError("Test error")
            result = send_error_email(error)
            
            assert result is True
            # Get the message that was sent
            sent_message = mock_server.send_message.call_args[0][0]
            assert sent_message["To"] == "jmelloy@gmail.com"


@pytest.mark.unit
def test_send_error_email_subject_includes_error_type():
    """Test that email subject includes the error type."""
    env_vars = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "testpassword",
        "ERROR_EMAIL_TO": "jmelloy@gmail.com",
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            error = ValueError("Test error")
            result = send_error_email(error)
            
            assert result is True
            # Get the message that was sent
            sent_message = mock_server.send_message.call_args[0][0]
            assert "ValueError" in sent_message["Subject"]
            assert "PhotoSafe 500 Error" in sent_message["Subject"]
