# jira-reports (0001)

First runnable draft with mock Jira, admin settings, reports, CSV, and a minimal UI.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env for APP_SECRET, ADMIN_EMAIL/PASSWORD
python backend/app.py --initdb
bash backend/run.sh
# open http://localhost:8000 (login with ADMIN_EMAIL / ADMIN_PASSWORD)
```

## What works
- Login/Logout (session cookie)
- Admin settings (stored; token encrypted at rest)
- Mock sync: POST /api/sync/runs {}
- Create/list/delete reports
- Download CSVs (stints, issue stats, rollups)
- Basic chart placeholder

## Notes
- Bootstrap/Chart.js are **placeholders** to keep the app self-contained for first drop.
  We'll replace them with full local vendor files next iteration.
- Real Jira client exists but requires valid credentials.

## Git
After unzipping into your repo root:

```bash
git add .
git commit -m "0001: initial runnable draft with mock sync, reports, CSV, admin"
```

