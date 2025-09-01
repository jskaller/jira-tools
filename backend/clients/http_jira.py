from typing import Dict, Any
import httpx, os
from ..db import SessionLocal, Settings
from ..util.crypto import fernet_from_env

class HttpJiraClient:
    def __init__(self):
        db = SessionLocal()
        settings = db.query(Settings).first()
        db.close()
        self.base = (settings.jira_base_url or "").rstrip("/")
        self.email = settings.jira_email
        token = settings.jira_token_ciphertext
        self.token = None
        if token:
            f = fernet_from_env()
            try:
                self.token = f.decrypt(token.encode()).decode()
            except Exception:
                self.token = None
        self.client = httpx.AsyncClient(base_url=self.base, headers=self._headers())

    def _headers(self):
        if self.email and self.token:
            import base64
            auth = base64.b64encode(f"{self.email}:{self.token}".encode()).decode()
            return {"Authorization": f"Basic {auth}", "Accept": "application/json"}
        return {"Accept": "application/json"}

    async def search_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        params = {"jql": jql, "maxResults": max_results, "expand": "changelog"}
        r = await self.client.get("/rest/api/3/search", params=params)
        r.raise_for_status()
        return r.json()

    async def get_issue_changelog(self, issue_key: str) -> Dict[str, Any]:
        r = await self.client.get(f"/rest/api/3/issue/{issue_key}/changelog")
        r.raise_for_status()
        return r.json()

    async def me(self) -> Dict[str, Any]:
        r = await self.client.get("/rest/api/3/myself")
        r.raise_for_status()
        return r.json()
