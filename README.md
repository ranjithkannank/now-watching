# now-watching

A little banner that shows the movie I'm watching right now. After 1 hour it
flips to "last watched" and the title gets appended to this year's list.

Served free under the existing blog domain at:

    https://ranjithkannan.com/now-watching/

It is a plain static page (no Jekyll) plus two GitHub Actions: one to set the
current movie (triggered from an iPhone Shortcut), one cron job to do the
1-hour flip.

## How it works

- `index.html` reads `data.json` and renders the banner. It refetches every
  minute and runs a live countdown.
- `data.json` is the single source of truth:
  ```json
  {
    "now_watching": { "title": "Dune", "started_at": "2026-06-27T20:14:00Z" },
    "last_watched": { "title": "Sinners", "finished_at": "2026-06-27T17:00:00Z" },
    "watched": [ { "title": "Sinners", "started_at": "...", "finished_at": "..." } ]
  }
  ```
- `scripts/movie.py` is the state machine: `set "<title>"`, `tick`, `stop`.
- `.github/workflows/set.yml` runs `set` on a `repository_dispatch` event.
- `.github/workflows/flip.yml` runs `tick` every ~10 minutes on a schedule.

Starting a new movie ends the previous one. The flip is recorded at the 1-hour
mark, not whenever the cron happened to run.

## One-time setup

### 1. Create the repo and push

    cd now-watching
    git init && git add -A && git commit -m "Initial now-watching banner"
    gh repo create now-watching --public --source=. --remote=origin --push

Do **not** add a `CNAME` file. The repo inherits `ranjithkannan.com` from the
main `ranjithkannank.github.io` site and serves at `/now-watching/`.

### 2. Enable Pages

Repo Settings -> Pages -> Build and deployment -> Source: **Deploy from a
branch**, branch `main`, folder `/ (root)`. Every push (including the bot's
`data.json` commits) redeploys the page.

### 3. Create a token for the Shortcut

GitHub Settings -> Developer settings -> Fine-grained tokens -> Generate:

- Repository access: **Only select repositories** -> `now-watching`
- Permissions: **Contents -> Read and write**
- Copy the token (starts with `github_pat_`).

This token can only touch this repo, nothing else.

### 4. Build the Apple Shortcut

New Shortcut named "Now Watching":

1. **Ask for Input** -> Text -> prompt "What are you watching?"
2. **Get Contents of URL**
   - URL: `https://api.github.com/repos/ranjithkannank/now-watching/dispatches`
   - Method: **POST**
   - Headers:
     - `Authorization` = `Bearer github_pat_...`
     - `Accept` = `application/vnd.github+json`
   - Request Body: **JSON**
     - `event_type` (Text) = `set_movie`
     - `client_payload` (Dictionary) -> `title` (Text) = the **Provided Input**
       from step 1

Add it to the Home Screen. Tap it, type or dictate the title, done. Within a
few seconds the page shows it.

## Local testing

    python3 scripts/movie.py set "Dune"   # start watching
    python3 scripts/movie.py tick         # no-op until 1h has passed
    python3 scripts/movie.py stop         # end it now (manual)

    # preview the page (a local server is needed; file:// blocks fetch())
    python3 -m http.server 8000           # then open http://localhost:8000/

## Notes

- GitHub's scheduled crons can run a few minutes late under load. That only
  delays the flip slightly; nothing is lost.
- "This year" is computed in the browser from `finished_at`, so the list rolls
  over to a new year automatically on Jan 1.
