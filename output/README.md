Potentially you can run to generate standard file:

```bash
.venv/bin/python -m notamplotter.cli daily              # use cache/skip if today exists
.venv/bin/python -m notamplotter.cli daily --refetch   # fresh from API
.venv/bin/python -m notamplotter.cli daily --recreate  # rebuild from today's csv
```
