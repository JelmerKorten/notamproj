# This file is part of NotamPlotter.
# NotamPlotter plots notams on a streetmap.
# Copyright (C) 2023  Jelmer Korten (korty.codes)

# Backwards-compatibility shim.
#
# The former god module has been split into the ``notamplotter`` package
# (AGENT_PLAN.md, Phase 2), and Phase 3 migrated the data source to the FAA
# API (:class:`~notamplotter.fetch.FaaClient`), dropping the GCAA/Selenium
# paths. This file exists only to keep ``import notam_util`` working for any
# external/old callers; it re-exports the public functions from the new
# package. Archive it once all entry points stop importing it.

from notamplotter.fetch import FaaClient, collect, fetch_notams
from notamplotter.parse import (
    convert_coords,
    create_circle,
    parse_faa_response,
    parse_icao_block,
    readnotams,
    re_match_serial,
)
from notamplotter.plot import (
    add_multiple_circles,
    add_polygons,
    back_traces,
    create_jdata,
    handle,
    split_circles_add_indices,
)

__all__ = [
    "FaaClient",
    "add_multiple_circles",
    "add_polygons",
    "back_traces",
    "collect",
    "convert_coords",
    "create_circle",
    "create_jdata",
    "fetch_notams",
    "handle",
    "parse_faa_response",
    "parse_icao_block",
    "readnotams",
    "re_match_serial",
    "split_circles_add_indices",
]