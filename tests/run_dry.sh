#!/bin/sh
# Offline smoke test: nothing is sent, nothing leaves your machine.
# WARNING: wipes state/ (your learned data). Run it only before going live.
set -e
cd "$(dirname "$0")/.."
export DRY_RUN=1
rm -f state/*.json state/*.jsonl state/*.md
mkdir -p inbox && cp tests/inbox_sample.json inbox/zz_test1.json && cp tests/inbox_complete.json inbox/zz_test2.json
python src/radar.py --fixture tests/feed.xml
python src/bot.py --fixture tests/updates.json
python src/learn.py
python src/brief.py
python src/selfcheck.py || true
rm -f inbox/done/zz_test*.json inbox/zz_test*.json
echo "=== snapshot ==="; cat state/hub_snapshot.md
