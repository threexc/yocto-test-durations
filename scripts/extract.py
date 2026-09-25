#!/usr/bin/env python3
"""Extract per-run test durations and status counts from a yocto-testresults clone.

Usage: extract.py <yocto-testresults clone>

Walks every commit reachable from HEAD in the clone, so it works with shallow
clones: backfill once from a deep clone, then update from shallow ones. Runs
already present in site/data/ are kept; new ones are merged in by run id.
"""
import collections
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"


def summarize(run):
    cfg, res = run["configuration"], run["result"]
    sections = res.get("ptestresult.sections", {})
    return {
        "start": cfg["STARTTIME"],
        "commit": cfg.get("LAYERS", {}).get("meta", {}).get("commit"),
        "durations": {k: round(v["duration"], 3) for k, v in res.items()
                      if isinstance(v.get("duration"), (int, float))},
        "sections": {k: float(v["duration"]) for k, v in sections.items() if "duration" in v},
        "status": dict(collections.Counter(v["status"] for v in res.values() if "status" in v)),
    }


def out_path(path):
    return DATA / (path.removesuffix("/testresults.json") + ".json")


def load(path):
    f = out_path(path)
    return {r["id"]: r for r in json.loads(f.read_text())} if f.exists() else {}


def save(path, runs):
    f = out_path(path)
    f.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(runs.values(), key=lambda r: r["start"])
    # One run per line keeps git diffs of the data small and readable.
    f.write_text("[\n" + ",\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n]\n")


def main():
    repo = sys.argv[1]
    patterns = [l.strip() for l in (ROOT / "tracked.txt").read_text().splitlines()
                if l.strip() and not l.startswith("#")]

    def git(*args):
        return subprocess.run(["git", "-C", repo, *args], check=True,
                              capture_output=True, text=True).stdout

    cat = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def blob(sha):
        cat.stdin.write(sha.encode() + b"\n")
        cat.stdin.flush()
        size = int(cat.stdout.readline().split()[2])
        data = cat.stdout.read(size)
        cat.stdout.read(1)
        return data

    stores, seen = {}, set()
    for commit in git("rev-list", "HEAD").split():
        for line in git("ls-tree", "-r", commit).splitlines():
            meta, path = line.split("\t", 1)
            sha = meta.split()[2]
            if sha in seen or not any(fnmatch.fnmatch(path, p) for p in patterns):
                continue
            seen.add(sha)
            store = stores.setdefault(path, load(path))
            for run_id, run in json.loads(blob(sha)).items():
                if run_id not in store:
                    store[run_id] = {"id": run_id, **summarize(run)}

    for path, runs in stores.items():
        save(path, runs)
    index = sorted(str(f.relative_to(DATA)) for f in DATA.rglob("*.json") if f.name != "index.json")
    (DATA / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    print(f"{len(stores)} files, {sum(map(len, stores.values()))} runs")


if __name__ == "__main__":
    main()
