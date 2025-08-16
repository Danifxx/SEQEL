from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .db import get_db, Match, MatchParticipant, GamePoints

router = APIRouter()

@router.get("/maintenance", response_class=HTMLResponse)
def maintenance_page(request: Request):
    return request.app.state.templates.TemplateResponse("admin_maintenance.html", {"request": request})

@router.post("/maintenance/reset")
def maintenance_reset(scope: str = Form(...)):
    db: Session = next(get_db())
    scope = (scope or "").lower()
    if scope in ("day","tournament","full"):
        db.query(MatchParticipant).delete(synchronize_session=False)
        db.query(GamePoints).delete(synchronize_session=False)
        db.query(Match).delete(synchronize_session=False)
        db.commit()
    return RedirectResponse(url="/admin/maintenance", status_code=303)
