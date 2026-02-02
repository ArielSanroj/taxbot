"""Email notification functions."""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List

from .config import EMAIL_PASSWORD, EMAIL_RECIPIENTS, EMAIL_SENDER
from .models import Concept


def send_email(csv_path: Path, new_concepts: List[Concept]) -> None:
    """Send email notification with new concepts."""
    if not new_concepts:
        logging.info("Sin conceptos nuevos, no se envia correo.")
        return

    if not _is_email_configured():
        logging.warning(
            "Configuracion de correo incompleta, se omite el envio."
        )
        return

    msg = _build_email_message(new_concepts)
    _attach_csv_file(msg, csv_path)
    _send_smtp_message(msg)


def _is_email_configured() -> bool:
    """Check if email is properly configured."""
    return bool(EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECIPIENTS)


def _build_email_message(concepts: List[Concept]) -> MIMEMultipart:
    """Build the email message."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECIPIENTS)
    msg["Subject"] = (
        f"Conceptos DIAN actualizados - "
        f"{datetime.utcnow().strftime('%Y-%m-%d')}"
    )

    body_lines = _build_email_body(concepts)
    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    return msg


def _build_email_body(concepts: List[Concept]) -> List[str]:
    """Build email body lines."""
    lines = ["Resumen de nuevos conceptos DIAN:"]
    for concept in concepts:
        date_str = concept.date.strftime("%Y-%m-%d")
        lines.append(f"- {date_str} | {concept.theme} | {concept.title}")
    lines.append("")
    lines.append("Se adjunta archivo con detalles, resumenes y analisis.")
    return lines


def _attach_csv_file(msg: MIMEMultipart, csv_path: Path) -> None:
    """Attach CSV file to email."""
    with open(csv_path, "rb") as handle:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(handle.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={csv_path.name}"
        )
        msg.attach(part)


def _send_smtp_message(msg: MIMEMultipart) -> None:
    """Send email via SMTP."""
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())
        logging.info("Correo enviado a %s", EMAIL_RECIPIENTS)
    except Exception as exc:
        logging.error("No se pudo enviar el correo: %s", exc)
