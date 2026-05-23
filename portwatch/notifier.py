"""Notification delivery: webhook and email, with optional retry support."""

from __future__ import annotations

import smtplib
import logging
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Any

import urllib.request
import json

from portwatch.retry import RetryConfig, with_retry

logger = logging.getLogger(__name__)


@dataclass
class NotifierConfig:
    webhook_url: str = ""
    email_to: list[str] = field(default_factory=list)
    email_from: str = "portwatch@localhost"
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    retry: RetryConfig = field(default_factory=RetryConfig)


def send_webhook(url: str, payload: dict[str, Any], retry: RetryConfig | None = None) -> None:
    """POST *payload* as JSON to *url*."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _do() -> None:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.debug("Webhook delivered, status=%s", resp.status)

    with_retry(_do, config=retry or RetryConfig())


def send_email(
    subject: str,
    body: str,
    config: NotifierConfig,
) -> None:
    """Send a plain-text alert email via SMTP."""
    if not config.email_to:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.email_from
    msg["To"] = ", ".join(config.email_to)
    msg.set_content(body)

    def _do() -> None:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as smtp:
            if config.smtp_user:
                smtp.login(config.smtp_user, config.smtp_password)
            smtp.send_message(msg)
            logger.debug("Email sent to %s", config.email_to)

    with_retry(_do, config=config.retry)


def notify(
    subject: str,
    body: str,
    payload: dict[str, Any],
    config: NotifierConfig,
) -> None:
    """Dispatch all configured notification channels."""
    if config.webhook_url:
        try:
            send_webhook(config.webhook_url, payload, retry=config.retry)
        except Exception as exc:
            logger.error("Webhook failed: %s", exc)

    if config.email_to:
        try:
            send_email(subject, body, config)
        except Exception as exc:
            logger.error("Email failed: %s", exc)
