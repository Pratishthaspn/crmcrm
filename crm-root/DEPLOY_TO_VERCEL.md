# Deploying this CRM to Vercel

This is a Django app, and Vercel is a serverless platform, so a couple of
things had to change before it can run there:

- Added `vercel.json` — routes all requests to the Django WSGI app
  (`Django-CRM-main/src/cfehome/wsgi.py`) and serves collected static files.
- Added `build_files.sh` — installs dependencies and runs `collectstatic`
  during the Vercel build step.
- Added a root-level `requirements.txt` (Vercel's Python builder expects one
  at the project root).
- Registered the `dashboard` app in `INSTALLED_APPS` (it was referenced in
  `urls.py` but never installed — a bug in the original repo).
- Added `SECURE_PROXY_SSL_HEADER` and `CSRF_TRUSTED_ORIGINS` so login/admin
  forms work behind Vercel's proxy and HTTPS.

## Required setup before it will actually run

1. **A real database.** Vercel's filesystem is read-only/ephemeral at
   runtime, so the default SQLite file (`db.sqlite3`) will not persist —
   every cold start would look empty. Provision a free Postgres database
   (Neon, Supabase, or Vercel's own Postgres add-on all work) and set
   `DATABASE_URL` as an environment variable in the Vercel project settings.
2. **`DJANGO_SECRET_KEY`.** Generate one and add it as an env var — see
   `.env.example` for the command.
3. Push this folder to a GitHub repo and import it in Vercel, or run
   `vercel` from inside this folder with the Vercel CLI.
4. After the first deploy, run migrations against your production database
   once, from your machine, pointed at the same `DATABASE_URL`:
   ```
   cd Django-CRM-main/src
   DATABASE_URL=... python manage.py migrate
   DATABASE_URL=... python manage.py createsuperuser
   ```
   (Vercel functions are stateless/short-lived, so you can't run one-off
   management commands *on* Vercel itself — run them locally against the
   same hosted database.)

## Honest caveat

Django on Vercel works, but it's not Vercel's core use case — it's built
for Next.js/serverless functions, not long-running WSGI apps. Cold starts
are slower than on a real Python host, there's no built-in worker/queue
support if you later add background jobs (e.g. Celery), and the Python
runtime/build behavior has changed across Vercel's platform versions before.
If this CRM grows into something you're relying on, Render or Railway are
generally a smoother fit for Django and cost about the same. Since you
specifically want Vercel to keep iterating on it, this setup should get you
running — just test the actual deploy and come back if anything in Vercel's
build log doesn't match what's described here.
