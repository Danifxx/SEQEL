# app/admin/home.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..db import get_db, Points, Game, Round, Event, Area, School, Student

router = APIRouter()

@router.get("/", response_class=HTMLResponse)  # <-- must be "/"
def admin_home(request: Request, db: Session = Depends(get_db)):
    counts = {
        "points": db.query(Points).count(),
        "games": db.query(Game).count(),
        "rounds": db.query(Round).count(),
        "events": db.query(Event).count(),
        "areas": db.query(Area).count(),
        "schools": db.query(School).count(),
        "students": db.query(Student).count(),
    }
    return request.app.state.templates.TemplateResponse(
        "admin_home.html",
        {"request": request, "counts": counts},
    )
