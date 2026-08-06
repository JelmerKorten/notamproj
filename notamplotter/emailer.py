"""Email delivery for NotamPlotter.

Phase 4 (AGENT_PLAN.md): sends the generated HTML plot as an email attachment
over SMTP. Credentials come exclusively from configuration / environment
variables (never hard-coded) and are never logged.
"""

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from notamplotter._logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmailConfig:
    """SMTP credentials and recipients for the emailer."""

    host: str
    port: int = 587
    user: str = ""
    password: str = ""
    from_addr: str = ""
    to_addr: str = ""

    @classmethod
    def from_config(cls, cfg) -> "EmailConfig":
        """Build an :class:`EmailConfig` from a :class:`~notamplotter.config.Config`."""
        return cls(
            host=cfg.smtp_host,
            port=cfg.smtp_port or 587,
            user=cfg.smtp_user,
            password=cfg.smtp_pass,
            from_addr=cfg.email_from,
            to_addr=cfg.email_to,
        )

    def validate(self) -> None:
        """Raise :class:`ValueError` if any required field is unset."""
        missing = [name for name, value in self._required() if not value]
        if missing:
            raise ValueError(f"missing SMTP configuration: {', '.join(missing)} (set via env vars or config)")

    def _required(self) -> tuple[tuple[str, str], ...]:
        return (
            ("SMTP_HOST", self.host),
            ("SMTP_USER", self.user),
            ("SMTP_PASS", self.password),
            ("EMAIL_FROM", self.from_addr),
            ("EMAIL_TO", self.to_addr),
        )


def send_html_email(cfg: EmailConfig, html_path: str | Path, subject: str | None = None) -> None:
    """Send ``html_path`` as an email attachment over SMTP.

    Uses implicit TLS on port 465 and STARTTLS otherwise (587). The password is
    used only for authentication and is never logged.
    """
    cfg.validate()
    path = Path(html_path)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {path}")

    message = EmailMessage()
    message["Subject"] = subject or f"NotamPlotter NOTAMs - {path.stem}"
    message["From"] = cfg.from_addr
    message["To"] = cfg.to_addr
    message.set_content("NotamPlotter HTML output is attached.")
    message.add_attachment(path.read_bytes(), maintype="application", subtype="octet-stream", filename=path.name)

    if cfg.port == 465:
        _send_with(smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=60, context=ssl.create_default_context()), cfg, message)
    else:
        server = smtplib.SMTP(cfg.host, cfg.port, timeout=60)
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        _send_with(server, cfg, message)

    logger.info("emailed %s to %s", path.name, cfg.to_addr)


def _send_with(server, cfg: EmailConfig, message: EmailMessage) -> None:
    try:
        server.login(cfg.user, cfg.password)
        server.send_message(message)
    finally:
        server.quit()
