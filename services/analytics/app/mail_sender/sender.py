"""Synchronous SMTP sender using stdlib only.

Usage::

    from mail_sender import send_mail

    send_mail(
        to="alice@example.com",
        subject="Hello",
        body="Plain text body",
        html="<p>Optional HTML</p>",
    )

Loads SMTP credentials from env (see backend/.env.example). Not wired into
any route - import and call from wherever you need it.

Because smtplib is blocking, call this from a threadpool when invoking
from async code, e.g. `await fastapi.concurrency.run_in_threadpool(send_mail, ...)`.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Iterable

from .config import SmtpSettings, load_smtp_settings

logger = logging.getLogger(__name__)


class MailSendError(RuntimeError):
    """Raised when the SMTP send fails or required settings are missing."""


def _normalize_recipients(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [v for v in value if v]


def send_mail(
    to: str | Iterable[str],
    subject: str,
    body: str,
    *,
    html: str | None = None,
    cc: str | Iterable[str] | None = None,
    bcc: str | Iterable[str] | None = None,
    reply_to: str | None = None,
    settings: SmtpSettings | None = None,
) -> None:
    """Send an email via SMTP. Raises MailSendError on any failure.

    `to` can be a single address or an iterable. `body` is plain text;
    `html` is optional alternative content.
    """
    cfg = settings or load_smtp_settings()

    missing = [
        name for name, val in (
            ("MAIL_SMTP_HOST", cfg.host),
            ("MAIL_FROM_ADDRESS", cfg.from_address),
        ) if not val
    ]
    if missing:
        raise MailSendError(f"Missing required mail config: {', '.join(missing)}")

    to_list = _normalize_recipients(to)
    cc_list = _normalize_recipients(cc)
    bcc_list = _normalize_recipients(bcc)
    if not to_list:
        raise MailSendError("At least one recipient is required")

    msg = EmailMessage()
    msg["From"] = formataddr((cfg.from_name, cfg.from_address))
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    all_recipients = to_list + cc_list + bcc_list

    try:
        if cfg.use_ssl:
            with smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=cfg.timeout) as smtp:
                if cfg.username:
                    smtp.login(cfg.username, cfg.password)
                smtp.send_message(msg, to_addrs=all_recipients)
        else:
            with smtplib.SMTP(cfg.host, cfg.port, timeout=cfg.timeout) as smtp:
                smtp.ehlo()
                if cfg.use_starttls:
                    smtp.starttls()
                    smtp.ehlo()
                if cfg.username:
                    smtp.login(cfg.username, cfg.password)
                smtp.send_message(msg, to_addrs=all_recipients)
    except smtplib.SMTPException as e:
        logger.exception("SMTP send failed")
        raise MailSendError(str(e)) from e
    except OSError as e:
        # Network errors (host unreachable, timeout, etc.)
        logger.exception("SMTP network error")
        raise MailSendError(str(e)) from e
