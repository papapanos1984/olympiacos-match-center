# Olympiacos Match Center

Mobile-friendly, no-login static website intended for **GitHub Pages**.

## Deploy to a public URL

1. Create a new **public** GitHub repository, e.g. `olympiacos-match-center`.
2. Upload **all files and folders** from this project to the repository root, including `.github/workflows/update.yml` (the `.github` folder may be hidden in file managers).
3. In repository **Settings → Pages**, choose **Source: GitHub Actions**.
4. Open **Actions → Refresh fixtures and deploy → Run workflow** (or push to `main`).
5. When the deployment succeeds, the URL will usually be `https://YOUR-GITHUB-USERNAME.github.io/olympiacos-match-center/`.
6. In **Settings → Actions → General**, ensure workflow permissions allow write access if the scheduled feed cannot commit data. GitHub Pages deployments also require Pages permissions.

## Data coverage and limitations

- ESPN's unofficial/public football team schedule endpoint is queried for Greek Super League and major UEFA competitions. Endpoint or team ID changes may prevent retrieval.
- EuroLeague's public API is queried for the 2026–27 season. Its response schema may change. These feeds have not been verified end-to-end from this build environment.
- **Greek Cup football, Greek domestic basketball and Greek basketball cup are not yet connected to verified automatic feeds.** The site does not claim full coverage until those are added.
- **TV channels are not automatically discovered.** A broadcaster is shown only if explicitly verified in `data/tv-overrides.json`. Otherwise the UI says “Not yet confirmed”. This avoids inventing channel assignments. A licensed TV listings API could automate that field.
- Scheduled GitHub Actions can be delayed or suspended by GitHub. Users can also click Refresh; this reloads the latest published JSON, not the upstream APIs directly.
- All event timestamps are expected to contain an explicit timezone offset. Greece/Slovakia display uses IANA timezone data and handles DST.

## Add a confirmed TV broadcaster

Edit `data/tv-overrides.json`:

```json
{
  "matches": {
    "2026-12-10|basketball|olympiacos|example opponent": {
      "channel": "Novasports Prime",
      "verified": true
    }
  }
}
```

This is **only a format example**, not a real match or broadcaster announcement. The key must match the feed's exact lowercased home/away names and date in UTC. Trigger the workflow again after editing.

## Test locally

From the project directory run `python -m http.server 8000` and visit `http://localhost:8000`. To test the feed, run `python scripts/update.py` with internet access. It retains previously collected future matches during transient feed failures.

## Files

- `index.html`, `styles.css`, `app.js`: responsive website
- `data/fixtures.json`: published data snapshot
- `data/tv-overrides.json`: manually verified TV channel assignments
- `scripts/update.py`: best-effort upstream feed aggregation
- `.github/workflows/update.yml`: 6-hour refresh and GitHub Pages deployment

This is an unofficial fan site, not affiliated with Olympiacos or broadcasters.
