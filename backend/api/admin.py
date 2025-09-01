import os, json
from fastapi import APIRouter, Depends, HTTPException
from ..db import SessionLocal, Settings
from ..security import require_admin
from ..util.crypto import fernet_from_env

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
    print("[api/admin] PUT /settings payload:", payload)
    db = SessionLocal()
    try:
        s = db.query(Settings).first()
        if not s:
            s = Settings()
            db.add(s)
            db.commit()
            db.refresh(s)
        # Coerce types carefully
        int_fields = ["bh_start","bh_end","max_issues","updated_days_limit"]
        for k in int_fields:
            if k in payload and payload[k] is not None:
                try:
                    payload[k] = int(payload[k])
                except Exception:
                    return {"ok": False, "error": f"Invalid integer for {k}"}
        bool_fields = ["use_real_jira"]
        for k in bool_fields:
            if k in payload and not isinstance(payload[k], bool):
                v = str(payload[k]).lower()
                payload[k] = v in ("1","true","yes","on")
        for k in ["jira_base_url","jira_email","jql_default","time_mode","bh_start","bh_end","max_issues","updated_days_limit","agg_mode","use_real_jira"]:
            if k in payload:
                setattr(s, k, payload[k])
        if "bh_days" in payload and payload["bh_days"] is not None:
            import json as _json
            try:
                # accept list or stringified list
                bh_days_val = payload["bh_days"]
                if isinstance(bh_days_val, str):
                    bh_days_val = _json.loads(bh_days_val)
                s.bh_days_json = _json.dumps(bh_days_val)
            except Exception as e:
                return {"ok": False, "error": f"Invalid bh_days: {e}"}
        if "jira_token" in payload and payload["jira_token"]:
            s.jira_token_ciphertext = fernet().encrypt(payload["jira_token"].encode()).decode()
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        print("[api/admin] PUT /settings error:", repr(e))
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@router.get("/test-connection")
async def test_connection(user=Depends(require_admin)):
    print('[api/admin] /test-connection called')
    from ..clients.http_jira import HttpJiraClient
    db = SessionLocal()
    s = db.query(Settings).first()
    db.close()
    configured = bool(s and s.jira_email and s.jira_token_ciphertext and s.jira_base_url)
    if not configured:
        return {"configured": False, "ok": False, "error": "Missing base URL, email, or token."}
    if not (s.jira_base_url.startswith("https://") and ".atlassian.net" in s.jira_base_url):
        return {"configured": True, "ok": False, "error": "Base URL should be like https://<org>.atlassian.net"}
    try:
        client = HttpJiraClient()
        me = await client.me()
        return {"configured": True, "ok": True, "account": {"displayName": me.get("displayName"), "emailAddress": me.get("emailAddress"), "accountId": me.get("accountId")}}
    except Exception as e:
        return {"configured": True, "ok": False, "error": str(e)}
