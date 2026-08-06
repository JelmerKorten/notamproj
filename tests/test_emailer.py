"""Phase 4 tests for the SMTP emailer (AGENT_PLAN.md).

Uses a fake SMTP server so no network or real credentials are needed.
"""

import smtplib

import pytest

from notamplotter.config import Config
from notamplotter.emailer import EmailConfig, send_html_email


def _sample_cfg(**overrides) -> EmailConfig:
    values = dict(
        host="smtp.example.com",
        port=587,
        user="user@example.com",
        password="secret",
        from_addr="user@example.com",
        to_addr="to@example.com",
    )
    values.update(overrides)
    return EmailConfig(**values)


class FakeSMTP:
    """Minimal SMTP stand-in that records calls instead of sending."""

    sent: list = []
    logins: int = 0
    starttls_called: bool = False

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def ehlo(self):
        pass

    def starttls(self, *args, **kwargs):
        FakeSMTP.starttls_called = True

    def login(self, *args, **kwargs):
        FakeSMTP.logins += 1

    def send_message(self, message):
        FakeSMTP.sent.append(message)

    def quit(self):
        pass


@pytest.fixture
def html_file(tmp_path):
    path = tmp_path / "20260806_notams_test.html"
    path.write_text("<html><body>plot</body></html>")
    return path


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    FakeSMTP.sent = []
    FakeSMTP.logins = 0
    FakeSMTP.starttls_called = False
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    return FakeSMTP


def test_from_config_maps_all_fields():
    cfg = Config(
        smtp_host="host", smtp_port=465, smtp_user="u", smtp_pass="p", email_from="f", email_to="t"
    )
    email_cfg = EmailConfig.from_config(cfg)
    assert email_cfg == EmailConfig("host", 465, "u", "p", "f", "t")


def test_send_uses_starttls_and_attachment(fake_smtp, html_file):
    cfg = _sample_cfg()
    send_html_email(cfg, html_file)
    assert fake_smtp.starttls_called
    assert fake_smtp.logins == 1
    assert len(fake_smtp.sent) == 1

    message = fake_smtp.sent[0]
    assert message["To"] == "to@example.com"
    assert message["From"] == "user@example.com"
    assert message["Subject"] == f"NotamPlotter NOTAMs - {html_file.stem}"

    attachment = next(part for part in message.iter_parts() if part.get_filename())
    assert attachment.get_filename() == html_file.name
    assert attachment.get_payload(decode=True) == html_file.read_bytes()


def test_send_uses_implicit_tls_on_port_465(fake_smtp, html_file):
    send_html_email(_sample_cfg(port=465), html_file)
    assert fake_smtp.logins == 1
    assert len(fake_smtp.sent) == 1


def test_send_missing_file_raises(fake_smtp, tmp_path):
    with pytest.raises(FileNotFoundError):
        send_html_email(_sample_cfg(), tmp_path / "does-not-exist.html")


def test_send_missing_config_raises(html_file):
    with pytest.raises(ValueError, match="missing SMTP configuration"):
        send_html_email(_sample_cfg(host=""), html_file)
