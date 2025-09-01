from fastapi import APIRouter, Depends
from ..security import require_user
from ..services.sync_service import sync_run

router = APIRouter()

@router.post("/runs")
async def start_sync(payload: dict, user=Depends(require_user)):
    res = await sync_run(payload or {})
    return res
