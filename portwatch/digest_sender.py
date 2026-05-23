"""digest_sender: flush a Digest and dispatch the result via notifier."""

from __future__ import annotations

import logging
from typing import Optional

from portwatch.digest import Digest, build_digest_body
from portwatch.notifier import NotifierConfig, send_webhook, send_email

log = logging.getLogger(__name__)


def maybe_flush_and_send(
    digest: Digest,
    notifier: NotifierConfig,
    *,
    force: bool = False,
) -> bool:
    """Flush the digest if ready (or forced) and send a notification.

    Returns True if a notification was dispatched, False otherwise.
    """
    if not digest.config.enabled:
        return False

    if not force and not digest.is_ready():
        return False

    if digest.pending_count() == 0:
        log.debug("digest flush requested but no pending entries")
        return False

    entries = digest.flush()
    body = build_digest_body(entries)
    subject = f"Portwatch digest: {len(entries)} change(s) detected"

    dispatched = False

    if notifier.webhook_url:
        try:
            send_webhook(notifier, payload={"text": body, "subject": subject})
            dispatched = True
        except Exception as exc:  # pragma: no cover
            log.error("digest webhook failed: %s", exc)

    if notifier.smtp_host and notifier.email_to:
        try:
            send_email(notifier, subject=subject, body=body)
            dispatched = True
        except Exception as exc:  # pragma: no cover
            log.error("digest email failed: %s", exc)

    if dispatched:
        log.info("digest sent: %d entries", len(entries))
    else:
        log.warning("digest ready but no notifier channel configured")

    return dispatched
