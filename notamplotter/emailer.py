"""Email delivery for NotamPlotter.

Phase 4 (AGENT_PLAN.md): sends the generated HTML plot as an email attachment
over SMTP. Credentials come exclusively from configuration / environment
variables (never hard-coded) and are never logged.

Authentication supports two mechanisms:

* OAuth2 (``XOAUTH2``) for Gmail -- a refresh token from configuration /
  environment / CI secrets is exchanged for a short-lived access token at send
  time (see :mod:`notamplotter.gmail_oauth`).
* classic SMTP ``LOGIN`` with a password for other relays.
"""

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from notamplotter._logging import get_logger
from notamplotter.gmail_oauth import refresh_access_token, xoauth2_string

logger = get_logger(__name__)


@dataclass
class EmailConfig:
    """SMTP credentials and recipients for the emailer.

    Authentication requires either ``password`` (classic SMTP LOGIN) or the
    Gmail OAuth2 trio (``google_client_id`` + ``google_client_secret`` +
    ``google_refresh_token``) for XOAUTH2.
    """

    host: str
    port: int = 587
    user: str = ""
    password: str = ""
    from_addr: str = ""
    to_addr: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""

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
            google_client_id=cfg.google_client_id,
            google_client_secret=cfg.google_client_secret,
            google_refresh_token=cfg.google_refresh_token,
        )

    def validate(self) -> None:
        """Raise :class:`ValueError` if any required field is unset."""
        missing = [name for name, value in self._required() if not value]
        if missing:
            raise ValueError(f"missing SMTP configuration: {', '.join(missing)} (set via env vars or config)")

    def _required(self) -> tuple[tuple[str, str], ...]:
        auth: tuple[tuple[str, str], ...]
        if self.google_client_id and self.google_client_secret and self.google_refresh_token:
            auth = (
                ("GOOGLE_CLIENT_ID", self.google_client_id),
                ("GOOGLE_CLIENT_SECRET", self.google_client_secret),
                ("GOOGLE_REFRESH_TOKEN", self.google_refresh_token),
            )
        else:
            auth = (("SMTP_PASS", self.password),)
        return (
            ("SMTP_HOST", self.host),
            ("SMTP_USER", self.user),
            *auth,
            ("EMAIL_FROM", self.from_addr),
            ("EMAIL_TO", self.to_addr),
        )

    @property
    def oauth(self) -> bool:
        """True when the Gmail OAuth2 (XOAUTH2) trio is configured.

        Takes precedence over a classic password when both are present so a
        placeholder ``SMTP_PASS`` can never cause a fallback to LOGIN.
        """
        return bool(
            self.google_client_id
            and self.google_client_secret
            and self.google_refresh_token
        )


def send_html_email(cfg: EmailConfig, html_path: str | Path, subject: str | None = None) -> None:
    """Send ``html_path`` as an email attachment over SMTP.

    Uses implicit TLS on port 465 and STARTTLS otherwise (587). Authenticates
    with OAuth2 XOAUTH2 when :attr:`EmailConfig.oauth` is set, otherwise with
    classic ``LOGIN``. Credentials are used only for authentication and are
    never logged.
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
        if cfg.oauth:
            access_token = refresh_access_token(
                cfg.google_client_id,
                cfg.google_client_secret,
                cfg.google_refresh_token,
            )
            server.auth("XOAUTH2", lambda _challenge=None: xoauth2_string(cfg.user, access_token))
        else:
            server.login(cfg.user, cfg.password)
        server.send_message(message)
    finally:
        server.quit()
