"""Configuration handling for NotamPlotter.

Pattern (AGENT_PLAN.md, Phase 2):

* ``.env``            -- local secrets / values, loaded with python-dotenv.
* ``config.yaml``     -- optional committed defaults (also accepts ``config.toml``).
* environment vars    -- highest priority, override anything above.

Precedence (lowest to highest): built-in defaults -> config file -> env vars.

The :class:`Config` dataclass holds all values so callers never reach for
``os.environ`` directly. Secrets (``SMTP_PASS``) are held in the object but
never logged.
"""

from dataclasses import dataclass, field
from pathlib import Path
import os
import tomllib

from dotenv import load_dotenv

from notamplotter._logging import get_logger

logger = get_logger(__name__)

# Environment variables with the highest precedence: ENV name -> Config field.
ENV_MAPPING = {
    "NOTAM_AIRPORTS": "airports",
    "NOTAM_OUTPUT_DIR": "output_dir",
    "NOTAM_FILES_DIR": "files_dir",
    "NOTAM_LOG_LEVEL": "log_level",
    "FAA_API_BASE_URL": "faa_api_base_url",
    "SMTP_HOST": "smtp_host",
    "SMTP_PORT": "smtp_port",
    "SMTP_USER": "smtp_user",
    "SMTP_PASS": "smtp_pass",
    "EMAIL_FROM": "email_from",
    "EMAIL_TO": "email_to",
}

# Keys accepted under the optional ``email:`` section of the config file.
EMAIL_FILE_KEYS = {"smtp_host", "smtp_port", "smtp_user", "smtp_pass", "email_from", "email_to"}

_INT_FIELDS = {"smtp_port"}
_LIST_FIELDS = {"airports"}


@dataclass
class Config:
    """Resolved runtime configuration."""

    airports: list[str] = field(default_factory=lambda: ["EHAM","NZSP","VHHH","SEQM"])
    files_dir: str = "files"
    output_dir: str = "output"
    log_level: str = "INFO"
    faa_api_base_url: str = "https://notams.aim.faa.gov/notamSearch"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    email_from: str = ""
    email_to: str = ""

    @classmethod
    def load(cls, base_dir: str | Path = ".") -> "Config":
        """Load config from file + env and return a :class:`Config`."""
        load_dotenv(_env_file(base_dir))
        merged = {name: getattr(cls(), name) for name in cls.__dataclass_fields__}
        merged = _apply_file(_load_file(base_dir), merged)
        merged = _apply_env(merged)
        return cls(**merged)


def _env_file(base_dir: str | Path) -> Path:
    """Return the local ``.env`` path (loaded only if present)."""
    return Path(base_dir) / ".env"


def _load_file(base_dir: str | Path) -> dict:
    """Return a dict from an optional ``config.yaml`` or ``config.toml``."""
    base = Path(base_dir)
    for candidate in (base / "config.yaml", base / "config.yml"):
        if candidate.is_file():
            try:
                import yaml
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("Reading config.yaml requires PyYAML") from exc
            with candidate.open() as fh:
                return yaml.safe_load(fh) or {}
    if (base / "config.toml").is_file():
        with (base / "config.toml").open("rb") as fh:
            return tomllib.load(fh)
    return {}


def _apply_file(file_cfg: dict, merged: dict) -> dict:
    """Merge ``nested = {"email": {...}}``-style file config into flat keys."""
    for key in ("airports", "files_dir", "output_dir", "log_level", "faa_api_base_url"):
        if key in file_cfg:
            _coerce(merged, key, file_cfg[key])
    email = file_cfg.get("email") or {}
    for key in EMAIL_FILE_KEYS:
        if key in email:
            _coerce(merged, key, email[key])
    return merged


def _apply_env(merged: dict) -> dict:
    """Override merged values with any environment variables that are set."""
    for env, name in ENV_MAPPING.items():
        value = os.environ.get(env)
        if value is not None:
            _coerce(merged, name, value)
    return merged


def _coerce(merged: dict, field: str, value) -> None:
    if field in _LIST_FIELDS:
        items = value if isinstance(value, list) else str(value).split(",")
        merged[field] = [part.strip().lower() for part in items if str(part).strip()]
    elif field in _INT_FIELDS:
        merged[field] = int(value)
    else:
        merged[field] = str(value)
