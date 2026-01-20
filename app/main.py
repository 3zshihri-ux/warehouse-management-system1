import os
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from starlette.middleware.sessions import SessionMiddleware

from .db import Base, engine, get_db
from .models import User, Warehouse, Shelf, Equipment, Movement
from .security import hash_password, verify_password

APP_TITLE = "نظام ادارة المستودع"

app = FastAPI(title=APP_TITLE)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"))

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

def ensure_db():
    Base.metadata.create_all(bind=engine)

def seed_admin(db: Session):
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe_12345")
    exists = db.scalar(select(func.count()).select_from(User).where(User.email == admin_email))
    if not exists:
        db.add(User(email=admin_email, password_hash=hash_password(admin_password), role="admin"))
        db.commit()

@app.on_event("startup")
def on_startup():
    ensure_db()
    # create admin on first run
    from .db import SessionLocal
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()

def current_user(request: Request, db: Session) -> User | None:
    email = request.session.get("user_email")
    if not email:
        return None
    return db.scalar(select(User).where(User.email == email))

def require_login(request: Request, db: Session) -> User:
    user = current_user(request, db)
    if not user:
        raise PermissionError("not_logged_in")
    return user

@app.exception_handler(PermissionError)
async def perm_error_handler(request: Request, exc: PermissionError):
    return RedirectResponse(url="/login", status_code=302)

@app.get("/", response_class=HTMLResponse)
def root(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db), msg: str | None = None):
    return templates.TemplateResponse("login.html", {"request": request, "title": APP_TITLE, "msg": msg})

@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?msg=بيانات الدخول غير صحيحة", status_code=302)
    request.session["user_email"] = user.email
    request.session["role"] = user.role
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login?msg=تم تسجيل الخروج", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    counts = {
        "total_equipment": db.scalar(select(func.count()).select_from(Equipment)) or 0,
        "ready": db.scalar(select(func.count()).select_from(Equipment).where(Equipment.status=="جاهزة")) or 0,
        "rented": db.scalar(select(func.count()).select_from(Equipment).where(Equipment.status=="مؤجرة")) or 0,
        "maintenance": db.scalar(select(func.count()).select_from(Equipment).where(Equipment.status=="تحت الصيانة")) or 0,
        "warehouses": db.scalar(select(func.count()).select_from(Warehouse)) or 0,
        "shelves": db.scalar(select(func.count()).select_from(Shelf)) or 0,
    }
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": APP_TITLE, "user": user, "counts": counts})

def next_equipment_code(db: Session) -> str:
    max_id = db.scalar(select(func.max(Equipment.id))) or 0
    return f"EQ-{max_id+1:06d}"

@app.get("/equipment", response_class=HTMLResponse)
def equipment_list(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    user = require_login(request, db)
    stmt = select(Equipment).order_by(Equipment.id.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Equipment.name.ilike(like)) | (Equipment.code.ilike(like)) | (Equipment.serial_number.ilike(like)))
    items = db.scalars(stmt).all()
    shelves = db.scalars(select(Shelf).order_by(Shelf.id.desc())).all()
    return templates.TemplateResponse("equipment_list.html", {"request": request, "title": APP_TITLE, "user": user, "items": items, "shelves": shelves, "q": q or ""})

@app.post("/equipment/create")
def equipment_create(
    request: Request,
    name: str = Form(...),
    category: str = Form(""),
    serial_number: str = Form(""),
    asset_number: str = Form(""),
    status: str = Form("جاهزة"),
    shelf_id: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_login(request, db)
    code = next_equipment_code(db)
    shelf = None
    if shelf_id and shelf_id.isdigit():
        shelf = db.get(Shelf, int(shelf_id))
    eq = Equipment(
        code=code,
        name=name.strip(),
        category=category.strip() or None,
        serial_number=serial_number.strip() or None,
        asset_number=asset_number.strip() or None,
        status=status,
        shelf_id=shelf.id if shelf else None,
        notes=notes.strip() or None,
    )
    db.add(eq)
    db.commit()
    return RedirectResponse("/equipment", status_code=302)

@app.post("/equipment/{equipment_id}/delete")
def equipment_delete(request: Request, equipment_id: int, db: Session = Depends(get_db)):
    user = require_login(request, db)
    eq = db.get(Equipment, equipment_id)
    if eq:
        db.delete(eq)
        db.commit()
    return RedirectResponse("/equipment", status_code=302)

@app.get("/warehouses", response_class=HTMLResponse)
def warehouses_page(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    items = db.scalars(select(Warehouse).order_by(Warehouse.id.desc())).all()
    return templates.TemplateResponse("warehouses.html", {"request": request, "title": APP_TITLE, "user": user, "items": items})

@app.post("/warehouses/create")
def warehouses_create(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    location: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_login(request, db)
    wh = Warehouse(name=name.strip(), code=code.strip().upper(), location=location.strip() or None)
    db.add(wh)
    db.commit()
    return RedirectResponse("/warehouses", status_code=302)

@app.get("/shelves", response_class=HTMLResponse)
def shelves_page(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    shelves = db.scalars(select(Shelf).order_by(Shelf.id.desc())).all()
    warehouses = db.scalars(select(Warehouse).order_by(Warehouse.id.desc())).all()
    return templates.TemplateResponse("shelves.html", {"request": request, "title": APP_TITLE, "user": user, "items": shelves, "warehouses": warehouses})

@app.post("/shelves/create")
def shelves_create(
    request: Request,
    warehouse_id: int = Form(...),
    code: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_login(request, db)
    shelf = Shelf(warehouse_id=warehouse_id, code=code.strip().upper(), description=description.strip() or None)
    db.add(shelf)
    db.commit()
    return RedirectResponse("/shelves", status_code=302)

@app.get("/movements", response_class=HTMLResponse)
def movements_page(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    items = db.scalars(select(Movement).order_by(Movement.id.desc()).limit(200)).all()
    equipment = db.scalars(select(Equipment).order_by(Equipment.id.desc())).all()
    shelves = db.scalars(select(Shelf).order_by(Shelf.id.desc())).all()
    return templates.TemplateResponse("movements.html", {"request": request, "title": APP_TITLE, "user": user, "items": items, "equipment": equipment, "shelves": shelves})

@app.post("/movements/create")
def movements_create(
    request: Request,
    equipment_id: int = Form(...),
    type: str = Form(...),
    to_person: str = Form(""),
    project: str = Form(""),
    from_shelf: str = Form(""),
    to_shelf: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = require_login(request, db)
    mv = Movement(
        equipment_id=equipment_id,
        type=type.strip(),
        to_person=to_person.strip() or None,
        project=project.strip() or None,
        from_shelf=from_shelf.strip() or None,
        to_shelf=to_shelf.strip() or None,
        notes=notes.strip() or None,
    )
    db.add(mv)
    # Update equipment shelf/status simple rules
    eq = db.get(Equipment, equipment_id)
    if eq:
        if type.strip() in ["صرف", "تسليم"]:
            eq.status = "قيد التشغيل"
        if type.strip() in ["تأجير"]:
            eq.status = "مؤجرة"
        if type.strip() in ["استلام", "إرجاع"]:
            eq.status = "جاهزة"
        if to_shelf.strip():
            # attempt set shelf by code
            shelf = db.scalar(select(Shelf).where(Shelf.code == to_shelf.strip().upper()))
            if shelf:
                eq.shelf_id = shelf.id
    db.commit()
    return RedirectResponse("/movements", status_code=302)
