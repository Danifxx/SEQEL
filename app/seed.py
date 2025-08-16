from sqlalchemy import select
from datetime import time
from sqlalchemy.orm import Session
from .db import Points, Game, Round, Event, Area, StreamEnum, ScoringMode, FinalsMetric

def seed_all(db: Session):
    # Points
    defaults = [
        ("1st","1st",50,1),
        ("2nd","2nd",20,2),
        ("3rd","3rd",15,3),
        ("4th","4th",10,4),
        ("Win","Win",50,10),
        ("Lose","Lose",25,11),
        ("Tie","Tie",10,12),
        ("TimeLap","Time Lap",10,20),
        ("Participation","Participation",10,30),
    ]
    exists = {p.Code for p in db.execute(select(Points)).scalars().all()}
    for code,label,val,order in defaults:
        if code not in exists:
            db.add(Points(Code=code, Label=label, Value=val, SortOrder=order, Active=True))
    db.commit()

    # Games
    games = [
        ("Velocity Drone", "PC", ScoringMode.WIN_LOSE, FinalsMetric.LowerIsBetter, "Drone lap time stored; TimeLap bonus applies"),
        ("Rocket League", "Switch", ScoringMode.WIN_LOSE, FinalsMetric.HigherIsBetter, None),
        ("Asphalt 9", "Switch", ScoringMode.TOP4, FinalsMetric.LowerIsBetter, None),
        ("NBA", "Switch", ScoringMode.WIN_LOSE, FinalsMetric.HigherIsBetter, None),
        ("FC25", "Switch", ScoringMode.WIN_LOSE, FinalsMetric.HigherIsBetter, None),
        ("Just Dance", "Switch", ScoringMode.TOP4, FinalsMetric.HigherIsBetter, None),
        ("Brawlhalla", "Switch", ScoringMode.WIN_LOSE, FinalsMetric.HigherIsBetter, None),
        ("Assetto Corsa", "PC", ScoringMode.TOP4, FinalsMetric.LowerIsBetter, None),
        ("Other", "Other", ScoringMode.PARTICIPATION, None, "Participation only"),
    ]
    existing_names = {g.GameName for g in db.execute(select(Game)).scalars().all()}
    for name, plat, smode, fmetric, notes in games:
        if name not in existing_names:
            db.add(Game(GameName=name, Platform=plat, ScoringMode=smode, FinalsMetric=fmetric, Notes=notes))
    db.commit()

    # Rounds
    rounds = [
        ("Round 1", time(9,20)), ("Round 2", time(9,30)), ("Round 3", time(9,40)),
        ("Round 4", time(9,50)), ("Round 5", time(10,0)), ("Round 6", time(10,10)),
        ("Round 7", time(10,20)), ("Round 8", time(10,30)), ("Round 9", time(10,40)),
        ("Round 10", time(10,50)), ("Round 11", time(11,0)), ("Round 12", time(11,10)),
        ("Round 13", time(11,20)), ("Round 14", time(11,30)), ("Round 15", time(11,40)),
        ("Round 16", time(11,50)), ("Round 17", time(12,0)), ("Round 18", time(12,10)),
        ("Round 19", time(12,20)), ("Round 20", time(12,30)), ("Round 21", time(12,40)),
        ("Quarter 1", time(12,50)), ("Quarter 2", time(13,0)),
        ("Quarter 3", time(13,10)), ("Quarter 4", time(13,20)),
        ("Semi 1", time(13,30)), ("Semi 2", time(13,40)),
        ("Final", time(13,50)),
    ]
    have = {r.Label for r in db.execute(select(Round)).scalars().all()}
    for lbl, t in rounds:
        if lbl not in have:
            db.add(Round(Label=lbl, StartTime=t))
    db.commit()

    # Events + Areas per game (two areas per game: Schools Cup Side, Competition Side)
    games_rows = db.execute(select(Game)).scalars().all()
    for g in games_rows:
        for stream in (StreamEnum.SchoolsCup, StreamEnum.Competition):
            ev = db.execute(select(Event).where(Event.GameID==g.GameID, Event.Stream==stream)).scalar_one_or_none()
            if not ev:
                db.add(Event(GameID=g.GameID, Stream=stream))
            # areas
            area_name = "Schools Cup Side" if stream == StreamEnum.SchoolsCup else "Competition Side"
            ar = db.execute(select(Area).where(Area.GameID==g.GameID, Area.Stream==stream, Area.AreaName==area_name)).scalar_one_or_none()
            if not ar:
                db.add(Area(GameID=g.GameID, Stream=stream, AreaName=area_name))
    db.commit()
