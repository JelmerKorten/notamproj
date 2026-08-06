# NotamPlotter Refactor Plan

## Overview

Refactor legacy NOTAM plotter: replace Selenium with `requests`-based FAA API, restructure monolith into modules, add config/email/CI support, and deprecate old code safely.

---

## Security Rules (MANDATORY)

- **ZERO secrets in code.** No API keys, passwords, SMTP creds, or tokens in source files.
- **Use environment variables exclusively** for secrets. Reference via `os.environ.get("VAR_NAME")`.
- **Never `print()` or log secrets.** Sanitise before logging.
- **`.env` files are local-only.** Add to `.gitignore`. Never commit.
- **Logs must not contain:** passwords, tokens, file paths with usernames, full email bodies.
- **Use `python-dotenv` for local dev** to load `.env`.
- **In CI (GitHub Actions), use repository secrets** mapped to env vars in the workflow file.
- **Pin all dependencies** (exact versions) in `pyproject.toml` to avoid supply-chain surprises.

---

## Branch Strategy

Every phase gets its own branch. Merge to `master` only after review.

| Branch | Purpose |
|--------|---------|
| `master` | Production-ready. Protected. |
| `refactor/01-cleanup-deprecate` | Phase 1 – cleanup & deprecation |
| `refactor/02-config-structure` | Phase 2 – config & module split |
| `refactor/03-api-migration` | Phase 3 – Selenium → requests |
| `refactor/04-email-automation` | Phase 4 – daily schedule + email |
| `refactor/05-ci-tests` | Phase 5 – CI/CD & tests |

Work one branch at a time. No merging without review.

---

## Phase 1 — Cleanup & Deprecation

**Goal:** Remove dead code / consolidate logging / archive unused files.

### Tasks

1. **Create `deprecated/` directory** at project root with its own `README.md` explaining what each file was.
2. **Move these files to `deprecated/`:**
   - `gcaadf.py` — duplicate of `notam_util.readgcaacsv()`
   - `dealwithchrome.py` — Selenium chrome driver updater (superseded by API)
   - `edgecasetest.py` — one-off PDF parsing test
   - `tester.py` — manual Selenium fetch test
   - `__version__.py` — version + chrome driver logic (move info to `pyproject.toml`; move chrome logic to deprecated)
3. **Consolidate logging** into a single module (`notamplotter/_logging.py`). Remove duplicate `logging.basicConfig()` calls from each file.
4. **Remove commented-out Selenium code blocks** scattered through `notam_util.py` (the 30+ lines of `XPATH = ...` comments).
5. **Strip unused imports** from all files (`zipfile`, `io`, `json`, `darkdetect`, `cx_Freeze`, etc.).
6. **Remove `setup.py`** (cx_Freeze). Move build config to `pyproject.toml` if still needed.

### Verification

- `python -c "import notam_util; print('OK')"` succeeds
- `ruff check .` passes (no undefined names)
- Logs only from single `_logging.py` source

---

## Phase 2 — Config & Module Split

**Goal:** Eliminate god module (`notam_util.py` at 1268 lines). Add configuration.

### Tasks

1. **Create `notamplotter/` package** with `__init__.py`.
2. **Split `notam_util.py` into:**
   - `notamplotter/config.py` — loads env vars + optional YAML/TOML config file. Provides `Config` dataclass.
   - `notamplotter/parse.py` — `readnotams()`, `readgcaacsv()`, coordinate conversion (`convert_coords`, `create_circle`)
   - `notamplotter/plot.py` — `back_traces()`, `create_jdata()`, all geo/polygon logic
   - `notamplotter/cleanup.py` — `cleanup()` (file retention/deletion)
3. **Create `notamplotter/models.py`** with typed dataclasses for NOTAM entries instead of dicts.
4. **Create `config.yaml`** (optional, with `.env` override) for:
   - Default airport list
   - Output paths
   - Email settings (SMTP host/port/from)
   - Cleanup retention days
5. **Update `notamplotter.py`** to use new package imports.
6. **Update `notamui.py`** to use new package imports.

### Verification

- `from notamplotter.config import Config` works
- `from notamplotter.fetch import fetch_notams` works
- All routes still produce valid `.html` output

