#!/usr/bin/env python3
"""Replace remux files with encodes for movies on Radarr's encode profiles.

Radarr never grabs or imports a lower quality than the file on disk, even when
the movie's profile no longer allows remuxes. For each movie on one of the
target profiles (default: HD Bluray + WEB, UHD Bluray + WEB) whose file is a
remux, this does an interactive search, picks the best release the profile
would accept if there were no file, grabs it, and then deletes the remux so
the download imports cleanly.

Dry run by default: it searches and reports what it would grab. Pass --apply
to grab and delete. Deleted remuxes are permanent unless Radarr's Recycle Bin
is set (Settings > Media Management > Recycle Bin).

Each movie costs one search on every indexer, so work in batches (--limit).

    RADARR_URL=https://radarr.example.com RADARR_API_KEY=... \
        python3 scripts/radarr-downsize.py --limit 10
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request

# Rejections that only exist because a (better) file is already on disk.
EXISTING_FILE_REJECTION = re.compile(r"existing file|not an upgrade|cutoff|upgrades? (are|is) not allowed", re.I)


def api(method, path, body=None):
    req = urllib.request.Request(
        os.environ["RADARR_URL"].rstrip("/") + "/api/v3" + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-Api-Key": os.environ["RADARR_API_KEY"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
    return json.loads(data) if data else None


def profile_qualities(profile):
    """Allowed quality names, highest preference first."""
    ranked = []
    for item in reversed(profile["items"]):
        if not item.get("allowed"):
            continue
        if item.get("items"):
            ranked.append({q["quality"]["name"] for q in item["items"]})
        else:
            ranked.append({item["quality"]["name"]})
    return ranked


def pick_release(releases, ranked, min_score):
    def rank(r):
        name = r["quality"]["quality"]["name"]
        return next((i for i, names in enumerate(ranked) if name in names), None)

    candidates = []
    for r in releases:
        if rank(r) is None or r.get("customFormatScore", 0) < min_score:
            continue
        if r.get("downloadAllowed") is False:
            continue
        if any(not EXISTING_FILE_REJECTION.search(msg) for msg in r.get("rejections", [])):
            continue
        candidates.append(r)
    # Radarr ranks quality first, then custom format score.
    candidates.sort(key=lambda r: (rank(r), -r.get("customFormatScore", 0)))
    return candidates[0] if candidates else None


def gb(n):
    return f"{n / 1e9:.1f} GB"


def main():
    # Show progress immediately when output is redirected to a log file.
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", action="append", help="target profile name (repeatable)")
    ap.add_argument("--limit", type=int, default=10, help="max movies to search this run (default 10)")
    ap.add_argument("--sleep", type=float, default=5, help="seconds between searches (default 5)")
    ap.add_argument("--min-savings", type=float, default=0.3,
                    help="skip unless the new release is at least this fraction smaller (default 0.3)")
    ap.add_argument("--apply", action="store_true", help="actually grab releases and delete remuxes")
    args = ap.parse_args()
    targets = args.profile or ["HD Bluray + WEB", "UHD Bluray + WEB"]

    profiles = {p["id"]: p for p in api("GET", "/qualityprofile") if p["name"] in targets}
    missing = set(targets) - {p["name"] for p in profiles.values()}
    if missing:
        sys.exit(f"profile(s) not found in Radarr: {', '.join(sorted(missing))}")

    queued = {q.get("movieId") for q in api("GET", "/queue?pageSize=10000").get("records", [])}
    movies = [
        m for m in api("GET", "/movie")
        if m["qualityProfileId"] in profiles
        and m.get("movieFile")
        and "Remux" in m["movieFile"]["quality"]["quality"]["name"]
        and m["id"] not in queued
    ]
    movies.sort(key=lambda m: -m["movieFile"]["size"])  # biggest savings first
    total = sum(m["movieFile"]["size"] for m in movies)
    print(f"{len(movies)} remuxes on {', '.join(targets)} ({gb(total)}); "
          f"processing {min(args.limit, len(movies))} {'(APPLY)' if args.apply else '(dry run)'}\n")

    saved = grabbed = 0
    for i, m in enumerate(movies[: args.limit]):
        if i:
            time.sleep(args.sleep)
        # Re-read the movie: a long run can outlive profile changes made in the
        # meantime (e.g. a movie moved back to a Remux profile to keep it).
        try:
            m = api("GET", f"/movie/{m['id']}")
        except Exception as e:
            print(f"  ERROR   {m['title']}: could not re-read movie: {e}")
            continue
        f = m.get("movieFile")
        if (m["qualityProfileId"] not in profiles or not f
                or "Remux" not in f["quality"]["quality"]["name"]):
            print(f"  GONE    {m['title']} ({m.get('year')}): profile or file changed since start, skipping")
            continue
        profile = profiles[m["qualityProfileId"]]
        label = f"{m['title']} ({m.get('year')}) [{f['quality']['quality']['name']}, {gb(f['size'])}]"
        try:
            releases = api("GET", f"/release?movieId={m['id']}")
        except Exception as e:  # indexer/network hiccup: skip this movie
            print(f"  ERROR   {label}: search failed: {e}")
            continue
        r = pick_release(releases, profile_qualities(profile), profile.get("minFormatScore", 0))
        if not r:
            print(f"  NONE    {label}: no acceptable release")
            continue
        if r["size"] > f["size"] * (1 - args.min_savings):
            print(f"  SKIP    {label}: best is {gb(r['size'])}, not enough smaller")
            continue
        print(f"  {'GRAB' if args.apply else 'WOULD'}    {label}\n"
              f"          -> {r['title']} [{r['quality']['quality']['name']}, score {r.get('customFormatScore')}, {gb(r['size'])}]")
        if args.apply:
            try:
                api("POST", "/release", {"guid": r["guid"], "indexerId": r["indexerId"]})
            except Exception as e:
                print(f"          grab failed, keeping remux: {e}")
                continue
            api("DELETE", f"/moviefile/{f['id']}")
            grabbed += 1
        saved += f["size"] - r["size"]

    verb = "grabbed" if args.apply else "would grab"
    print(f"\n{verb} {grabbed if args.apply else 'the WOULD lines above'}; ~{gb(saved)} saved once imported")


if __name__ == "__main__":
    main()
