import os, json
from fastapi import APIRouter, Depends, HTTPException
from ..db import SessionLocal, Settings
from ..security import require_admin
from cryptography.fernet import Fernet

router = APIRouter()

def fernet():
    key = os.getenv("APP_SECRET", "dev-secret").encode().ljust(32, b'0')[:32]
    return Fernet(key)

@router.get("/settings")
def get_settings(user=Depends(require_admin)):
    db = SessionLocal()
    s = db.query(Settings).first()
    db.close()
    if not s:
        raise HTTPException(500, "settings missing")
    return {
        "jira_base_url": s.jira_base_url,
        "jira_email": s.jira_email,
        "has_token": bool(s.jira_token_ciphertext),
        "jql_default": s.jql_default,
        "time_mode": s.time_mode,
        "bh_start": s.bh_start,
        "bh_end": s.bh_end,
        "bh_days": json.loads(s.bh_days_json or "[]"),
        "max_issues": s.max_issues,
        "updated_days_limit": s.updated_days_limit,
        "agg_mode": s.agg_mode,
        "use_real_jira": s.use_real_jira,
    }

@router.put("/settings")
def put_settings(payload: dict, user=Depends(require_admin)):
    db = SessionLocal()
    s = db.query(Settings).first()
    for k in ["jira_base_url","jira_email","jql_default","time_mode","bh_start","bh_end","max_issues","updated_days_limit","agg_mode","use_real_jira"]:
        if k in payload:
            setattr(s, k, payload[k])
    if "bh_days" in payload:
        s.bh_days_json = json.dumps(payload["bh_days"])
    if "jira_token" in payload and payload["jira_token"]:
        s.jira_token_ciphertext = fernet().encrypt(payload["jira_token"].encode()).decode()
    db.commit()
    db.close()
    return {"ok": True}

@router.get("/test-connection")
async def test_connection(user=Depends(require_admin)):
    db = SessionLocal()
    s = db.query(Settings).first()
    db.close()
    return {"configured": bool(s.jira_email and s.jira_token_ciphertext and s.jira_base_url)}
