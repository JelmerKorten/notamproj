"""Security regression tests (NOTAM text escaping + ICAO code validation).

Covers the Phase 4 audit fixes: NOTAM-derived text and airport codes must be
HTML-escaped before they reach the generated plot, and airport codes must be
whitelist-validated so they can never traverse paths or inject into headers.
"""

import pandas as pd
import pytest

from notamplotter.fetch import _normalize_designators
from notamplotter.parse import parse_faa_response
from notamplotter.plot import back_traces, create_jdata


def _payload(english: str, serial: str = "A0001/26 NOTAMN") -> dict:
    return {"notamList": [{"icaoMessage": f"{serial}\nE){english}\nF)SFC\nG)UNL"}]}


def test_wrap_escapes_notam_text():
    payload = _payload('RWY <img src=x onerror=alert(1)> & CLOSED')
    df = parse_faa_response(payload)
    wrap = df.loc["A0001/26 NOTAMN", "wrap"]
    assert "<img" not in wrap
    assert "&lt;img" in wrap
    assert "&amp;" in wrap


def test_wrap_escapes_serial():
    payload = _payload("X", serial="A0001/26 <b>NOTAMN</b>")
    df = parse_faa_response(payload)
    wrap = df.loc[payload["notamList"][0]["icaoMessage"].splitlines()[0], "wrap"]
    assert "<b>" not in wrap
    assert "&lt;b&gt;" in wrap


def test_normalize_designators_valid():
    assert _normalize_designators("OMAA, omae omaa") == ["OMAA", "OMAE", "OMAA"]


@pytest.mark.parametrize(
    "bad",
    [
        "OMAA/../../etc",
        "OMAA\r\nBcc:attacker@example.com",
        "<script>alert(1)</script>",
        "OMAA;rm -rf /",
        "..",
    ],
)
def test_normalize_designators_rejects_injection(bad):
    with pytest.raises(ValueError):
        _normalize_designators(bad)


def test_title_escapes_airports(tmp_path):
    df = pd.DataFrame(
        [{
            "short": "",
            "icao": "OMAA",
            "start_date": "",
            "end_date": "",
            "times": "",
            "english": "X",
            "lower": "",
            "upper": "",
            "coords": [(55.0, 25.0), (56.0, 26.0)],
            "wrap": "safe",
        }],
        index=["A0001/26 NOTAMN"],
    )
    out = tmp_path / "out.html"
    back_traces(
        df,
        create_jdata(df),
        airports_str='<img src=x onerror=alert(1)>',
        filepath_out=str(out),
    )
    html = out.read_text()
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert '\\u003cimg src=x onerror=alert(1)\\u003e' not in html
