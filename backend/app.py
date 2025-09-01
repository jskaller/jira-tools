import os
from fastapi import FastAPI, Request, Depends, Response, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from .security import get_password_hash, verify_password, require_user, require_admin
from .db import init_db, SessionLocal, User, Settings, get_db
from .api import auth as auth_api, admin as admin_api, reports as reports_api, sync as sync_api

load_dotenv()
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="jira-reports", lifespan=lifespan)

# Sessions (cookie-based)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("APP_SECRET", "dev-secret"))

# Static & templates
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Routers
app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_api.router, prefix="/api/admin", tags=["admin"])
app.include_router(reports_api.router, prefix="/api/reports", tags=["reports"])
app.include_router(sync_api.router, prefix="/api/sync", tags=["sync"])

# ---- UI routes ----

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/reports", status_code=302)
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    from .db import get_user_by_email
    db = SessionLocal()
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "title": "Login", "error": "Invalid credentials"}, status_code=401)
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    return RedirectResponse("/reports", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, user=Depends(require_admin)):
    return templates.TemplateResponse("admin.html", {"request": request, "title": "Admin"})

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse("reports.html", {"request": request, "title": "Reports"})

@app.get("/reports/{report_id}", response_class=HTMLResponse)
def report_detail_page(report_id: int, request: Request, user=Depends(require_user)):
    return templates.TemplateResponse("report_detail.html", {"request": request, "title": f"Report {report_id}", "report_id": report_id})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--initdb", action="store_true")
    args = parser.parse_args()
    if args.initdb:
        init_db(force=True)
        print("Database initialized.")
