# This file is part of NotamPlotter.
# NotamPlotter plots notams on a streetmap.
# Copyright (C) 2023  Jelmer Korten (korty.codes)

# Thin CLI entry point (AGENT_PLAN.md, Phase 2).
# Orchestrates fetch -> handle using the ``notamplotter`` package and a
# :class:`~notamplotter.config.Config`.

import os
import sys
from datetime import date

from notamplotter._logging import setup_logging, get_logger
from notamplotter.cleanup import cleanup
from notamplotter.config import Config
from notamplotter.fetch import alternative, collect, read_gcaa_pdf, successfull_notam_fetch
from notamplotter.plot import handle, handle_gcaa

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
    # Clean up old files to save memory
    logger.info("calling cleanup()")
    cleanup(base=root, days=cfg.retention_days)

    today = date.today().strftime("%Y%m%d")
    airports_str = "_".join(cfg.airports)

    FILE_URL = os.path.join(root, cfg.files_dir, f"{today}_notams_{airports_str}.csv")
    OUTPUT_FILE = os.path.join(root, cfg.output_dir, f"{today}_notams_{airports_str}.html")

    file_integrity = successfull_notam_fetch(filepath=FILE_URL)
    if os.path.isfile(OUTPUT_FILE) and file_integrity:
        logger.info("file already exists")
        sys.exit()
    elif os.path.isfile(FILE_URL) and file_integrity:
        logger.info("csv already exists, creating html from that")
        handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE, airports_str=airports_str)
    else:
        logger.info("calling fetch_notams() to create .csv")
        collect(base=root, airports=airports_str)
        if successfull_notam_fetch(filepath=FILE_URL):
            logger.info("notam fetch seems successful. continuing.")
            handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE, airports_str=airports_str)
        else:
            logger.info("notam fetch seems invalid. fetching from other site.")
            alternative(root, airports=airports_str)
            logger.info("reading gcaa pdf")
            new_filename = read_gcaa_pdf(root)
            filepath_out = os.path.join(root, cfg.output_dir, os.path.basename(new_filename).split(".")[0] + ".html")
            handle_gcaa(filepath_in=new_filename, filepath_out=filepath_out)


if __name__ == "__main__":
    main(ROOT, CFG)
    sys.exit()
