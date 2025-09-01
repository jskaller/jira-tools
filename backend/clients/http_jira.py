from typing import Dict, Any
import httpx, os
from ..db import SessionLocal, Settings
from ..util.crypto import fernet_from_env

class HttpJiraClient:
    def __init__(self):
        db = SessionLocal()
        settings = db.query(Settings).first()
        db.close()
        self.base = (settings.jira_base_url or "").strip().rstrip("/")
        self.email = (settings.jira_email or "").strip()
        token_ct = settings.jira_token_ciphertext
        self.token = None
        if token_ct:
            try:
                t = fernet_from_env().decrypt(token_ct.encode()).decode()
                self.token = t.strip()
                print("[http_jira] token decrypt: ok (len=%d)" % len(self.token))
            except Exception as e:
                print("[http_jira] token decrypt FAILED:", repr(e))
                self.token = None
        self.client = httpx.AsyncClient(base_url=self.base, headers=self._headers(), timeout=httpx.Timeout(10.0, connect=5.0))

    def _headers(self):
        if self.email and self.token:
            import base64
            raw = f"{self.email}:{self.token}".encode()
            auth = base64.b64encode(raw).decode()
            return {"Authorization": f"Basic {auth}", "Accept": "application/json"}
        return {"Accept": "application/json"}

    async def me(self):
        # Jira: GET /rest/api/3/myself
        resp = await self.client.get("/rest/api/3/myself")
        resp.raise_for_status()
        return resp.json()

    async def aclose(self):
        try:
            await self.client.aclose()
        except Exception:
            pass

    def _headers(self):
        if self.email and self.token:
            import base64
            raw = f"{self.email}:{self.token}".encode()
            auth = base64.b64encode(raw).decode()
            return {"Authorization": f"Basic {auth}", "Accept": "application/json"}
        return {"Accept": "application/json"}
