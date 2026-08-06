"""Phase 3 proof-of-concept tests for the FAA API migration (AGENT_PLAN.md).

Covers :class:`~notamplotter.fetch.FaaClient`, :func:`~notamplotter.parse.parse_faa_response`
and the shared block parser against a committed live fixture
(``tests/fixtures/faa_full.json``, captured from the real API), plus an
optional live smoke test against the FAA endpoint.
"""

import json
import pathlib

import pytest

from notamplotter.fetch import FaaClient
from notamplotter.parse import parse_faa_response, readnotams

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "faa_full.json"

EXPECTED_COLUMNS = ["short", "icao", "start_date", "end_date", "times", "english", "lower", "upper"]


@pytest.fixture(scope="module")
def api_payload() -> dict:
    with open(FIXTURE) as file:
        return json.load(file)


def test_fixture_is_complete(api_payload):
    assert api_payload["totalNotamCount"] == 61
    assert len(api_payload["notamList"]) == 61


def test_parse_faa_response_schema(api_payload):
    df = parse_faa_response(api_payload)
    assert df.shape == (61, 10)
    assert list(df.columns) == EXPECTED_COLUMNS + ["coords", "wrap"]


def test_parse_faa_response_fields(api_payload):
    df = parse_faa_response(api_payload)
    row = df.loc["A2204/26 NOTAMN"]
    assert row["icao"] == "OMAE"
    assert row["start_date"] == "2607010547"
    assert row["end_date"] == "2608312359"
    assert row["lower"] == "SFC"
    assert row["upper"] == "5000FT AMSL"
    assert "BOUNDED" in row["english"]


def test_parse_faa_response_no_notams():
    df = parse_faa_response({"notamList": [], "totalNotamCount": 0})
    assert df.shape == (0, 10)


def test_roundtrip_through_csv(api_payload, tmp_path):
    csv_path = tmp_path / "notams.csv"
    with open(csv_path, "w") as file:
        for notam in api_payload["notamList"]:
            file.write((notam.get("icaoMessage") or "").strip())
            file.write("\n\n")

    from_api = parse_faa_response(api_payload)
    from_csv = readnotams(str(csv_path))
    assert from_api.shape == from_csv.shape
    assert from_api[EXPECTED_COLUMNS].equals(from_csv[EXPECTED_COLUMNS])


def test_live_api_smoke():
    """Hit the real FAA endpoint; skip cleanly when offline or blocked."""
    client = FaaClient()
    try:
        notams = client.fetch_all(["OMAA"])
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"FAA API unreachable: {exc}")
    assert notams
    assert all("icaoMessage" in notam for notam in notams)