---

## Phase 3 — API Migration (Core)

**Goal:** Replace Selenium scraper with `requests`-based FAA API.

> **Note (from Phase 1):** pre-plan API work is preserved in a `git stash`
> (`stash@{0}`, from the `queries` branch). It contains `test_requests.py`
> (the `requests`-based API proof-of-concept referenced in the verification
> below) and the `wait_for_download()` Selenium helper. Restore it at the
> start of Phase 3 with `git stash pop` (or `git stash apply stash@{0}`), then
> move `test_requests.py` into the test suite.

### Tasks

1. **Create `notamplotter/fetch.py`** with FAA API client.
2. **Implement `FaaClient` class:**
   - Session with retry adapter (`tenacity` or `urllib3.Retry`), 3 retries, 5s timeout
   - `get_cookies()` → `GET https://notams.aim.faa.gov/notamSearch/`
   - `search(designators: list[str])` → `POST /notamSearch/search` with JSON payload:
     ```python
     {
         "searchType": "0",
         "designatorsForLocation": "KJFK,KLAX",
         "offset": "0",
         "notamsOnly": "false",
     }
     ```
   - Returns parsed JSON (`notamList`, `totalNotamCount`)
3. **Implement `parse_faa_response(data: dict) -> pd.DataFrame`** to convert API JSON to the same DataFrame schema that `readnotams()` produces.
4. **Create `notamplotter/fetch_gcaa.py`** for PDF fallback (keep Selenium only here if GCAA still needed).
5. **Update `collect()` signature:** accept `FaaClient` instance.
6. **Remove Selenium import paths** from everywhere. Move Selenium deps out of runtime deps in `pyproject.toml`.
7. **Move `wait_for_download()`** to `deprecated/` if GCAA fallback is kept.

### Verification

- Proof of API test file (`test_requests.py`) passes
- Full `collect()` → `handle()` pipeline produces valid `.html`
- Runs on GitHub Actions Linux runner **without Chrome**

---

## Phase 4 — Daily Automation + Email

**Goal:** Scheduled daily runs + email delivery of HTML.

### Tasks

1. **Create `notamplotter/cli.py`** with `click` or `argparse` commands:
   - `daily` — fetch today's NOTAMs, generate HTML, email it
   - `fetch` — fetch NOTAMs and save CSV (no HTML, no email)
   - `plot` — generate HTML from existing CSV
   - `email` — send last HTML via email
2. **Create `notamplotter/emailer.py`:**
   - Load SMTP config from env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`, `EMAIL_TO`)
   - Attach the `.html` file or embed as inline
   - Handle TLS vs SSL ports (587 vs 465)
   - Timeout, error handling, logging without leaking credentials
3. **Create `notamplotter/scheduler.py`:**
   - `schedule_daily(time="06:00", airports=["OMAA","OMAE"])`
   - Uses `schedule` library or APScheduler
   - Can run as long-lived process or be triggered by cron

### Security (Email)

```python
import os, smtplib
from email.message import EmailMessage
from dataclasses import dataclass

@dataclass
class EmailConfig:
    host: str = os.environ["SMTP_HOST"]
    port: int = int(os.environ.get("SMTP_PORT", "587"))
    user: str = os.environ["SMTP_USER"]
    password: str = os.environ["SMTP_PASS"]  # NEVER LOG THIS
    from_addr: str = os.environ["EMAIL_FROM"]
    to_addr: str = os.environ["EMAIL_TO"]
