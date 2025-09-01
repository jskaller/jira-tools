import datetime as dt
from typing import Dict, Any
from ..db import SessionLocal, Project, Issue, Transition, Stint, Settings
from .timecalc import business_seconds
from ..clients.mock_jira import MockJiraClient
from ..clients.http_jira import HttpJiraClient

async def get_client(use_real: bool):
    return HttpJiraClient() if use_real else MockJiraClient()

def json_to_set(s: str):
    import json
    try:
        return set(json.loads(s))
    except Exception:
        return {0,1,2,3,4}

async def sync_run(params: Dict[str, Any]) -> Dict[str, Any]:
    db = SessionLocal()
    settings = db.query(Settings).first()
    client = await get_client(settings.use_real_jira)
    jql = params.get("jql") or settings.jql_default or "order by updated desc"
    data = await client.search_issues(jql=jql, max_results=min(settings.max_issues, 1000))
    count = 0
    for raw in data.get("issues", []):
        key = raw["key"]
        fields = raw["fields"]
        proj_key = fields["project"]["key"]
        proj_name = fields["project"]["name"]
        if not db.get(Project, proj_key):
            db.add(Project(key=proj_key, name=proj_name))
        created = dt.datetime.fromisoformat(fields["created"])
        updated = dt.datetime.fromisoformat(fields["updated"])
        issue = db.query(Issue).filter(Issue.key==key).first()
        if not issue:
            issue = Issue(key=key, project_key=proj_key, type=fields["issuetype"]["name"], summary=fields["summary"],
                          status=fields["status"]["name"], status_category=fields["status"]["statusCategory"]["name"],
                          epic_key=fields.get("customfield_epic"), parent_key=(fields.get("parent") or {}).get("key"),
                          created=created, updated=updated)
            db.add(issue)
        else:
            issue.status = fields["status"]["name"]
            issue.status_category = fields["status"]["statusCategory"]["name"]
            issue.updated = updated
        changelog = await client.get_issue_changelog(key)
        db.query(Transition).filter(Transition.issue_key==key).delete()
        for v in changelog.get("values", []):
            at = dt.datetime.fromisoformat(v["at"])
            db.add(Transition(issue_key=key, from_status=v["from"], to_status=v["to"], at=at))
        db.commit()
        db.query(Stint).filter(Stint.issue_key==key).delete()
        trans = db.query(Transition).filter(Transition.issue_key==key).order_by(Transition.at.asc()).all()
        if not trans:
            continue
        prev_time = created
        prev_status = trans[0].from_status
        entry_index = 0
        for t in trans:
            start = prev_time
            end = t.at
            dur_24 = int((end - start).total_seconds())
            dur_bh = business_seconds(start, end, settings.bh_start, settings.bh_end, set(json_to_set(settings.bh_days_json)))
            db.add(Stint(issue_key=key, status=prev_status, status_category=issue.status_category,
                         start_at=start, end_at=end, dur_seconds_24x7=dur_24, dur_seconds_bh=dur_bh, entry_index=entry_index))
            prev_status = t.to_status
            prev_time = t.at
            entry_index += 1
        end = updated
        dur_24 = int((end - prev_time).total_seconds())
        dur_bh = business_seconds(prev_time, end, settings.bh_start, settings.bh_end, set(json_to_set(settings.bh_days_json)))
        db.add(Stint(issue_key=key, status=prev_status, status_category=issue.status_category,
                     start_at=prev_time, end_at=end, dur_seconds_24x7=dur_24, dur_seconds_bh=dur_bh, entry_index=entry_index))
        db.commit()
        count += 1
    db.close()
    return {"issues_processed": count}
