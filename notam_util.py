# This file is part of NotamPlotter.
# NotamPlotter plots notams on a streetmap.
# Copyright (C) 2023  Jelmer Korten (korty.codes)

# Backwards-compatibility shim.
#
# The former god module has been split into the ``notamplotter`` package
# (AGENT_PLAN.md, Phase 2). This file exists only to keep ``import notam_util``
# working for any external/old callers; it re-exports the public functions from
# the new package. Archive it once all entry points stop importing it.

from notamplotter.cleanup import cleanup
from notamplotter.fetch import (
    alternative,
    collect,
    fetch_notams,
    read_gcaa_pdf,
    re_match_serial,
    successfull_notam_fetch,
)
from notamplotter.parse import (
    convert_coords,
    create_circle,
    readgcaacsv,
    readnotams,
)
from notamplotter.plot import (
    add_multiple_circles,
    add_polygons,
    back_traces,
    create_jdata,
    handle,
    handle_gcaa,
    split_circles_add_indices,
)

__all__ = [
    "add_multiple_circles",
    "add_polygons",
    "alternative",
    "back_traces",
    "cleanup",
    "collect",
    "convert_coords",
    "create_circle",
    "create_jdata",
    "fetch_notams",
    "handle",
    "handle_gcaa",
    "read_gcaa_pdf",
    "readgcaacsv",
    "readnotams",
    "re_match_serial",
    "split_circles_add_indices",
    "successfull_notam_fetch",
]