```

### GitHub Actions Daily Cron

```yaml
# .github/workflows/daily_notam.yml
name: Daily NOTAM
on:
  schedule:
    - cron: "0 6 * * *"  # 06:00 UTC daily
  workflow_dispatch:       # manual trigger

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - run: pip install -e .
      - run: notamplotter daily
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASS: ${{ secrets.SMTP_PASS }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
```

### Verification

- `notamplotter daily` produces HTML **and** sends email (check inbox)
- `notamplotter fetch --airports KJFK,KLAX` fetches and saves CSV
- `notamplotter email` sends existing HTML
- GitHub Actions run succeeds end-to-end

---

## Phase 5 — CI/CD & Tests

**Goal:** Reliable test suite, automated linting, artifact upload.

### Tasks

1. **Create `tests/` directory** with:
   - `test_parse.py` — test `readnotams()` with a known fixture CSV (committed to `tests/fixtures/`)
   - `test_plot.py` — test `back_traces()` produces valid HTML string
   - `test_fetch.py` — mock FAA API responses (no real network)
2. **Use `pytest`** with `pytest-cov`.
3. **Update `.github/workflows/test.yml`:**
   ```yaml
   name: Test & Lint
   on: [push, pull_request]
   jobs:
     quality:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with: { python-version: "3.13" }
         - run: pip install -e ".[dev]"
         - run: ruff check .
         - run: ruff format --check .
         - run: pytest --cov=notamplotter --cov-report=xml
         - uses: codecov/codecov-action@v4
   ```
4. **Create `pre-commit` config** (`ruff` + `trailing-whitespace` + `end-of-file-fixer`).
5. **Update `pyproject.toml`** with:
   ```toml
   [project.optional-dependencies]
   dev = ["pytest>=8", "ruff>=0.6", "pytest-cov>=5", "pre-commit>=3"]

   [tool.ruff]
   line-length = 120
   target-version = "py313"
   ```

### Verification

- `pytest` passes with >80% coverage
- `ruff check` passes (zero warnings)
- GitHub Actions shows green check on every push
- `pre-commit` runs on `git commit`

---

## Files to Archive to `deprecated/`

| File | Reason |
|------|--------|
| `gcaadf.py` | Full duplicate of `notam_util.readgcaacsv()` |
| `dealwithchrome.py` | ChromeDriver updater — obsolete post-API migration |
| `edgecasetest.py` | One-off debug script |
| `tester.py` | Manual Selenium test script |
| `__version__.py` | Version metadata + Chrome driver logic — extract version only to `pyproject.toml` |
| `setup.py` | cx_Freeze build — obsolete if moving to `pyproject.toml` |
| `support/` dir | ChromeDriver binaries — obsolete post-API migration |
| `chromeversions.json` | ChromeDriver version map — obsolete |

Add a `deprecated/README.md` explaining each file's origin and why it was archived.

---

## Files to Keep Updating

| File | Fate |
|------|------|
| `notamplotter.py` | Become thin CLI entry point |
| `notam_util.py` | Split into `notamplotter/` package, then archived to deprecated |
| `notamui.py` | Keep as alternative GUI entry (update imports) |
| `requirements.txt` | Keep for pip users, auto-generated from `pyproject.toml` |
| `pyproject.toml` | Become single source of truth for deps/version/build |
| `.github/workflows/test.yml` | Rewritten for Ubuntu + pytest + lint |
| `README.md` | Update with new instructions |

---

## Environment Variables Reference

```bash
# === FAA API (no keys needed, but configurable) ===
FAA_API_BASE_URL=https://notams.aim.faa.gov/notamSearch

# === Email (SMTP) ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASS=app-password-here   # Never commit this
EMAIL_FROM=your@email.com
EMAIL_TO=recipient@email.com

# === App Config ===
NOTAM_AIRPORTS=OMAA,OMAE,OMAD,OMAM
NOTAM_OUTPUT_DIR=./output
NOTAM_FILES_DIR=./files
NOTAM_CLEANUP_DAYS=5
NOTAM_LOG_LEVEL=INFO

# === GCAA Fallback (if kept) ===
GCAA_USERNAME=   # if auth required
GCAA_PASSWORD=   # Never commit this
```

Load with:
```python
# notamplotter/config.py
from dotenv import load_dotenv
load_dotenv()  # loads .env for local dev only
```

---

## Execution Order

```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5
(cleanup)    (structure)  (API)       (email)     (CI/tests)
```

Each phase is a separate PR branch. Merge only when:
- [ ] Tests pass
- [ ] Ruff passes
- [ ] Manual `.html` generation verified
- [ ] Logs checked for secrets

---

## Rollback

If a phase breaks production:
```bash
git checkout master
git branch -D refactor/XX-failing-phase
# Fix on a new branch
```

The `deprecated/` archive preserves the old code for reference without polluting the active codebase.
