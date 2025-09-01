# jira-reports (0002 hotfix)

Complete package with fixes:
- Add `backend/__init__.py`
- Pin `itsdangerous==2.2.0`
- Fix `backend/db.py` inner `import os` shadowing
- Update Makefile/README to use `python -m backend.app --initdb`
- Requires Python 3.12

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m backend.app --initdb
bash backend/run.sh
```

## Git
```bash
git add .
git commit -m "0002: hotfix - itsdangerous pin, backend package init, db import fix"
```

Real Jira Test: configure Admin (URL, email, token), then click Test connection to call /myself.
