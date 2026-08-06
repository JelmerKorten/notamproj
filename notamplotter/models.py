"""Typed dataclasses for NOTAM entries.

Phase 2 (AGENT_PLAN.md) replaces the dict-based NOTAM handling with typed
objects. The parsers (:mod:`notamplotter.parse`) build :class:`Notam`
instances which are then converted into the DataFrame schema consumed by the
plotting pipeline (:mod:`notamplotter.plot`).
"""

from dataclasses import dataclass, field

# Fields stored per NOTAM, mirroring the legacy DataFrame columns produced by
# readnotams()/readgcaacsv(). ``serial`` is the row index.
NOTAM_FIELDS = (
    "short",
    "icao",
    "start_date",
    "end_date",
    "times",
    "english",
    "lower",
    "upper",
)


@dataclass
class Notam:
    """A single parsed NOTAM entry.

    ``serial`` is the identifier line (e.g. ``A1718/25     NOTAMN``) used as
    the DataFrame row index. Field *presence* is tracked so a field that was
    explicitly present-but-empty in the source is preserved (rendered as an
    empty string), while an absent field is rendered as ``NaN`` -- matching the
    legacy dict-based behaviour exactly.
    """

    serial: str
    short: str = ""
    icao: str = ""
    start_date: str = ""
    end_date: str = ""
    times: str = ""
    english: str = ""
    lower: str = ""
    upper: str = ""

    _present: set[str] = field(default_factory=set, init=False, repr=False, compare=False)

    @classmethod
    def from_dict(cls, serial: str, data: dict[str, str]) -> "Notam":
        """Build a Notam from a dict, tracking which fields were present."""
        notam = cls(serial=serial)
        for name in NOTAM_FIELDS:
            if name in data:
                setattr(notam, name, data[name])
                notam._present.add(name)
        return notam

    def to_dict(self) -> dict[str, str]:
        """Return the fields that were present, preserving empty strings."""
        return {name: getattr(self, name) for name in NOTAM_FIELDS if name in self._present}
