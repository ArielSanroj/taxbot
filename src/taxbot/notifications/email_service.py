"""Email notification service with multi-provider support and retry logic."""

from __future__ import annotations

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core.config import get_settings
from ..core.logging import get_scraper_logger
from ..models.concept import Concept


class EmailService:
    """Email service with multi-provider support and retry logic."""

    def __init__(self):
        """Initialize email service."""
        self.settings = get_settings()
        self.logger = get_scraper_logger()

    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(
            self.settings.email_sender and
            self.settings.email_password and
            self.settings.email_recipients
        )

    @retry(
        retry=retry_if_exception_type((smtplib.SMTPException, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def send_concept_notification(
        self,
        concepts: List[Concept],
        csv_path: Optional[Path] = None
    ) -> bool:
        """Send notification about new concepts."""
        if not concepts:
            self.logger.info("No concepts to notify about")
            return True

        if not self.is_configured():
            self.logger.warning("Email not configured, skipping notification")
            return False

        try:
            # Create message
            msg = self._create_message(concepts, csv_path)
            
            # Send email
            self._send_message(msg)
            
            self.logger.info(f"Sent notification for {len(concepts)} concepts")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            raise

    def _create_message(self, concepts: List[Concept], csv_path: Optional[Path] = None) -> MIMEMultipart:
        """Create email message."""
        msg = MIMEMultipart()
        msg["From"] = self.settings.email_sender
        msg["To"] = ", ".join(self.settings.email_recipients)
        msg["Subject"] = f"Conceptos DIAN actualizados - {len(concepts)} nuevos conceptos"

        # Create email body
        body_lines = [
            f"Se han encontrado {len(concepts)} nuevos conceptos DIAN:",
            "",
        ]

        # Add concept summaries
        for concept in concepts[:10]:  # Limit to first 10 for email
            body_lines.extend([
                f"• {concept.date.strftime('%Y-%m-%d')} | {concept.theme} | {concept.title}",
                f"  {concept.get_content_preview(100)}",
                "",
            ])

        if len(concepts) > 10:
            body_lines.append(f"... y {len(concepts) - 10} conceptos más")

        body_lines.extend([
            "",
            "Se adjunta archivo CSV con detalles completos, resúmenes y análisis.",
            "",
            "---",
            "TaxBot Enterprise - Sistema automatizado de monitoreo DIAN",
        ])

        # Attach text body
        msg.attach(MIMEText("\n".join(body_lines), "plain", "utf-8"))

        # Attach CSV file if provided
        if csv_path and csv_path.exists():
            self._attach_csv_file(msg, csv_path)

        return msg

    def _attach_csv_file(self, msg: MIMEMultipart, csv_path: Path) -> None:
        """Attach CSV file to message."""
        try:
            with open(csv_path, "rb") as file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={csv_path.name}"
                )
                msg.attach(part)
        except Exception as e:
            self.logger.warning(f"Failed to attach CSV file: {e}")

    def _send_message(self, msg: MIMEMultipart) -> None:
        """Send email message."""
        # Determine SMTP settings based on provider
        smtp_host, smtp_port, use_tls = self._get_smtp_settings()
        
        # Create SMTP connection
        if use_tls:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()

        try:
            # Login and send
            server.login(self.settings.email_sender, self.settings.email_password)
            server.sendmail(
                self.settings.email_sender,
                self.settings.email_recipients,
                msg.as_string()
            )
        finally:
            server.quit()

    def _get_smtp_settings(self) -> tuple[str, int, bool]:
        """Get SMTP settings based on email provider."""
        email_domain = self.settings.email_sender.split("@")[-1].lower()
        
        # Provider-specific settings
        provider_settings = {
            "gmail.com": ("smtp.gmail.com", 587, True),
            "outlook.com": ("smtp-mail.outlook.com", 587, True),
            "hotmail.com": ("smtp-mail.outlook.com", 587, True),
            "yahoo.com": ("smtp.mail.yahoo.com", 587, True),
            "live.com": ("smtp-mail.outlook.com", 587, True),
        }
        
        # Use custom settings if provided
        if (self.settings.email_smtp_host != "smtp.gmail.com" or 
            self.settings.email_smtp_port != 465):
            return (
                self.settings.email_smtp_host,
                self.settings.email_smtp_port,
                self.settings.email_smtp_use_tls
            )
        
        # Use provider-specific settings
        return provider_settings.get(email_domain, ("smtp.gmail.com", 587, True))

    def send_test_email(self) -> bool:
        """Send test email to verify configuration."""
        if not self.is_configured():
            self.logger.error("Email not configured")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.settings.email_sender
            msg["To"] = ", ".join(self.settings.email_recipients)
            msg["Subject"] = "TaxBot - Test Email"

            body = """
            This is a test email from TaxBot Enterprise.
            
            If you receive this email, your email configuration is working correctly.
            
            ---
            TaxBot Enterprise - Sistema automatizado de monitoreo DIAN
            """
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            self._send_message(msg)
            
            self.logger.info("Test email sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send test email: {e}")
            return False

    def send_error_notification(self, error_message: str) -> bool:
        """Send error notification."""
        if not self.is_configured():
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.settings.email_sender
            msg["To"] = ", ".join(self.settings.email_recipients)
            msg["Subject"] = "TaxBot - Error Notification"

            body = f"""
            TaxBot encountered an error:
            
            {error_message}
            
            Please check the logs for more details.
            
            ---
            TaxBot Enterprise - Sistema automatizado de monitoreo DIAN
            """
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            self._send_message(msg)
            
            self.logger.info("Error notification sent")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")
            return False
