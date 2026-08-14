"""Transactional email delivery via SMTP.

Local development defaults to a no-op (no SMTP configured) so nothing breaks
without external credentials. When SMTP_HOST is set (e.g. Mailpit locally or
a real provider in production) emails are sent synchronously with a short
timeout; failures are logged and never raise into the request path.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("yenimenzil.email")


def send_email(
    to: str,
    subject: str,
    text_body: str,
    *,
    html_body: str | None = None,
) -> bool:
    """Send one transactional email. Returns False when SMTP is unconfigured.

    Never raises: delivery problems are logged only.
    """
    settings = get_settings()
    if not settings.SMTP_HOST:
        logger.info("SMTP not configured; email to %s skipped", to)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.DEFAULT_FROM_EMAIL
    message["To"] = to
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=10
        ) as smtp:
            if settings.SMTP_USE_TLS:
                context = ssl.create_default_context()
                smtp.starttls(context=context)
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception:  # noqa: BLE001 - never break the request for email
        logger.exception("Failed to send email to %s", to)
        return False
