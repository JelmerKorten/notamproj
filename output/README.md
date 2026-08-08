Potentially you can run to generate standard file:

```bash
.venv/bin/python -m notamplotter.cli daily              # use cache/skip if today exists
.venv/bin/python -m notamplotter.cli daily --refetch   # fresh from API
.venv/bin/python -m notamplotter.cli daily --recreate  # rebuild from today's csv

.venv/bin/python -m notamplotter.cli daily --refetch # force a fresh API call, ignore cached output
.venv/bin/python -m notamplotter.cli daily --recreate # rebuild today's HTML from today's cached CSV
.venv/bin/python -m notamplotter.cli plot --output <path> # choose the output `.html` path
.venv/bin/python -m notamplotter.cli email --html <path> # email a specific file instead of the newest one
.venv/bin/python -m notamplotter.cli --airports EHAM,NZSP # override the configured airports for a run
```
