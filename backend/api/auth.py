from fastapi import APIRouter, Request, Form
from ..db import SessionLocal, User
from ..security import verify_password

router = APIRouter()

@router.post("/login")
def api_login(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.email==email).first()
    if user and verify_password(password, user.password_hash):
        request.session["user_id"] = user.id
        request.session["role"] = user.role
        return {"ok": True}
    return {"ok": False}

@router.post("/logout")
def api_logout(request: Request):
    request.session.clear()
    return {"ok": True}
