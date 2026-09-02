"""Email delivery for StreakForge reports using SMTP."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


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
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    
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
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure connection
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        
        log_success(f"Email sent successfully to {', '.join(recipients)}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed. Check email credentials: {str(e)}"
        log_error(error_msg)
        return False
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error during send: {str(e)}"
        log_error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error sending email: {str(e)}"
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
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    
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
        
        server = smtplib.SMTP(smtp_server, smtp_port)
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
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    
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
