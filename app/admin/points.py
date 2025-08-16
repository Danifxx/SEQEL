from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db, Points, Game, GamePoints

router = APIRouter()

@router.get("/points", response_class=HTMLResponse)
def points_page(
    request: Request,
    db: Session = Depends(get_db),
):
    # Global points, ordered
    pts = db.query(Points).order_by(Points.SortOrder, Points.Code).all()

    # Games, ordered
    games = db.query(Game).order_by(Game.GameName).all()

    # Per-game overrides -> {game_id: {code: value}}
    overrides: dict[int, dict[str, int]] = {}
    for g in games:
        rows = (
            db.query(GamePoints)
            .filter(GamePoints.GameID == g.GameID)
            .all()
        )
        overrides[g.GameID] = {r.Code: r.Value for r in rows}

    return request.app.state.templates.TemplateResponse(
        "admin_points.html", 
        {
            "request": request,
            "points": pts,
            "games": games,
            "overrides": overrides,
        },
    )

@router.post("/points/add")
def points_add(
    Code: str = Form(...),
    Label: str = Form(...),
    Value: int = Form(...),
    SortOrder: int = Form(0),
    Active: int = Form(1),                             
    db: Session = Depends(get_db),
):
    code = Code.strip()
    if not db.get(Points, code):
        db.add(
            Points(
                Code=code,
                Label=Label.strip(),
                Value=int(Value),
                SortOrder=int(SortOrder),
                Active=bool(int(Active)),                
            )
        )
        db.commit()
    return RedirectResponse(url="/admin/points", status_code=303)

@router.post("/points/override")
def points_override(
    GameID: int = Form(...),
    Code: str = Form(...),
    Value: int = Form(...),
    db: Session = Depends(get_db),
):
    code = Code.strip()
    gp = (
        db.query(GamePoints)
        .filter(GamePoints.GameID == int(GameID), GamePoints.Code == code)
        .one_or_none()
    )
    if gp:
        gp.Value = int(Value)
    else:
        db.add(GamePoints(GameID=int(GameID), Code=code, Value=int(Value)))
    db.commit()
    return RedirectResponse(url="/admin/points", status_code=303)
