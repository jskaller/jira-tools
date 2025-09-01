import csv, io, json
from typing import Dict, Any, List, Tuple
from ..db import SessionLocal, Report, ReportIssue, Issue, Stint, Settings

def create_report(params: Dict[str, Any], owner_id: int) -> int:
    db = SessionLocal()
    r = Report(name=params.get("name","Report"), owner_id=owner_id, params_json=json.dumps(params))
    db.add(r)
    db.commit()
    for issue in db.query(Issue).all():
        db.add(ReportIssue(report_id=r.id_pk, issue_key=issue.key))
    db.commit()
    rid = r.id_pk
    db.close()
    return rid

def get_report(rid: int) -> Dict[str, Any]:
    db = SessionLocal()
    r = db.query(Report).filter(Report.id_pk==rid).first()
    if not r:
        db.close()
        return {}
    issues = [ri.issue_key for ri in db.query(ReportIssue).filter(ReportIssue.report_id==rid).all()]
    db.close()
    return {"id": r.id_pk, "name": r.name, "params": json.loads(r.params_json), "issues": issues}

def list_reports() -> List[Dict[str, Any]]:
    db = SessionLocal()
    out = [{"id": r.id_pk, "name": r.name, "created_at": str(r.created_at)} for r in db.query(Report).order_by(Report.created_at.desc()).all()]
    db.close()
    return out

def delete_report(rid: int) -> bool:
    db = SessionLocal()
    db.query(ReportIssue).filter(ReportIssue.report_id==rid).delete()
    db.query(Report).filter(Report.id_pk==rid).delete()
    db.commit()
    db.close()
    return True

def csv_stints(rid: int) -> Tuple[str, str]:
    db = SessionLocal()
    issues = [ri.issue_key for ri in db.query(ReportIssue).filter(ReportIssue.report_id==rid).all()]
    si = db.query(Stint).filter(Stint.issue_key.in_(issues)).order_by(Stint.issue_key, Stint.entry_index).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["report_id","issue_key","status_name","status_category","stint_index","stint_start","stint_end","duration_seconds_24x7","duration_seconds_business"])
    for s in si:
        w.writerow([rid, s.issue_key, s.status, s.status_category, s.entry_index, s.start_at.isoformat(), s.end_at.isoformat(), s.dur_seconds_24x7, s.dur_seconds_bh])
    return (f"report-{rid}-stints.csv", out.getvalue())

def csv_issue_stats(rid: int) -> Tuple[str, str]:
    db = SessionLocal()
    issues = [ri.issue_key for ri in db.query(ReportIssue).filter(ReportIssue.report_id==rid).all()]
    stints = db.query(Stint).filter(Stint.issue_key.in_(issues)).all()
    agg = {}
    for s in stints:
        key = (s.issue_key, s.status)
        agg.setdefault(key, [0,0,0])
        agg[key][0] += s.dur_seconds_24x7
        agg[key][1] += s.dur_seconds_bh
        agg[key][2] += 1
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["report_id","issue_key","bucket","total_duration_seconds_24x7","total_duration_seconds_business","times_entered"])
    for (issue_key, bucket), vals in agg.items():
        w.writerow([rid, issue_key, bucket, vals[0], vals[1], vals[2]])
    return (f"report-{rid}-issue-stats.csv", out.getvalue())

def csv_rollups(rid: int) -> Tuple[str, str]:
    db = SessionLocal()
    issues = [ri.issue_key for ri in db.query(ReportIssue).filter(ReportIssue.report_id==rid).all()]
    stints = db.query(Stint).filter(Stint.issue_key.in_(issues)).all()
    per_issue = {}
    for s in stints:
        per_issue.setdefault(s.issue_key, [0,0,0])
        per_issue[s.issue_key][0] += s.dur_seconds_bh
        per_issue[s.issue_key][1] += s.dur_seconds_24x7
        per_issue[s.issue_key][2] += 1
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["report_id","node_type","node_key","parent_node_key","agg_by","bucket","total_duration_seconds_business","total_duration_seconds_24x7","times_entered","child_count"])
    for k, vals in per_issue.items():
        w.writerow([rid,"issue",k,"","","",vals[0],vals[1],vals[2],0])
    return (f"report-{rid}-rollups.csv", out.getvalue())
