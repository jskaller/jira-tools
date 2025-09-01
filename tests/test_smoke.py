import os, json
from backend.db import init_db, SessionLocal, User, Settings
from backend.security import verify_password

def test_bootstrap_db(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLITE_PATH', str(tmp_path/'db.sqlite3'))
    init_db(force=True)
    db = SessionLocal()
    u = db.query(User).first()
    assert u and u.email
    s = db.query(Settings).first()
    assert s and s.time_mode in ('business','24x7')
    db.close()
