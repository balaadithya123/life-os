#!/bin/sh
# Proposal-only fixture smoke test; append its steps to tests/run_dry.sh after review.
set -eu
cd "$(dirname "$0")/../../.."
export DRY_RUN=1
export DEVWATCH_REPOS="proposals/devwatch/repos.yml"
export DEVWATCH_FIXTURE="proposals/devwatch/fixtures/github_responses.json"
python proposals/devwatch/src/devwatch.py
python - <<'PY'
import json
from pathlib import Path
data=json.loads(Path("state/dev.json").read_text())
assert data["repos_checked"] == 1
assert data["problem_count"] == 1
assert any("failed workflow runs" in i for i in data["reports"][0]["issues"])
print("DevWatch fixture smoke test passed")
PY
