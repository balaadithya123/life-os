# proposals/devwatch (inert)

Files here are the finished dev engine from SPEC.md.
Owner moves them into place:

- `src/devwatch.py` → repo `src/devwatch.py`
- `devwatch.yml` → `.github/workflows/devwatch.yml`
- `repos.yml` → `config/repos.yml`
- Optional: wire fixture into `tests/run_dry.sh`

## Dry-run

```bash
export DRY_RUN=1
export DEVWATCH_FIXTURE=proposals/devwatch/fixture.json
python proposals/devwatch/src/devwatch.py
# or after move: python src/devwatch.py
```

Code is untested against live GitHub (no GH_PAT in this agent run). Fixture path exercises the three report paths (failed run, bad HEAD status, old PR).

## Required secret after activation

`GH_PAT` — fine-grained PAT, read-only: Actions, Contents, Pull requests, Commit statuses. Scope to the repos listed in `repos.yml`.
