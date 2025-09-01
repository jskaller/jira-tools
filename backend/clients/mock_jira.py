import datetime as dt
from typing import Dict, Any

class MockJiraClient:
    def __init__(self):
        self._now = dt.datetime(2025, 8, 1, 12, 0, 0)

    async def search_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        # Return a small deterministic set
        issues = [
            {
                "key": "PRJ-1",
                "fields": {
                    "summary": "Build auth",
                    "issuetype": {"name": "Story"},
                    "status": {"name": "In Progress", "statusCategory": {"name": "In Progress"}},
                    "parent": None,
                    "customfield_epic": "PRJ-EPIC1",
                    "project": {"key": "PRJ", "name": "Project PRJ"},
                    "created": (self._now - dt.timedelta(days=10)).isoformat(),
                    "updated": (self._now - dt.timedelta(days=1)).isoformat(),
                }
            },
            {
                "key": "PRJ-2",
                "fields": {
                    "summary": "Fix bugs",
                    "issuetype": {"name": "Task"},
                    "status": {"name": "Done", "statusCategory": {"name": "Done"}},
                    "parent": {"key": "PRJ-1"},
                    "customfield_epic": "PRJ-EPIC1",
                    "project": {"key": "PRJ", "name": "Project PRJ"},
                    "created": (self._now - dt.timedelta(days=5)).isoformat(),
                    "updated": (self._now - dt.timedelta(hours=2)).isoformat(),
                }
            }
        ]
        return {"issues": issues}

    async def get_issue_changelog(self, issue_key: str) -> Dict[str, Any]:
        # Deterministic simple transitions
        base = [
            {"from": "To Do", "to": "In Progress", "at": (self._now - dt.timedelta(days=9)).isoformat()},
            {"from": "In Progress", "to": "Done", "at": (self._now - dt.timedelta(days=2)).isoformat()},
        ]
        if issue_key == "PRJ-2":
            base = [
                {"from": "To Do", "to": "In Progress", "at": (self._now - dt.timedelta(days=4)).isoformat()},
                {"from": "In Progress", "to": "Done", "at": (self._now - dt.timedelta(days=1)).isoformat()},
            ]
        return {"values": base}

    async def me(self) -> Dict[str, Any]:
        return {"accountId": "mock-1", "emailAddress": "mock@example.com", "displayName": "Mock User"}
