# Deprecated / Archived Files

This directory preserves legacy NotamPlotter code for reference.  Nothing
here is imported by the active codebase — it is archived because the
Selenium-based scraping and chromedriver management are being phased out in
favour of the FAA's `requests`-based API (see `AGENT_PLAN.md`).

Do not import from this directory.  Its contents are excluded from linting
(`deprecated/` is ignored by ruff).

| File | What it was | Why it was archived |
|------|-------------|---------------------|
| `gcaadf.py` | Standalone copy of `notam_util.readgcaacsv()` for parsing GCAA CSVs | Full duplicate of a function that lives in `notam_util.py` |
| `dealwithchrome.py` | ChromeDriver version checker + auto-downloader | Superseded: chromedriver auto-management is obsolete once the Selenium scraper is replaced by the FAA API (Phase 3) |
| `edgecasetest.py` | One-off script that dumped a GCAA PDF's text to `files/test.csv` | Debug/throwaway script |
| `tester.py` | Manual test harness calling `notam_util.alternative()` | Debug/throwaway script |
| `__version__.py` | Package metadata (`__version__`, author info) **and** all chromedriver download/update logic | Version metadata moved to `pyproject.toml` (single source of truth); the chrome logic is obsolete post-API-migration |
| `setup.py` | cx_Freeze build config (`python setup.py build` -> Windows binary) | cx_Freeze builds obsolete; project now builds via `pyproject.toml` |
| `support/` | Downloaded ChromeDriver binaries (untracked, ~18 MB) | Chromedriver no longer needed once Selenium is removed (Phase 3). Kept on disk only — not committed to git |
| `chromeversions.json` | Cached chromedriver version map from googlechromelabs | Obsolete: no longer used now that chromedriver management is archived |

## Notes

- `tester.py` originally imported `notam_util`; it will not run from this
  directory and is kept purely as a record of the old manual test flow.
- The Selenium/`dealwithchrome` helper chain that used to live at the top of
  `notam_util.py` was deleted in Phase 1; `deprecated/__version__.py` and
  `deprecated/dealwithchrome.py` are the authoritative copies of that logic.
