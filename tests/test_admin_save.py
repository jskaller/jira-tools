import os, json
from backend.db import init_db, SessionLocal, Settings

def test_admin_save_persists(tmp_path, monkeypatch):
    monkeypatch.setenv('SQLITE_PATH', str(tmp_path/'db.sqlite3'))
    init_db(force=True)
    db = SessionLocal()
    s = db.query(Settings).first()
    assert s is not None
    s.jira_base_url = 'https://example.atlassian.net'
    s.jira_email = 'user@example.com'
    s.jira_token_ciphertext = 'cipher'
    db.commit()
    db.close()

    # reopen and verify
    db2 = SessionLocal()
    s2 = db2.query(Settings).first()
    assert s2.jira_base_url == 'https://example.atlassian.net'
    assert s2.jira_email == 'user@example.com'
    assert s2.jira_token_ciphertext == 'cipher'
    db2.close()
