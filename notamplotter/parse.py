"""Parsing of raw NOTAM text into DataFrames.

Phase 2 (AGENT_PLAN.md) split the parsing half of the former ``notam_util.py``
into this module (:func:`readnotams`, :func:`convert_coords`,
:func:`create_circle`). Phase 3 adds :func:`parse_icao_block` (a shared block
parser used by both :func:`readnotams` and :func:`parse_faa_response`) and
drops the GCAA format support (:func:`readgcaacsv`). Parsers build
:class:`~notamplotter.models.Notam` objects which are converted into the
DataFrame schema consumed by :mod:`notamplotter.plot`.
"""

import re
import textwrap
from datetime import date

import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

from notamplotter._logging import get_logger
from notamplotter.models import NOTAM_FIELDS, Notam

logger = get_logger(__name__)

# A NOTAM serial line such as ``A1718/25     NOTAMN`` or ``V0081/26 NOTAMN``.
_SERIAL_RE = re.compile(r"^[A-Z]\d{4}/\d{2}")

# Marker code -> resulting field name for ICAO block lines.
_BLOCK_FIELDS = {
    "Q": "short",
    "A": "icao",
    "B": "start_date",
    "C": "end_date",
    "D": "times",
    "E": "english",
    "F": "lower",
    "G": "upper",
}


def convert_coords(latlon: str) -> tuple:
    """Convert a coordinate string to a decimal ``(lat, lon)`` tuple.

    Accepts ``hhmmss.s(s)(N/S) hhhmmss.s(s)(E/W)`` format.
    """

    lat, lon = latlon.split()

    # latitude
    hemi = lat[-1]
    if "." in lat:
        dec_lat_sec = float(re.search(r"\d{2}\.\d+", lat).group()) / 60
        dec_lat_min = (float(re.search(r"\d+\.", lat).group()[-5:-3]) + dec_lat_sec) / 60
    else:
        dec_lat_sec = float(lat[-3:-1]) / 60
        dec_lat_min = (float(lat[-5:-3]) + dec_lat_sec) / 60

    lat_hrs = float(lat[:2])
    dec_lat = lat_hrs + dec_lat_min
    if hemi == "S":
        dec_lat *= -1

    # longitude
    side_earth = lon[-1]
    if "." in lon:
        dec_lon_sec = float(re.search(r"\d{2}\.\d+", lon).group()) / 60
        dec_lon_min = (float(re.search(r"\d+\.", lon).group()[-5:-3]) + dec_lon_sec) / 60
    else:
        dec_lon_sec = float(lon[-3:-1]) / 60
        dec_lon_min = (float(lon[-5:-3]) + dec_lon_sec) / 60

    lon_hrs = float(lon[:3])
    dec_lon = lon_hrs + dec_lon_min
    if side_earth == "W":
        dec_lon *= -1

    return (dec_lat, dec_lon)


def create_circle(latlon: tuple, radius: int) -> list:
    """Turn a point + radius into a list of (lon, lat) coords drawing a circle.

    ``latlon`` is a ``(lat, lon)`` decimal tuple, ``radius`` is in metres.
    """

    lat, lon = latlon[0], latlon[1]

    local_aeqd = f"+proj=aeqd +R=6371000 +units=m +lat_0={lat} +lon_0={lon}"
    std_wgs84 = "+proj=longlat +datum=WGS84 +no_defs"

    wgs84_to_aeqd = Transformer.from_proj(std_wgs84, local_aeqd)
    aeqd_to_wgs84 = Transformer.from_proj(local_aeqd, std_wgs84)

    point = Point(wgs84_to_aeqd.transform(lon, lat))
    buffer = point.buffer(radius)
    circle = transform(aeqd_to_wgs84.transform, buffer)

    return list(circle.exterior.coords)


def _to_frame(notams: list[Notam]) -> pd.DataFrame:
    """Build the standard plotting DataFrame from :class:`Notam` objects."""
    rows = {notam.serial: notam.to_dict() for notam in notams}
    df = pd.DataFrame.from_dict(rows, orient="index")
    df = df.reindex(columns=NOTAM_FIELDS)
    df["coords"] = ""
    df["wrap"] = ""
    for i in range(len(df)):
        idx = df.index[i]
        if df.loc[idx, "english"]:
            df.at[idx, "wrap"] = (
                f"{idx}<br>"
                + "<br>".join(textwrap.wrap(df.loc[idx, "english"], width=50))
                + "<br>Lower: "
                + str(df.loc[idx, "lower"])
                + " -- Upper: "
                + str(df.loc[idx, "upper"])
                + "<br>Dates From: "
                + str(df.loc[idx, "start_date"])
                + " To: "
                + str(df.loc[idx, "end_date"])
                + "<br>Times: "
                + str(df.loc[idx, "times"])
            )
    return df


def parse_icao_block(text: str) -> dict[str, str]:
    """Parse a raw ICAO NOTAM block into a dict of fields.

    Recognises the ``Q) A) B) C) D) E) F) G)`` markers whether each sits on its
    own line or several share one line. Unmarked lines are treated as
    continuation of the ``E)`` text. The first line is the ``serial``.
    Returns only the fields that are present.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {}

    result: dict[str, str] = {"serial": lines[0]}
    current = None
    for line in lines[1:]:
        for token in re.split(r"(?=[A-GQ]\))", line):
            if not token:
                continue
            match = re.match(r"([A-GQ]\))\s?(.*)", token, re.S)
            if match:
                code = match.group(1)[0]
                result[_BLOCK_FIELDS[code]] = match.group(2).strip()
                current = code
            elif current == "E":
                result["english"] = f"{result.get('english', '')} {token}".strip()
    return result


def _iter_blocks(text: str):
    """Yield each NOTAM block in ``text``, split on serial lines."""
    current: list[str] = []
    for line in text.splitlines():
        if current and _SERIAL_RE.match(line.strip()):
            yield "\n".join(current)
            current = []
        current.append(line)
    if current:
        yield "\n".join(current)


def readnotams(filepath: str | None = None, airports_str: str = "omaa") -> pd.DataFrame:
    """Read an FAA-format NOTAM file into the plotting DataFrame."""
    if filepath is None:
        today = date.today().strftime("%Y%m%d")
        filepath = f"files/{today}_notams_{airports_str}.csv"

    with open(filepath) as file:
        text = file.read()

    notams = []
    for block in _iter_blocks(text):
        parsed = parse_icao_block(block)
        if parsed:
            notams.append(
                Notam.from_dict(serial=parsed["serial"], data={k: v for k, v in parsed.items() if k != "serial"})
            )
    return _to_frame(notams)


def parse_faa_response(data: dict) -> pd.DataFrame:
    """Convert a parsed FAA API response into the plotting DataFrame.

    ``data`` is the JSON returned by :meth:`FaaClient.search` -- the raw
    ``icaoMessage`` blocks are parsed with :func:`parse_icao_block`, giving the
    same schema as :func:`readnotams`.
    """
    notams = []
    for item in data.get("notamList") or []:
        parsed = parse_icao_block(item.get("icaoMessage") or "")
        if not parsed:
            continue
        notams.append(
            Notam.from_dict(serial=parsed["serial"], data={k: v for k, v in parsed.items() if k != "serial"})
        )
    return _to_frame(notams)


def re_match_serial(text: str) -> bool:
    """Return True if ``text`` looks like a NOTAM serial line (e.g. ``A1718/25``)."""
    return bool(_SERIAL_RE.match(text))
