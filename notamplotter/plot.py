"""Plotting and geo/polygon logic for NotamPlotter.

Phase 2 (AGENT_PLAN.md): hosts the plotting half of the former
``notam_util.py`` -- everything from polygon creation to writing the final
``.html`` via Plotly. Phase 3 changes :func:`handle` to consume a DataFrame
directly (built by :func:`~notamplotter.parse.parse_faa_response`) and drops
the GCAA path (:func:`handle_gcaa`).
"""

import copy
import re
from datetime import date
from html import escape

import pandas as pd
import plotly.graph_objects as go

from notamplotter._logging import get_logger
from notamplotter.parse import convert_coords, create_circle

logger = get_logger(__name__)

_SEARCH_UI = (
    '<div id="notam-search-wrap">'
    '<input id="notam-search" type="text" placeholder="Search NOTAMs..." />'
    '<button id="notam-reset" type="button">Show all</button>'
    "</div>"
)

_LEGEND_DIVIDER = "-------------------------<br>"

_SEARCH_JS = r"""
(function () {
  var gd = document.getElementById('notamplot');
  if (!gd || !gd.data || !gd.data.length) return;
  var CHORO = 0;
  var choro = gd.data[CHORO];
  var features = (choro && choro.geojson && choro.geojson.features) || [];
  var ids = new Set(features.map(function (f) { return String(f.properties.id); }));
  var allText = (choro && choro.text) || [];
  var allLocs = (choro && choro.locations) || [];
  var notams = [];
  for (var i = 0; i < gd.data.length; i++) {
    if (gd.data[i].meta != null && ids.has(String(gd.data[i].meta))) notams.push(i);
  }
  var search = document.getElementById('notam-search');
  var reset = document.getElementById('notam-reset');

  function setVisible(keep) {
    var showS = [], hideS = [];
    var keepLocs = [], keepZ = [], keepText = [];
    for (var i = 0; i < notams.length; i++) {
      var id = String(gd.data[notams[i]].meta);
      if (keep === null || keep.has(id)) showS.push(notams[i]);
      else hideS.push(notams[i]);
    }
    if (showS.length) Plotly.restyle(gd, { visible: true, showlegend: true }, showS);
    if (hideS.length) Plotly.restyle(gd, { visible: false, showlegend: false }, hideS);
    for (var j = 0; j < allLocs.length; j++) {
      var lid = String(allLocs[j]);
      if (keep === null || keep.has(lid)) {
        keepLocs.push(allLocs[j]);
        keepZ.push(0);
        keepText.push(allText[j]);
      }
    }
    var data = gd.data.slice();
    data[CHORO] = Object.assign({}, gd.data[CHORO], {
      locations: keepLocs,
      z: keepZ,
      text: keepText,
    });
    Plotly.react(gd, data, gd.layout, { responsive: true });
  }

  function fitZoom(west, east, south, north) {
    var rect = gd.getBoundingClientRect();
    var width = Math.max(rect.width, 10), height = Math.max(rect.height, 10);
    var R = 6378137, TILE = 512, world = 2 * Math.PI * R;
    function mx(lon) { return lon * Math.PI / 180 * R; }
    function my(lat) { return Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * R; }
    var dx = Math.max(Math.abs(mx(east) - mx(west)), 1);
    var dy = Math.max(Math.abs(my(north) - my(south)), 1);
    var zx = Math.log2(width * 0.8 * world / (dx * TILE));
    var zy = Math.log2(height * 0.8 * world / (dy * TILE));
    return Math.max(0, Math.min(17, Math.min(zx, zy)));
  }

  function zoomToTrace(ci) {
    var tr = gd.data[ci];
    if (!tr || tr.meta == null || !ids.has(String(tr.meta))) return;
    var lon = tr.lon || [], lat = tr.lat || [];
    if (!lon.length) return;
    var west = Math.min.apply(null, lon), east = Math.max.apply(null, lon);
    var south = Math.min.apply(null, lat), north = Math.max.apply(null, lat);
    var dw = Math.max((east - west) * 0.15, 0.005);
    var dh = Math.max((north - south) * 0.15, 0.005);
    setVisible(new Set([String(tr.meta)]));
    Plotly.relayout(gd, {
      'mapbox.center': { lon: (west + east) / 2, lat: (south + north) / 2 },
      'mapbox.zoom': fitZoom(west - dw, east + dw, south - dh, north + dh)
    });
  }

  if (search) {
    var debounceTimer = null;
    search.addEventListener('input', function () {
      var q = search.value.trim().toLowerCase();
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        if (!q) { setVisible(null); return; }
        var keep = new Set();
        for (var i = 0; i < notams.length; i++) {
          var tr = gd.data[notams[i]];
          if ((tr.name || '').toLowerCase().indexOf(q) !== -1) keep.add(String(tr.meta));
        }
        setVisible(keep);
      }, 150);
    });
  }

  function resolveTrace(p) {
    var cn = p.curveNumber;
    var tr = gd.data[cn];
    if (tr && tr.meta != null && ids.has(String(tr.meta))) return cn;
    if (cn === CHORO && p.location != null) {
      for (var i = 0; i < notams.length; i++) {
        if (String(gd.data[notams[i]].meta) === String(p.location)) return notams[i];
      }
    }
    return null;
  }

  if (gd.on) {
    // On mapbox, plotly_doubleclick fires with `null` data and only after
    // Plotly has reset the view, so recover the double-clicked NOTAM from the
    // last plotly_click (which carries the trace) and pan to it here.
    var lastNotamClick = { t: 0, ci: null };
    gd.on('plotly_click', function (ev) {
      if (!ev || !ev.points || !ev.points.length) return;
      var ci = resolveTrace(ev.points[0]);
      if (ci != null) lastNotamClick = { t: Date.now(), ci: ci };
    });
    gd.on('plotly_doubleclick', function () {
      if (lastNotamClick.ci != null && Date.now() - lastNotamClick.t < 500) {
        // run after Plotly's own mapbox double-click view reset settles
        setTimeout(function () { zoomToTrace(lastNotamClick.ci); }, 0);
      }
      return false;
    });
    gd.on('plotly_legenddoubleclick', function (ev) {
      if (ev && ev.curveNumber != null) zoomToTrace(ev.curveNumber);
      return false;
    });
  }

  if (reset) {
    reset.addEventListener('click', function () {
      if (search) search.value = '';
      setVisible(null);
      Plotly.relayout(gd, {
        'mapbox.center': { lon: 54.651512, lat: 24.442970 },
        'mapbox.zoom': 9,
        'mapbox.bounds': null
      });
    });
  }
})();
"""


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
    plottitle += f" {escape(airports_str)}"
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
        autosize=True,
        mapbox={
            "style": "open-street-map",
            "center": {"lon": 54.651512, "lat": 24.442970},
            "zoom": 9,
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 30},
    )

    fig.update_layout(hoverlabel=dict(bgcolor="white", font_size=12, font_family="Rockwell"))

    fig.update_layout(legend=dict(itemdoubleclick=False))

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
                    name=_LEGEND_DIVIDER + df.loc[df.index[i], "wrap"],
                    mode="lines",
                    lon=lon,
                    lat=lat,
                    fill="toself",
                    hoverinfo="skip",
                    legendwidth=0.1,
                    line=dict(color="tomato", width=1),
                    meta=df.index[i],
                )
            )

    html = fig.to_html(
        full_html=True,
        include_plotlyjs=True,
        config={"responsive": True},
        div_id="notamplot",
    )
    html = re.sub(
        r'id="notamplot" class="plotly-graph-div" style="[^"]*"',
        'id="notamplot" class="plotly-graph-div" style="height:100vh;width:100vw;"',
        html,
    )
    html = html.replace(
        "</head>",
        "<style>html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;}"
        "#notam-search-wrap{position:fixed;top:8px;left:8px;z-index:1000;display:flex;gap:6px;font-family:sans-serif;}"
        "#notam-search{width:220px;padding:6px 8px;border:1px solid #ccc;border-radius:4px;font-size:13px;}"
        "#notam-reset{padding:6px 10px;border:1px solid #ccc;border-radius:4px;background:#fff;font-size:13px;cursor:pointer;}"
        "</style></head>",
    )
    html = html.replace("</body>", _SEARCH_UI + "<script>" + _SEARCH_JS + "</script></body>")
    with open(filepath_out, "w") as file:
        file.write(html)
    logger.info("html file created in output folder")


def handle(df, filepath_out=None, airports_str="omaa"):
    """Plot a NOTAM DataFrame and write an ``.html`` plot to ``filepath_out``.

    ``df`` is the plotting DataFrame produced by
    :func:`~notamplotter.parse.parse_faa_response` (or
    :func:`~notamplotter.parse.readnotams`).
    """
    logger.info("running handle()")
    df = add_polygons(df)
    logger.info("polygons added")
    df = add_multiple_circles(df)
    logger.info("multiple circles added")
    df = split_circles_add_indices(df)
    logger.info("circles split")
    jdata = create_jdata(df)
    logger.info("jdata created")
    back_traces(df, jdata, airports_str, filepath_out)
