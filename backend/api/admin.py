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
    try:
        s = db.query(Settings).first()
        if not s:
            s = Settings()
            db.add(s); db.commit(); db.refresh(s)
        return {
            "jira_base_url": s.jira_base_url,
            "jira_email": s.jira_email,
            "has_token": bool(s.jira_token_ciphertext),
            "jql_default": s.jql_default,
            "time_mode": s.time_mode,
            "bh_start": s.bh_start,
            "bh_end": s.bh_end,
            "bh_days": __import__("json").loads(s.bh_days_json or "[]"),
            "max_issues": s.max_issues,
            "updated_days_limit": s.updated_days_limit,
            "agg_mode": s.agg_mode,
            "use_real_jira": s.use_real_jira,
        }
    finally:
        db.close()

@router.put("/settings")
def put_settings(payload: dict, user=Depends(require_admin)):
    print("[api/admin] PUT /settings payload:", payload)
    db = SessionLocal()
    try:
        s = db.query(Settings).first()
        if not s:
            s = Settings()
            db.add(s); db.commit(); db.refresh(s)
        # Coerce ints
        for k in ["bh_start","bh_end","max_issues","updated_days_limit"]:
            if k in payload and payload[k] is not None:
                payload[k] = int(payload[k])
        # Coerce bools
        if "use_real_jira" in payload:
            v = payload["use_real_jira"]
            if not isinstance(v, bool):
                payload["use_real_jira"] = str(v).lower() in ("1","true","yes","on")
        # Assign fields
        for k in ["jira_base_url","jira_email","jql_default","time_mode","bh_start","bh_end","max_issues","updated_days_limit","agg_mode","use_real_jira"]:
            if k in payload:
                setattr(s, k, payload[k])
        # bh_days
        if "bh_days" in payload and payload["bh_days"] is not None:
            import json as _json
            bd = payload["bh_days"]
            if isinstance(bd, str):
                bd = _json.loads(bd)
            s.bh_days_json = _json.dumps(bd)
        # token
        if "jira_token" in payload and payload["jira_token"]:
            s.jira_token_ciphertext = fernet().encrypt(payload["jira_token"].encode()).decode()
        db.commit(); db.refresh(s)
        return {
            "ok": True,
            "saved": {
                "jira_base_url": s.jira_base_url,
                "jira_email": s.jira_email,
                "has_token": bool(s.jira_token_ciphertext),
                "use_real_jira": s.use_real_jira
            }
        }
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

@router.post("/test-connection")
async def test_connection_post(payload: dict | None = None, user=Depends(require_admin)):
    print('[api/admin] POST /test-connection payload:', payload)
    from ..clients.http_jira import HttpJiraClient
    db = SessionLocal()
    s = db.query(Settings).first()
    db.close()
    # Use provided values if present; fall back to DB
    base_url = (payload or {}).get("jira_base_url") or (s.jira_base_url if s else None)
    email = (payload or {}).get("jira_email") or (s.jira_email if s else None)
    token_plain = (payload or {}).get("jira_token")
    configured = bool(base_url and email and (token_plain or (s and s.jira_token_ciphertext)))
    if not configured:
        missing = []
        if not base_url: missing.append("base URL")
        if not email: missing.append("email")
        if not (token_plain or (s and s.jira_token_ciphertext)): missing.append("token")
        return {"configured": False, "ok": False, "error": "Missing " + ", ".join(missing)}
    # Temp client that uses provided values when present
    try:
        if token_plain is not None:
            # Build a transient client by temporarily overriding settings values
            # so HttpJiraClient picks them up
            class TempClient(HttpJiraClient):
                def __init__(self):
                    # bypass DB fetch in parent; set fields directly
                    self.base = (base_url or "").rstrip("/")
                    self.email = email
                    import base64 as _b64, httpx
                    auth = _b64.b64encode(f"{self.email}:{token_plain}".encode()).decode()
                    self.client = httpx.AsyncClient(base_url=self.base, headers={"Authorization": f"Basic {auth}", "Accept":"application/json"}, timeout=httpx.Timeout(10.0, connect=5.0))
            client = TempClient()
        else:
            client = HttpJiraClient()
        me = await client.me()
        return {"configured": True, "ok": True, "account": {"displayName": me.get("displayName"), "emailAddress": me.get("emailAddress"), "accountId": me.get("accountId")}}
    except Exception as e:
        return {"configured": True, "ok": False, "error": str(e)}

@router.get("/_debug/settings")
def debug_settings(user=Depends(require_admin)):
    db = SessionLocal()
    try:
        s = db.query(Settings).first()
        if not s:
            return {"exists": False}
        return {
            "exists": True,
            "jira_base_url": s.jira_base_url,
            "jira_email": s.jira_email,
            "jira_token_len": len(s.jira_token_ciphertext or ""),
            "use_real_jira": s.use_real_jira,
        }
    finally:
        db.close()

