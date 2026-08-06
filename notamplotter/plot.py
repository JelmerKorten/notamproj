"""Plotting and geo/polygon logic for NotamPlotter.

Phase 2 (AGENT_PLAN.md): hosts the plotting half of the former
``notam_util.py`` -- everything from polygon creation to writing the final
``.html`` via Plotly.
"""

import copy
import re
from datetime import date

import pandas as pd
import plotly.graph_objects as go

from notamplotter._logging import get_logger
from notamplotter.parse import convert_coords, create_circle, readgcaacsv, readnotams

logger = get_logger(__name__)


def add_polygons(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``coords`` for anything containing 'BOUNDED'. Returns a new df.

    The coords returned are ``(lon, lat)`` to work with Plotly traces.
    """

    for i in range(len(df)):
        if "BOUNDED" in df.loc[df.index[i], "english"]:
            data = df.loc[df.index[i], "english"]
            data = [convert_coords(x) for x in _find_coord_strings(data)]
            data = [(x[1], x[0]) for x in data]
            df.at[df.index[i], "coords"] = data

    return df


def _find_coord_strings(text: str) -> list[str]:
    return re.findall(r"\d{6}(?:\.\d+)?[NS] \d{7}(?:\.\d+)?[EW]", text)


def add_multiple_circles(df: pd.DataFrame) -> pd.DataFrame:
    """Add circle/PSN radius info, converted from regex into usable values."""

    circle_list = []
    for i in range(len(df)):
        if "CIRCLE" in df.iloc[i].english:
            cur_list = []
            lat_matches = re.finditer(r"\d{6}(?:\.\d+)?[NS]", df.iloc[i].english)
            lat_res = [m.group() for m in lat_matches]
            lon_matches = re.finditer(r"\d{7}(?:\.\d+)?[EW]", df.iloc[i].english)
            lon_res = [m.group() for m in lon_matches]
            radius_match = re.search(r"\bRADIUS\b\s\d+(?:\.\d+)?\s?[a-zA-Z]+\b", df.iloc[i].english).group()
            coord_matches = [lat_res[i] + " " + lon_res[i] for i in range(len(lat_res))]
            cur_list.append(radius_match)
            cur_list.append(coord_matches)
            circle_list.append(cur_list)
        elif "PSN" in df.iloc[i].english:
            cur_list = []
            lat_matches = re.finditer(r"\d{6}(?:\.\d+)?[NS]", df.iloc[i].english)
            lat_res = [m.group() for m in lat_matches]
            lon_matches = re.finditer(r"\d{7}(?:\.\d+)?[EW]", df.iloc[i].english)
            lon_res = [m.group() for m in lon_matches]
            coord_matches = [lat_res[i] + " " + lon_res[i] for i in range(len(lat_res))]
            cur_list.append("RADIUS 300 M")
            cur_list.append(coord_matches)
            circle_list.append(cur_list)
        else:
            circle_list.append("")

    df["circles"] = circle_list

    dist_meas_map = {"M": 1, "NM": 1852, "KM": 1000}

    for item in df.circles:
        if item:
            dist = re.search(r"[0-9]+(?:\.\d+)?", item[0]).group()
            dist_meas = item[0][re.search(r"[0-9]+(?:\.\d+)?", item[0]).end() :].strip()

            dist_miles = float(dist) * dist_meas_map[dist_meas]
            item[0] = dist_miles
            coord_lst = []
            for coord_set in item[1]:
                coord_lst.append(convert_coords(coord_set))
            item[1] = coord_lst

    return df


def split_circles_add_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Split rows if multiple circles are found."""

    temp_master_data = pd.DataFrame(columns=df.columns)
    for i in range(len(df)):
        if isinstance(df.iloc[i].circles, list):
            temp_df = pd.DataFrame(columns=df.columns)
            for j in range(1, len(df.iloc[i].circles[1]) + 1):
                newindex = f"{df.index[i]}_{j}"
                cur_df = pd.DataFrame([df.iloc[i]], columns=df.columns, index=[newindex])

                latlon = df.iloc[i].circles[1][j - 1]
                radius = df.iloc[i].circles[0]

                cur_df.at[newindex, "coords"] = create_circle(latlon, radius)
                temp_df = pd.concat([temp_df, cur_df])
            temp_master_data = pd.concat([temp_master_data, temp_df])

    indexlist = list(temp_master_data.index)

    prev_index = None
    for new_index in indexlist:
        index_to_compare = new_index.split("_")[0]
        if index_to_compare != prev_index:
            df.drop(index=index_to_compare, axis=0, inplace=True)
        prev_index = index_to_compare

    return pd.concat([df, temp_master_data])


def create_jdata(df: pd.DataFrame) -> dict:
    """Build geoJSON ``jdata`` from ``df.coords`` and ``df.index`` for Plotly."""

    base_jdata = {
        "type": "FeatureCollection",
        "name": "notams",
        "features": [],
    }

    base_jdata_feature = {
        "type": "Feature",
        "properties": {"id": 0},
        "geometry": {"type": "Polygon", "coordinates": []},
    }

    jdata = copy.deepcopy(base_jdata)
    for i in range(len(df)):
        if df.coords.iloc[i]:
            feat = copy.deepcopy(base_jdata_feature)
            feat["properties"].update({"id": df.index[i]})
            feat["geometry"]["coordinates"].append(df.coords.iloc[i])
            jdata["features"].append(feat)

    return jdata


def back_traces(df: pd.DataFrame, jdata: dict, airports_str: str, filepath_out: str) -> None:
    """Plot the required shapes and write the final ``.html`` to ``filepath_out``."""

    ROUTECOL = "teal"
    LEG_WIDTH = 25

    today = date.today()
    plottitle = today.strftime("%Y %b %d")
    plottitle += f" {airports_str}"
    fig = go.Figure(
        go.Choroplethmapbox(
            name="Notams",
            geojson=jdata,
            text=df["wrap"],
            locations=df.index,
            z=[0] * len(df),
            featureidkey="properties.id",
            colorscale=[[0, "tomato"], [1, "tomato"]],
            showlegend=True,
            hovertemplate="%{text}",
            showscale=False,
            legendwidth=25,
            marker=dict(line=dict(color="red", width=1), opacity=0.5),
        )
    )

    fig.update_layout(
        title_text=f"Notams {plottitle}",
        title_x=0.5,
        width=1600,
        height=800,
        mapbox={
            "style": "open-street-map",
            "center": {"lon": 54.651512, "lat": 24.442970},
            "zoom": 9,
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 30},
    )

    fig.update_layout(hoverlabel=dict(bgcolor="white", font_size=12, font_family="Rockwell"))

    # commonly used routes
    fig.add_trace(
        go.Scattermapbox(
            name="aa3",
            mode="markers+lines",
            lon=[54.2, 54.3152, 54.45, 54.5377, 54.5982, 54.660418, 54.6112, 54.5458, 54.452, 54.3143, 54.1852],
            lat=[24.3745, 24.32, 24.3437, 24.3473, 24.4047, 24.420518, 24.393, 24.3307, 24.3273, 24.3, 24.3572],
            legendwidth=LEG_WIDTH,
            line=dict(color=ROUTECOL),
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            name="aa1",
            mode="markers+lines",
            lon=[54.589, 54.692, 54.681, 54.6604, 54.6633, 54.6732, 54.589],
            lat=[24.6345, 24.553, 24.482, 24.4205, 24.4867, 24.5515, 24.619],
            legendwidth=LEG_WIDTH,
            line=dict(color=ROUTECOL),
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            name="ad7",
            mode="markers+lines",
            lon=[54.4572, 54.4493, 54.4033, 54.2863],
            lat=[24.4133, 24.3928, 24.4122, 24.4533],
            legendwidth=LEG_WIDTH,
            line=dict(color=ROUTECOL),
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            name="aa3_dab",
            mode="markers+lines",
            lon=[54.3143, 54.144],
            lat=[24.3, 24.3187],
            legendwidth=LEG_WIDTH,
            line=dict(color=ROUTECOL),
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            name="aa3_dab",
            mode="markers+lines",
            lon=[54.3152, 54.1518],
            lat=[24.32, 24.338],
            legendwidth=LEG_WIDTH,
            line=dict(color=ROUTECOL),
        )
    )

    # grid lines
    minlon = 53.5
    maxlon = 56.5
    minlat = 24
    maxlat = 26
    gridlon = []
    for i in range(int(minlon * 10), int(maxlon * 10)):
        gridlon += [i / 10] * int((maxlat - minlat) * 10)
        gridlon.append(None)
    for i in range(int((maxlat - minlat) * 10)):
        gridlon += [i / 10 for i in range(int(minlon * 10), int(maxlon * 10))]
        gridlon.append(None)

    gridlat = []
    for i in range(int((maxlon - minlon) * 10)):
        gridlat += [i / 10 for i in range(int(minlat * 10), int(maxlat * 10))]
        gridlat.append(None)
    for i in range(int(minlat * 10), int(maxlat * 10)):
        gridlat += [i / 10] * int((maxlon - minlon) * 10)
        gridlat.append(None)

    fig.add_trace(
        go.Scattermapbox(
            name="grid",
            mode="lines",
            lon=gridlon,
            lat=gridlat,
            below="true",
            legendwidth=50,
            line=dict(color="lightgrey", width=1),
        )
    )

    # a trace per shape
    for i in range(len(df)):
        if df.loc[df.index[i], "coords"]:
            coords = df.loc[df.index[i], "coords"]
            lon = [item[0] for item in coords]
            lat = [item[1] for item in coords]
            fig.add_trace(
                go.Scattermapbox(
                    name=df.loc[df.index[i], "wrap"],
                    mode="lines",
                    lon=lon,
                    lat=lat,
                    fill="toself",
                    hoverinfo="skip",
                    legendwidth=0.1,
                    line=dict(color="tomato", width=1),
                )
            )

    fig.write_html(filepath_out, full_html=True)
    logger.info("html file created in output folder")


def handle(filepath_in=None, filepath_out=None, airports_str="omaa"):
    """Read a NOTAM file and write an ``.html`` plot."""
    logger.info("running handle()")
    df = readnotams(filepath_in, airports_str)
    logger.info("Notams read.")
    df = add_polygons(df)
    logger.info("polygons added")
    df = add_multiple_circles(df)
    logger.info("multiple circles added")
    df = split_circles_add_indices(df)
    logger.info("circles split")
    jdata = create_jdata(df)
    logger.info("jdata created")
    back_traces(df, jdata, airports_str, filepath_out)


def handle_gcaa(filepath_in=None, filepath_out=None, airports_str: str | None = None):
    """Read a GCAA file and generate an ``.html`` plot."""
    df = readgcaacsv(filepath_in)
    df = add_polygons(df)
    df = add_multiple_circles(df)
    df = split_circles_add_indices(df)
    jdata = create_jdata(df)
    back_traces(df, jdata, airports_str, filepath_out)
