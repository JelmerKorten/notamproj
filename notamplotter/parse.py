"""Parsing of raw NOTAM text into DataFrames.

Phase 2 (AGENT_PLAN.md): hosts the parsing half of the former
``notam_util.py`` -- :func:`readnotams`, :func:`readgcaacsv`, :func:`convert_coords`
and :func:`create_circle`. Parsers build :class:`~notamplotter.models.Notam`
objects which are converted into the DataFrame schema consumed by
:mod:`notamplotter.plot`.
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


def readnotams(filepath: str | None = None, airports_str: str = "omaa") -> pd.DataFrame:
    """Read an FAA-format NOTAM file into the plotting DataFrame."""
    if filepath is None:
        today = date.today().strftime("%Y%m%d")
        filepath = f"files/{today}_notams_{airports_str}.csv"

    with open(filepath) as file:
        current_notams = file.readlines()

    for idx, line in enumerate(current_notams):
        current_notams[idx] = line.strip()

    startlines = []
    endlines = []
    for i, line in enumerate(current_notams):
        if line.find("Q)") != -1:
            startlines.append(i - 1)
        if "CREATED:" in line:
            endlines.append(i)

    notam_dict = {}
    for i in range(len(startlines) - 1):
        notam_dict.update({current_notams[startlines[i]]: current_notams[startlines[i] + 1 : startlines[i + 1] - 1]})
    try:
        notam_dict.update({current_notams[startlines[-1]]: current_notams[startlines[-1] : endlines[-1] + 1]})
    except Exception:
        print("No Notams downloaded, unable to process. This is most likely due to the new headless feature")
        logger.debug("No Notams downloaded. Check Headless feature and rewrite access code.")
        logger.debug("exiting program")
        raise SystemExit(0)

    long_dict = {}
    for key in notam_dict.keys():
        keydict = {}
        valuedictlist = []
        f_idx = 100
        created_idx = 100
        for i in range(len(notam_dict[key])):
            if "F)" in notam_dict[key][i]:
                f_idx = i
            if "CREATED: " in notam_dict[key][i]:
                created_idx = i
        e_end = min(f_idx, created_idx)

        for i, line in enumerate(notam_dict[key]):
            if "Q)" in notam_dict[key][i]:
                if "A)" in notam_dict[key][i]:
                    q_line = notam_dict[key][i][: notam_dict[key][i].find(" A)")]
                else:
                    q_line = notam_dict[key][i]
                valuedictlist.append({"short": q_line})

            if "A)" in notam_dict[key][i]:
                a_line = notam_dict[key][i][notam_dict[key][i].find("A)") + 3 : notam_dict[key][i].find("B)") - 1]
                b_line = notam_dict[key][i][notam_dict[key][i].find("B)") + 3 : notam_dict[key][i].find("C)") - 1]
                c_line = notam_dict[key][i][notam_dict[key][i].find("C)") + 3 :]

                valuedictlist.append({"icao": a_line})
                valuedictlist.append({"start_date": b_line})
                valuedictlist.append({"end_date": c_line})

            if "D)" in notam_dict[key][i]:
                d_line = notam_dict[key][i][notam_dict[key][i].find("D)") + 3 :]
                valuedictlist.append({"times": d_line})

            if "E)" in notam_dict[key][i]:
                e_line = notam_dict[key][i][notam_dict[key][i].find("E)") + 3 :]
                for j in range(i + 1, e_end):
                    e_line += " "
                    e_line += notam_dict[key][j]
                valuedictlist.append({"english": e_line})

            if "F)" in notam_dict[key][i]:
                f_line = notam_dict[key][i][notam_dict[key][i].find("F)") + 3 : notam_dict[key][i].find("G)") - 1]
                g_line = notam_dict[key][i][notam_dict[key][i].find("G)") + 3 :]
                valuedictlist.append({"lower": f_line})
                valuedictlist.append({"upper": g_line})

        keydict.update({key: valuedictlist})
        long_dict.update(keydict)

    notams = [
        Notam.from_dict(serial=key, data={a: b for item in lines for a, b in item.items()})
        for key, lines in long_dict.items()
    ]
    return _to_frame(notams)


def readgcaacsv(filepath: str) -> pd.DataFrame:
    """Read a GCAA-format NOTAM CSV into the plotting DataFrame."""
    with open(filepath) as file:
        notams = file.readlines()

    for idx, line in enumerate(notams):
        notams[idx] = line.strip()

    notam_dict = {}
    current_notam = {}
    name = ""
    english = False
    english_line = ""
    endfound = False

    for line in notams:
        if re.search(r"^[A-Z]\d{4}/\d{2}", line):
            name = line
            endfound = False
        elif line.startswith("Q)"):
            current_notam.update({"short": line[2:]})
        elif line.startswith("A)"):
            current_notam.update({"icao": line[2:]})
        elif line.startswith("B)"):
            current_notam.update({"start_date": line[2:]})
        elif line.startswith("C)"):
            current_notam.update({"end_date": line[2:]})
        elif line.startswith("D)"):
            current_notam.update({"times": line[2:]})
        elif line.startswith("E)"):
            english = True
            english_line = line[2:]
        elif line.startswith("F)"):
            if english:
                current_notam.update({"english": english_line})
                english = False
            current_notam.update({"lower": line[2:]})
        elif line.startswith("G)"):
            current_notam.update({"upper": line[2:]})
        elif line == "":
            endfound = True
        else:
            english_line += f" {line}"

        if endfound:
            if english:
                current_notam.update({"english": english_line})
            notam_dict.update({name: current_notam})
            current_notam = {}
            endfound = False

    notam_dict.update(current_notam)

    notams_objs = [Notam.from_dict(serial=key, data=value) for key, value in notam_dict.items()]
    return _to_frame(notams_objs)
