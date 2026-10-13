# scripts

## radarr-downsize.py

Replaces remux files with smaller encodes for movies on Radarr's encode
profiles (`HD Bluray + WEB`, `UHD Bluray + WEB`, both managed by Configarr).

Radarr never does this on its own: it won't grab a lower quality than the file
on disk, and it rejects the import ("Not an upgrade for existing movie file")
even after a manual grab. For each remux on a target profile, the script runs an
interactive search, picks the best release the profile would accept if there
were no file (allowed quality, at least the profile's minimum custom format
score, so the language rules still apply), grabs it, and then deletes the remux
so the download imports cleanly. If the grab fails, the remux is kept.

Movies are processed largest file first. A movie is skipped when no acceptable
release exists, when the best one isn't at least `--min-savings` (default 30%)
smaller, or when it already has something in the download queue.

### Requirements

- Python 3 (standard library only)
- `kubectl` access to the cluster, to read the Radarr API key from the
  `configarr` secret (or supply the key some other way)
- The movies you want shrunk assigned to `HD Bluray + WEB` or `UHD Bluray + WEB`
  in Radarr (Movie Editor, or Kometa's `quality_profile` with `upgrade_existing`)

### Usage

The API key is read from the environment and never written to disk:

```bash
export RADARR_URL=https://radarr.frost.haus
export RADARR_API_KEY=$(kubectl -n configarr get secret configarr -o jsonpath='{.data.RADARR_API_KEY}' | base64 -d)
```

Dry run (searches and reports what it would grab; changes nothing):

```bash
python3 scripts/radarr-downsize.py --limit 25
```

Apply (grabs the encodes and deletes the remuxes):

```bash
python3 scripts/radarr-downsize.py --limit 25 --apply
```

| Option | Default | Meaning |
|---|---|---|
| `--limit N` | 10 | Movies to search this run |
| `--sleep S` | 5 | Seconds between searches |
| `--min-savings F` | 0.3 | Skip unless the new release is at least this fraction smaller |
| `--profile NAME` | both encode profiles | Target profile name; repeat for several |
| `--apply` | off | Actually grab and delete |

Output lines: `WOULD`/`GRAB` (swap planned/done), `SKIP` (not enough smaller), `GONE` (profile
or file changed since the run started; skipped),
`NONE` (no acceptable release), `ERROR` (search failed; retried next run).

### Cautions

- **Deleted remuxes are permanent** unless Radarr's Recycle Bin is set
  (Settings > Media Management > Recycle Bin). If you set one, it needs room
  for a whole batch until it is emptied (`recycleBinCleanupDays`).
- **Indexer API limits:** each movie costs one search on every indexer. Run
  small batches (e.g. `--limit 25` a few times a day) rather than everything
  at once.
- Until the new download imports, the movie has no file in Plex. If a download
  fails, Radarr (with the movie monitored) searches for a replacement within
  the same profile.
- Movies still on `Any Quality` are ignored; move them to an encode profile first.

## seal-release-notify-webhook.sh

Seals the Slack webhook URL for Configarr's `release-notify` CronJob into a
SealedSecret:

```bash
./scripts/seal-release-notify-webhook.sh https://hooks.slack.com/services/...
```
