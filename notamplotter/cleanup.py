"""File retention / cleanup.

Phase 2 (AGENT_PLAN.md): hosts :func:`cleanup`, formerly in ``notam_util.py``.
"""

from pathlib import Path
import os

import arrow

from notamplotter._logging import get_logger

logger = get_logger(__name__)


def cleanup(base, days: int) -> None:
    """Walk the files/output dirs and delete files older than ``days`` days.

    Only matching ``*_notams*`` files are removed.
    """
    logger.info("running cleanup")
    remove_time = arrow.now().shift(days=-days)
    for folder in ("files", "output"):
        folder_path = os.path.join(base, folder)
        for item in Path(folder_path).glob("*_notams*"):
            if not item.is_file():
                continue
            if arrow.get(item.stat().st_mtime) < remove_time:
                os.remove(item)
                logger.info(f"Removing {item}")
