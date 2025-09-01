import os, json, datetime as dt
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("SQLITE_PATH", "./data/jira_reports.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, server_default=func.now())

class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    jira_base_url = Column(String, default="https://your-domain.atlassian.net")
    jira_email = Column(String, nullable=True)
    jira_token_ciphertext = Column(Text, nullable=True)
    default_projects_json = Column(Text, default="[]")
    jql_default = Column(Text, default="")
    time_mode = Column(String, default="business")  # business|24x7
    bh_start = Column(Integer, default=9)
    bh_end = Column(Integer, default=17)
    bh_days_json = Column(Text, default=json.dumps([1,2,3,4,5]))
    max_issues = Column(Integer, default=25000)
    updated_days_limit = Column(Integer, default=180)
    agg_mode = Column(String, default="both")
    custom_status_buckets_json = Column(Text, default="{}")
    use_real_jira = Column(Boolean, default=False)

class Project(Base):
    __tablename__ = "projects"
    key = Column(String, primary_key=True)
    name = Column(String)

class Issue(Base):
    __tablename__ = "issues"
    id_pk = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    project_key = Column(String, ForeignKey("projects.key"))
    type = Column(String)
    summary = Column(Text)
    status = Column(String)
    status_category = Column(String)
    epic_key = Column(String, nullable=True)
    parent_key = Column(String, nullable=True)
    created = Column(DateTime)
    updated = Column(DateTime)

class Transition(Base):
    __tablename__ = "transitions"
    id_pk = Column(Integer, primary_key=True)
    issue_key = Column(String, index=True)
    from_status = Column(String)
    to_status = Column(String)
    at = Column(DateTime, index=True)

class Stint(Base):
    __tablename__ = "stints"
    id_pk = Column(Integer, primary_key=True)
    issue_key = Column(String, index=True)
    status = Column(String)
    status_category = Column(String)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    dur_seconds_24x7 = Column(Integer)
    dur_seconds_bh = Column(Integer)
    entry_index = Column(Integer)

class Report(Base):
    __tablename__ = "reports"
    id_pk = Column(Integer, primary_key=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    params_json = Column(Text)

class ReportIssue(Base):
    __tablename__ = "report_issues"
    id_pk = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("reports.id_pk"))
    issue_key = Column(String, index=True)

def init_db(force: bool=False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    Base.metadata.create_all(engine)
    # bootstrap admin + settings
    from .security import get_password_hash
    db = SessionLocal()
    if not db.query(User).first():
        import os
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        db.add(User(email=admin_email, password_hash=get_password_hash(admin_password), role="admin"))
    if not db.query(Settings).first():
        db.add(Settings())
    db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()
