"""NotamPlotter package.

Phase 2 (AGENT_PLAN.md) split the former ``notam_util.py`` god module into
this package:

* ``models``  -- typed NOTAM dataclasses
* ``config``  -- configuration (env + optional YAML/TOML)
* ``parse``   -- raw-text parsing into DataFrames
* ``plot``    -- geo/polygon logic and HTML generation
* ``cleanup`` -- file retention/deletion
* ``fetch``   -- legacy Selenium fetchers (replaced by the FAA API in Phase 3)
* ``_logging``-- centralised logging
"""

__version__ = "0.1.5"
