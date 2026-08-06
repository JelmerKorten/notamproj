"""Command-line interface for NotamPlotter.

Phase 4 (AGENT_PLAN.md): argparse subcommands:

* ``daily`` -- fetch today's NOTAMs, cache to CSV, build the HTML and email it
  (skips if today's HTML already exists; ``--refetch`` forces a fresh API call,
  ``--recreate`` rebuilds from today's cached CSV)
* ``fetch`` -- fetch NOTAMs and save a CSV (no HTML, no email)
* ``plot``  -- build HTML from an existing CSV
* ``email`` -- email the latest HTML in the output directory

SMTP credentials are read from config / environment variables (never from the
command line) so nothing secret ends up in shell history or process listings.
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from notamplotter._logging import get_logger, setup_logging
from notamplotter.config import Config
from notamplotter.emailer import EmailConfig, send_html_email
from notamplotter.fetch import FaaClient, collect
from notamplotter.parse import readnotams
from notamplotter.plot import handle

setup_logging()
logger = get_logger(__name__)


def _resolve_config(args) -> Config:
    cfg = Config.load(args.base)
    if args.airports:
        cfg.airports = [code.strip().lower() for code in args.airports.split(",") if code.strip()]
    return cfg


def _airports_str(cfg: Config) -> str:
    return "_".join(cfg.airports)


def _today_str() -> str:
    return date.today().strftime("%Y%m%d")


def _default_output(cfg: Config) -> str:
    return os.path.join(cfg.output_dir, f"{_today_str()}_notams_{_airports_str(cfg)}.html")


def _default_csv(cfg: Config) -> str:
    return os.path.join(cfg.files_dir, f"{_today_str()}_notams_{_airports_str(cfg)}.csv")


def _send_email(cfg: Config, html_path: str) -> None:
    email_cfg = EmailConfig.from_config(cfg)
    try:
        email_cfg.validate()
    except ValueError as exc:
        logger.warning("skipping email: %s", exc)
        return
    send_html_email(email_cfg, html_path)
    logger.info("email sent")


def _latest_html(output_dir: str) -> Path:
    htmls = sorted(Path(output_dir).glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not htmls:
        raise FileNotFoundError(f"no .html files found in {output_dir!r}")
    return htmls[0]


def cmd_daily(args) -> None:
    """Fetch today's NOTAMs, build the HTML and email it.

    The API result is cached to ``files/{today}_notams_*.csv``. When today's
    HTML already exists the command does nothing, unless ``--refetch`` (fresh
    API call) or ``--recreate`` (rebuild from today's cached CSV) is given.
    """
    cfg = _resolve_config(args)
    output_file = _default_output(cfg)

    if args.recreate:
        csv_file = _default_csv(cfg)
        logger.info("rebuilding %s from %s", output_file, csv_file)
        df = readnotams(csv_file, airports_str=_airports_str(cfg))
        handle(df, filepath_out=output_file, airports_str=_airports_str(cfg))
        _send_email(cfg, output_file)
        return

    if not args.refetch and os.path.exists(output_file):
        logger.info("daily output already exists for today: %s (use --refetch to rebuild)", output_file)
        return

    logger.info("fetching NOTAMs for %s", ", ".join(cfg.airports))
    client = FaaClient(base_url=cfg.faa_api_base_url)
    csv_file = collect(base=args.base, airports=cfg.airports, client=client)

    df = readnotams(csv_file, airports_str=_airports_str(cfg))
    logger.info("parsed %d notams", len(df))
    handle(df, filepath_out=output_file, airports_str=_airports_str(cfg))
    logger.info("html written to %s", output_file)

    _send_email(cfg, output_file)


def cmd_fetch(args) -> None:
    """Fetch NOTAMs and save a CSV file."""
    cfg = _resolve_config(args)
    client = FaaClient(base_url=cfg.faa_api_base_url)
    filepath = collect(base=args.base, airports=cfg.airports, client=client)
    logger.info("csv saved to %s", filepath)


def cmd_plot(args) -> None:
    """Build HTML from an existing CSV."""
    cfg = _resolve_config(args)
    output_file = args.output or _default_output(cfg)

    df = readnotams(args.csv, airports_str=_airports_str(cfg))
    logger.info("read %d notams from %s", len(df), args.csv)
    handle(df, filepath_out=output_file, airports_str=_airports_str(cfg))
    logger.info("html written to %s", output_file)


def cmd_email(args, html_path: str | None = None) -> None:
    """Email the latest HTML (or ``html_path``) in the output directory."""
    cfg = _resolve_config(args)
    path = html_path or args.html or _latest_html(cfg.output_dir)
    email_cfg = EmailConfig.from_config(cfg)
    send_html_email(email_cfg, path)
    logger.info("email sent")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notamplotter",
        description="Fetch, plot and email NOTAMs from the FAA NOTAM search API.",
    )
    parser.add_argument("--base", default=".", help="project root directory (default: current directory)")
    parser.add_argument("--airports", help="comma-separated ICAO codes (overrides config)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_daily = sub.add_parser("daily", help="fetch today's NOTAMs, build the HTML and email it")
    daily_group = p_daily.add_mutually_exclusive_group()
    daily_group.add_argument(
        "--refetch",
        action="store_true",
        help="force a fresh fetch from the FAA API (ignore any cached HTML/CSV)",
    )
    daily_group.add_argument(
        "--recreate",
        action="store_true",
        help="rebuild today's HTML from today's cached CSV without calling the API",
    )

    sub.add_parser("fetch", help="fetch NOTAMs and save a CSV (no HTML, no email)")

    p_plot = sub.add_parser("plot", help="build HTML from an existing CSV")
    p_plot.add_argument("csv", help="path to the NOTAM CSV file")
    p_plot.add_argument("--output", help="output .html path (default: output/<today>_notams_<airports>.html)")

    p_email = sub.add_parser("email", help="email the latest HTML in the output directory")
    p_email.add_argument("--html", help="path to the .html file to send (default: newest in output/)")

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    command = args.command
    try:
        {"daily": cmd_daily, "fetch": cmd_fetch, "plot": cmd_plot, "email": cmd_email}[command](args)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
