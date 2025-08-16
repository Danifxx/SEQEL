from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .db import init_db
from .seed import seed_all
from .admin import router as admin_router
from .logger import router as logger_router
from .boards import router as boards_router
from sqlalchemy.orm import Session
from .db import SessionLocal

app = FastAPI(title="SEQEL Esports")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates

@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

app.include_router(admin_router)
app.include_router(logger_router)
app.include_router(boards_router)
