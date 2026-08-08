# This file is part of NotamPlotter.
# NotamPlotter plots notams on a streetmap.
# Copyright (C) 2023  Jelmer Korten (korty.codes)

# Thin CLI entry point (AGENT_PLAN.md, Phase 2).
# Orchestrates fetch -> plot using the ``notamplotter`` package and a
# :class:`~notamplotter.config.Config`.

import os
import sys
from datetime import date

from notamplotter._logging import setup_logging, get_logger
from notamplotter.config import Config
from notamplotter.fetch import FaaClient, fetch_notams
from notamplotter.parse import parse_faa_response
from notamplotter.plot import handle

setup_logging()
logger = get_logger(__name__)


def find_data_dir():
    """Return the directory containing this file (or the frozen executable)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


ROOT = find_data_dir()
CFG = Config.load(ROOT)


def main(root, cfg):
    today = date.today().strftime("%Y%m%d")
    airports_str = "_".join(cfg.airports)

    OUTPUT_FILE = os.path.join(root, cfg.output_dir, f"{today}_notams_{airports_str}.html")

    if os.path.isfile(OUTPUT_FILE):
        logger.info("file already exists")
        sys.exit()

    logger.info("calling fetch_notams() against the FAA API")
    client = FaaClient(base_url=cfg.faa_api_base_url)
    notams = fetch_notams(cfg.airports, client)

    df = parse_faa_response({"notamList": notams, "totalNotamCount": len(notams)})
    logger.info("parsed %d notams", len(df))
    handle(df, filepath_out=OUTPUT_FILE, airports_str=airports_str)


if __name__ == "__main__":
    main(ROOT, CFG)
    sys.exit()
