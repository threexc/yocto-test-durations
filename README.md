# test-track

Test result tracker for https://git.yoctoproject.org/yocto-testresults/

## Dashboard

`site/` is a static page charting test durations and result counts over time.
`site/data/` holds per-run summaries extracted from yocto-testresults by
`scripts/extract.py`; `tracked.txt` lists which `testresults.json` files to track.

`.github/workflows/update.yml` runs every 6 hours: it shallow-clones
yocto-testresults (default depth 10, ~80MB; the server does not support partial
clones), merges any new runs into `site/data/`, commits them, and publishes
`site/` to the `pages` branch.

To track more results, add patterns to `tracked.txt` and backfill history from
a full local clone (a full clone is ~7GB, so this is not done in CI):

    git clone https://git.yoctoproject.org/yocto-testresults/
    python3 scripts/extract.py yocto-testresults
    python3 -m http.server -d site   # preview at http://localhost:8000
