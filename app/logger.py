from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_db, Game, Round, Event, Area, Match, MatchParticipant, StreamEnum, ScoringMode, FinalsMetric, Setting
from .utils import points_lookup

router = APIRouter()

def get_setting(db: Session, key: str, default: str = "") -> str:
    s = db.get(Setting, key)
    return s.Value if s else default

@router.get("/logger", response_class=HTMLResponse)
def logger_page(request: Request):
    db: Session = next(get_db())
    games = db.query(Game).order_by(Game.GameName).all()
    rounds = db.query(Round).order_by(Round.StartTime).all()
    return request.app.state.templates.TemplateResponse("logger.html", {"request": request, "games": games, "rounds": rounds, "StreamEnum": StreamEnum})

@router.post("/logger/submit")
def logger_submit(
    GameID: int = Form(...),
    Stream: str = Form(...),
    RoundID: int = Form(...),
    AreaID: int = Form(...),
    Mode: str = Form(...),
    UID1: int = Form(None),
    UID2: int = Form(None),
    UID3: int = Form(None),
    UID4: int = Form(None),
    WinnerUID: int = Form(None),
    Place1: int = Form(None),
    Place2: int = Form(None),
    Place3: int = Form(None),
    Place4: int = Form(None),
    FinalsUID: int = Form(None),
    FinalsMetricValue: float = Form(None),  # seconds or score
):
    db: Session = next(get_db())

    # Create Match
    ev = db.execute(select(Event).where(Event.GameID==GameID, Event.Stream==StreamEnum(Stream))).scalar_one()
    m = Match(EventID=ev.EventID, AreaID=AreaID, RoundID=RoundID, Stage="Group")
    db.add(m); db.flush()

    g = db.get(Game, GameID)

    def award(uid: int, code: str, metric_ms: int | None = None):
        pts = points_lookup(db, GameID, code) or 0
        db.add(MatchParticipant(MatchID=m.MatchID, UID4=uid, Slot=0, Outcome=code, PointsAwarded=pts, MetricValueMs=metric_ms))

    if Mode == "WIN_LOSE":
        if WinnerUID not in (UID1, UID2):
            return RedirectResponse("/logger?error=WinnerMismatch", status_code=303)
        loser = UID2 if WinnerUID == UID1 else UID1
        award(WinnerUID, "Win")
        award(loser, "Lose")

        # Drone TimeLap bonus in groups
        drone_bonus = get_setting(db, "DRONE_TIMELAP_BONUS", "Yes")
        if g.GameName.lower().startswith("velocity") and drone_bonus.lower().startswith("y"):
            # If time was typed into FinalsMetricValue for this group race, treat as lap ms and add TimeLap
            if FinalsMetricValue is not None:
                ms = int(FinalsMetricValue * 1000)
                # we only store metric on winner’s entry for reference
                award(WinnerUID, "TimeLap", metric_ms=ms)

    elif Mode == "TOP4":
        order = [Place1, Place2, Place3, Place4]
        codes = ["1st","2nd","3rd","4th"]
        for uid, code in zip(order, codes):
            if uid:
                award(uid, code)

    elif Mode == "FINALS":
        # One player with a numeric metric; who wins is decided later by comparing metrics
        ms = None
        if FinalsMetricValue is not None:
            ms = int(FinalsMetricValue * 1000)
        # We store metric only; points will be added by awarding a “FinalsEntry” or mapped codes after evaluation
        db.add(MatchParticipant(MatchID=m.MatchID, UID4=FinalsUID, Slot=1, Outcome=None, PointsAwarded=0, MetricValueMs=ms))

    db.commit()
    return RedirectResponse(url=f"/logger?ok=1&next_round={RoundID}", status_code=303)
