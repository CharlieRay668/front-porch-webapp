from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, List, Dict
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
# This is a change
load_dotenv()  # Load environment variables from .env file

app = FastAPI(title="Volunteer Signup")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "volunteers.db")
engine = create_engine(
    f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False}
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOURS = list(range(7, 24))  # 7 to 23

# Business rules for availability
# Friday 7-16 (i.e., 4 pm), Sunday 9-17, Saturday unavailable
AVAILABLE_RULES = {
    "Friday": set(range(7, 17)),
    "Sunday": set(range(9, 18)),
}

CAPACITY = 4

class Signup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    day: str
    hour: int
    name: str

class Admin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    password_hash: str


def init_db():
    SQLModel.metadata.create_all(engine)
    # Create default admin if not exists
    with Session(engine) as session:
        admin = session.exec(select(Admin).where(Admin.username == ADMIN_USERNAME)).first()
        if not admin:
            pw_hash = pwd_context.hash(ADMIN_PASSWORD)
            session.add(Admin(username=ADMIN_USERNAME, password_hash=pw_hash))
            session.commit()


@app.on_event("startup")
def on_startup():
    init_db()


def hour_available(day: str, hour: int) -> bool:
    if day == "Saturday":
        return False
    if day in AVAILABLE_RULES:
        return hour in AVAILABLE_RULES[day]
    # Other days 7-23 available by default
    return True


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Build grid data with remaining slots per cell and current signups
    with Session(engine) as session:
        available_map: Dict[str, Dict[int, bool]] = {d: {h: hour_available(d, h) for h in HOURS} for d in DAYS}
        data: Dict[str, Dict[int, List[Signup]]] = {d: {h: [] for h in HOURS} for d in DAYS}
        rows = session.exec(select(Signup)).all()
        for r in rows:
            if r.day in data and r.hour in data[r.day]:
                data[r.day][r.hour].append(r)
        remaining: Dict[str, Dict[int, int]] = {
            d: {h: (CAPACITY if available_map[d][h] else 0) - len(data[d][h]) for h in HOURS} for d in DAYS
        }
    return templates.TemplateResponse("index.html", {"request": request, "days": DAYS, "hours": HOURS, "remaining": remaining, "available": available_map, "data": data, "capacity": CAPACITY})


@app.post("/signup")
async def signup(request: Request, day: str = Form(...), hour: int = Form(...), people_count: int = Form(...)):
    if day not in DAYS or hour not in HOURS:
        raise HTTPException(status_code=400, detail="Invalid slot")
    if not hour_available(day, hour):
        raise HTTPException(status_code=400, detail="This slot is not available")
    if people_count < 1:
        raise HTTPException(status_code=400, detail="Invalid number of people")

    form_data = await request.form()
    requested_names: List[str] = []
    for i in range(1, people_count + 1):
        fn = str(form_data.get(f"first_name_{i}", "")).strip()
        ln = str(form_data.get(f"last_name_{i}", "")).strip()
        full = (fn + " " + ln).strip()
        if full:
            requested_names.append(full)
    if not requested_names:
        raise HTTPException(status_code=400, detail="At least one name is required")

    with Session(engine) as session:
        current = session.exec(select(Signup).where(Signup.day == day, Signup.hour == hour)).all()
        remaining = max(0, CAPACITY - len(current))
        if remaining <= 0:
            raise HTTPException(status_code=400, detail="This slot is full")
        # Only allow up to remaining
        names_to_add = requested_names[:remaining]
        for nm in names_to_add:
            session.add(Signup(day=day, hour=hour, name=nm))
        session.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# Simple cookie-based session for admin
from fastapi import Cookie
from secrets import token_urlsafe

SESSIONS: Dict[str, str] = {}

def is_admin_session(session_id: Optional[str]) -> bool:
    return bool(session_id) and SESSIONS.get(session_id) == ADMIN_USERNAME


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, session_id: Optional[str] = Cookie(default=None)):
    username = SESSIONS.get(session_id) if session_id else None
    if username != ADMIN_USERNAME:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})

    # Show dashboard
    with Session(engine) as db:
        data: Dict[str, Dict[int, List[Signup]]] = {d: {h: [] for h in HOURS} for d in DAYS}
        rows = db.exec(select(Signup)).all()
        for r in rows:
            if r.day in data and r.hour in data[r.day]:
                data[r.day][r.hour].append(r)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "days": DAYS, "hours": HOURS, "data": data, "capacity": CAPACITY})


@app.post("/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    with Session(engine) as session:
        admin = session.exec(select(Admin).where(Admin.username == username)).first()
        if not admin or not pwd_context.verify(password, admin.password_hash):
            return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid credentials"})
        sid = token_urlsafe(32)
        SESSIONS[sid] = admin.username
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie("session_id", sid, httponly=True, samesite="lax")
        return response


@app.post("/admin/logout")
async def admin_logout(session_id: Optional[str] = Cookie(default=None)):
    if session_id and session_id in SESSIONS:
        SESSIONS.pop(session_id, None)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


# Admin delete without password
@app.post("/admin/delete_signup")
async def admin_delete_signup(signup_id: int = Form(...), session_id: Optional[str] = Cookie(default=None)):
    if not is_admin_session(session_id):
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    with Session(engine) as session:
        s = session.get(Signup, signup_id)
        if s:
            session.delete(s)
            session.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


# Admin move signup to another slot
@app.post("/admin/move_signup")
async def admin_move_signup(signup_id: int = Form(...), day: str = Form(...), hour: int = Form(...), session_id: Optional[str] = Cookie(default=None)):
    if not is_admin_session(session_id):
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    if day not in DAYS or hour not in HOURS or not hour_available(day, hour):
        raise HTTPException(status_code=400, detail="Invalid target slot")
    with Session(engine) as session:
        s = session.get(Signup, signup_id)
        if not s:
            raise HTTPException(status_code=404, detail="Signup not found")
        # Capacity check excluding this signup
        count = session.exec(select(Signup).where(Signup.day == day, Signup.hour == hour, Signup.id != signup_id)).all()
        if len(count) >= CAPACITY:
            raise HTTPException(status_code=400, detail="Target slot is full")
        s.day = day
        s.hour = hour
        session.add(s)
        session.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
