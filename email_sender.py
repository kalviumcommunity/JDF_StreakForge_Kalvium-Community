"""Email delivery for StreakForge reports using SMTP."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # If python-dotenv not installed, use environment variables directly
    pass


def send_report(report_text, recipients, subject="StreakForge Retention Report", report_format="text"):
    """Send report via email using SMTP with credentials from environment variables.
    
    Args:
        report_text (str): Report content (text or HTML)
        recipients (list or str): Email address or list of addresses to send to
        subject (str): Email subject line
        report_format (str): "text" or "html" to set MIME type
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Read credentials from environment variables
    sender = os.environ.get("SENDER_EMAIL", "").strip()
    password = os.environ.get("SENDER_PASSWORD", "").strip()
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
    smtp_port_str = os.environ.get("SMTP_PORT", "587").strip()
    
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        error_msg = f"Invalid SMTP_PORT: {smtp_port_str} (must be a number)"
        log_error(error_msg)
        return False
    
    # Validate credentials exist
    if not sender or not password:
        error_msg = "Email credentials not configured. Set SENDER_EMAIL and SENDER_PASSWORD environment variables."
        log_error(error_msg)
        return False
    
    # Normalize recipients to list
    if isinstance(recipients, str):
        recipients = [recipients]
    
    if not recipients:
        error_msg = "No recipients provided for email delivery."
        log_error(error_msg)
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        # Attach report with appropriate MIME type
        if report_format == "html":
            mime_type = "html"
        else:
            mime_type = "plain"
        
        msg.attach(MIMEText(report_text, mime_type, "utf-8"))
        
        # Connect to SMTP server and send
        log_error(f"DEBUG: Connecting to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()  # Secure connection
        
        log_error(f"DEBUG: Logging in with {sender}")
        server.login(sender, password)
        
        log_error(f"DEBUG: Sending message to {recipients}")
        server.send_message(msg)
        server.quit()
        
        log_success(f"Email sent successfully to {', '.join(recipients)}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed. Check email credentials. Error: {str(e)}"
        log_error(error_msg)
        return False
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error during send: {str(e)}"
        log_error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error sending email: {type(e).__name__}: {str(e)}"
        log_error(error_msg)
        return False


def send_report_with_attachments(report_text, recipients, attachments=None, 
                                 subject="StreakForge Retention Report", report_format="text"):
    """Send report via email with optional file attachments.
    
    Args:
        report_text (str): Report content
        recipients (list or str): Email recipient(s)
        attachments (list): List of file paths to attach
        subject (str): Email subject
        report_format (str): "text" or "html"
    
    Returns:
        bool: True if successful, False otherwise
    """
    sender = os.environ.get("SENDER_EMAIL", "").strip()
    password = os.environ.get("SENDER_PASSWORD", "").strip()
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
    smtp_port_str = os.environ.get("SMTP_PORT", "587").strip()
    
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        log_error(f"Invalid SMTP_PORT: {smtp_port_str}")
        return False
    
    if not sender or not password:
        error_msg = "Email credentials not configured."
        log_error(error_msg)
        return False
    
    if isinstance(recipients, str):
        recipients = [recipients]
    
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        # Attach report
        if report_format == "html":
            msg.attach(MIMEText(report_text, "html", "utf-8"))
        else:
            msg.attach(MIMEText(report_text, "plain", "utf-8"))
        
        # Attach files if provided
        if attachments:
            from email.mime.base import MIMEBase
            from email import encoders
            
            for filepath in attachments:
                if os.path.exists(filepath):
                    with open(filepath, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {os.path.basename(filepath)}"
                        )
                        msg.attach(part)
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        
        log_success(f"Email with attachments sent to {', '.join(recipients)}")
        return True
        
    except Exception as e:
        error_msg = f"Error sending email with attachments: {str(e)}"
        log_error(error_msg)
        return False


def verify_email_config():
    """Check if email configuration is complete.
    
    Returns:
        tuple: (is_configured: bool, message: str)
    """
    sender = os.environ.get("SENDER_EMAIL", "").strip()
    password = os.environ.get("SENDER_PASSWORD", "").strip()
    smtp_server = os.environ.get("SMTP_SERVER", "").strip()
    smtp_port = os.environ.get("SMTP_PORT", "").strip()
    
    missing = []
    if not sender:
        missing.append("SENDER_EMAIL")
    if not password:
        missing.append("SENDER_PASSWORD")
    if not smtp_server:
        missing.append("SMTP_SERVER")
    if not smtp_port:
        missing.append("SMTP_PORT")
    
    if missing:
        message = f"Email not configured. Missing: {', '.join(missing)}. Set these in .env file."
        return False, message
    
    return True, "Email configuration complete and ready to send."


def test_email_connection():
    """Test SMTP connection without sending an email.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    sender = os.environ.get("SENDER_EMAIL", "").strip()
    password = os.environ.get("SENDER_PASSWORD", "").strip()
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip()
    smtp_port_str = os.environ.get("SMTP_PORT", "587").strip()
    
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        return False, f"Invalid SMTP_PORT: {smtp_port_str}"
    
    if not sender or not password:
        return False, "Credentials not configured"
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender, password)
        server.quit()
        return True, f"✓ SMTP connection successful! Credentials are valid."
    except smtplib.SMTPAuthenticationError:
        return False, "❌ SMTP Authentication failed. Check email and password."
    except smtplib.SMTPException as e:
        return False, f"❌ SMTP error: {str(e)}"
    except Exception as e:
        return False, f"❌ Connection error: {str(e)}"


def log_error(message):
    """Log error message with timestamp.
    
    Args:
        message (str): Error message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {message}")


def log_success(message):
    """Log success message with timestamp.
    
    Args:
        message (str): Success message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] SUCCESS: {message}")
