# NotamPlotter

Fetches aviation NOTAMs from the free [FAA NOTAM search API](https://notams.aim.faa.gov/notamSearch) and plots them on an interactive HTML map, ready to be emailed or served as a static file.

Works for any airport worldwide that publishes NOTAMs to the FAA system. No API key required.

## Install

Requires Python 3.13+.

```bash
pip install -e .
```

## Usage

```bash
notamplotter fetch              # save today's NOTAMs to files/*.csv
notamplotter plot <csv>         # build an interactive map: output/*.html
notamplotter daily              # fetch + plot + email in one step
notamplotter email              # email the latest HTML in output/
```

Sub-command flags:

- `daily --refetch` — force a fresh API call, ignore cached output
- `daily --recreate` — rebuild today's HTML from today's cached CSV
- `plot --output <path>` — choose the output `.html` path
- `email --html <path>` — email a specific file instead of the newest one
- `--airports EHAM,NZSP` — override the configured airports for a run

## Configuration

Defaults live in `config.yaml` (committed). Override with environment variables or a local `.env` file — see `.env.example` for the full list.

Precedence: environment variables > `config.yaml` > built-in defaults.

Key options: `airports`, `output_dir`, `files_dir`, `log_level`, and the SMTP settings (`smtp_host`, `smtp_port`, `smtp_user`, `smtp_pass`, `email_from`, `email_to`) used by `daily`/`email`.

## Development

```bash
pip install -e ".[dev]"
ruff check .
```

Tests are kept local (not committed); GitHub Actions runs lint + an import check on every push.
