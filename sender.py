"""
sender.py
Sends the HTML digest email via SendGrid.
"""

import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To
import settings

logger = logging.getLogger(__name__)


def send_digest(subject: str, html_content: str) -> bool:
    """
    Send digest to all recipients in EMAIL_TO.
    Returns True on success, False on failure.
    """
    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=[To(addr) for addr in settings.EMAIL_TO],
        subject=subject,
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(
            f"Email sent to {settings.EMAIL_TO} | "
            f"Status: {response.status_code}"
        )
        return response.status_code in (200, 202)
    except Exception as e:
        logger.error(f"SendGrid delivery failed: {e}")
        return False
