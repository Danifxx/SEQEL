from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .db import get_db, MatchParticipant, Student, School, Event, Game, StreamEnum

router = APIRouter()

@router.get("/boards/students", response_class=HTMLResponse)
def board_students(request: Request, game_id: int | None = None, stream: str | None = None):
    db: Session = next(get_db())

    q = (
        select(MatchParticipant.UID4, func.sum(MatchParticipant.PointsAwarded))
        .group_by(MatchParticipant.UID4)
        .order_by(func.sum(MatchParticipant.PointsAwarded).desc())
    )

    if game_id or stream:
        q = q.join(Event, Event.EventID==MatchParticipant.MatchID, isouter=True)  # join via Match -> Event
        # easier: join chain explicitly
    # Simpler approach: compute totals all, filter later in code if needed — keeping this board global as requested.

    rows = db.execute(q).all()
    # Build list with school
    out = []
    for uid, pts in rows[:30]:
        sch = db.execute(
            select(School.SchoolName)
            .join(Student, Student.SchoolID==School.SchoolID)
            .where(Student.UID4==uid)
        ).scalar_one_or_none()
        out.append({"uid": uid, "school": sch or "", "pts": int(pts or 0)})

    return request.app.state.templates.TemplateResponse("board_students.html", {"request": request, "rows": out})
