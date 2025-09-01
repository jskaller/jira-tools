from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from ..security import require_user
from ..services.reports import create_report, list_reports, get_report, delete_report, csv_stints, csv_issue_stats, csv_rollups

router = APIRouter()

@router.get("")
def list_reports_api(user=Depends(require_user)):
    return list_reports()

@router.post("")
def create_report_api(payload: dict, user=Depends(require_user)):
    rid = create_report(payload, owner_id=user["id"])
    return {"id": rid}

@router.get("/{rid}")
def get_report_api(rid: int, user=Depends(require_user)):
    data = get_report(rid)
    if not data:
        raise HTTPException(404, "Report not found")
    return data

@router.delete("/{rid}")
def delete_report_api(rid: int, user=Depends(require_user)):
    delete_report(rid)
    return {"ok": True}

@router.get("/{rid}/csv")
def csv_api(rid: int, which: str, user=Depends(require_user)):
    name, content = {"stints": csv_stints, "issue": csv_issue_stats, "rollups": csv_rollups}[which](rid)
    return PlainTextResponse(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={name}"})
