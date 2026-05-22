"""Notification backends for portwatch alerts."""

import json
import logging
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Optional
from urllib import request, error

logger = logging.getLogger(__name__)


@dataclass
class NotifierConfig:
    """Configuration for notification backends."""
    webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    use_tls: bool = True


def send_webhook(url: str, payload: dict, timeout: int = 10) -> bool:
    """Send a JSON payload to a webhook URL. Returns True on success."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as resp:
            logger.info("Webhook delivered, status=%s", resp.status)
            return resp.status < 300
    except error.URLError as exc:
        logger.error("Webhook delivery failed: %s", exc)
        return False


def send_email(config: NotifierConfig, subject: str, body: str) -> bool:
    """Send an alert email via SMTP. Returns True on success."""
    if not all([config.smtp_host, config.email_from, config.email_to]):
        logger.error("Incomplete SMTP configuration; email not sent.")
        return False
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.email_from
    msg["To"] = config.email_to
    try:
        smtp_cls = smtplib.SMTP
        with smtp_cls(config.smtp_host, config.smtp_port) as server:
            if config.use_tls:
                server.starttls()
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.email_from, [config.email_to], msg.as_string())
        logger.info("Email alert sent to %s", config.email_to)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Email delivery failed: %s", exc)
        return False


def notify(config: NotifierConfig, subject: str, body: str, payload: Optional[dict] = None) -> None:
    """Dispatch notifications to all configured backends."""
    if config.webhook_url:
        webhook_payload = payload or {"subject": subject, "body": body}
        send_webhook(config.webhook_url, webhook_payload)
    if config.smtp_host:
        send_email(config, subject, body)
