# intercom-helpscout-migrator

One-way article migrator that moves your **Intercom** help center into
**Help Scout Docs** — including inline images.

A small Flask web app: you sign in with Intercom OAuth, paste a Help Scout
Docs API key, and it walks every Intercom article, converts the HTML,
re-uploads all embedded images to Help Scout's asset store (so nothing
hotlinks back to Intercom), and streams progress to the page as it goes.

## What it does

1. **Intercom OAuth login** — no article collection without it.
2. **Fetches every article** from the Intercon Articles API, preserving HTML.
3. **Re-hosts inline images** — each `<img>` is downloaded from Intercom and
   re-uploaded to the Help Scout Docs asset API, then the HTML is rewritten
   to the new URL.
4. **Creates the article in Help Scout** via the Docs API and prints a live
   progress log (`🖼️ Migrated image …` / `⚠️ Failed image …`).

## Running it

```sh
pip install -r requirements.txt

export INTERCOM_CLIENT_ID=...
export INTERCOM_CLIENT_SECRET=...
export INTERCOM_REDIRECT_URI=https://your-host/oauth/callback
export FLASK_SECRET=change-me

python app.py
```

Deployable as-is to Render / Heroku (`Procfile` + `runtime.txt` included).

## Notes

- The Help Scout Docs API key is requested in the UI; the Intercom token
  comes from the OAuth dance.
- Image re-uploads are best-effort — failures are logged and skipped so one
  broken asset never halts a whole migration.
- Written as a one-shot migration tool, not a long-running service.

## License

MIT
