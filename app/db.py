from __future__ import annotations
import os, random
from enum import Enum
from typing import Optional
from datetime import time, datetime
from sqlalchemy import (
    create_engine, String, Integer, Boolean, ForeignKey,
    Enum as SAEnum, Time, DateTime, Text, func, UniqueConstraint, event
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
)
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seqel.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

# Enums
class StreamEnum(str, Enum):
    SchoolsCup = "SchoolsCup"
    Competition = "Competition"

class ScoringMode(str, Enum):
    WIN_LOSE = "WIN_LOSE"
    TOP4 = "TOP4"
    PARTICIPATION = "PARTICIPATION"

class FinalsMetric(str, Enum):
    HigherIsBetter = "HigherIsBetter"
    LowerIsBetter = "LowerIsBetter"

# Master data
class School(Base):
    __tablename__ = "Schools"
    SchoolID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SchoolUID4: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    SchoolName: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    students: Mapped[list["Student"]] = relationship(back_populates="school")

class Student(Base):
    __tablename__ = "Students"
    StudentID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UID4: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    FirstName: Mapped[str] = mapped_column(String(100))
    LastName: Mapped[str] = mapped_column(String(100))
    SchoolID: Mapped[int] = mapped_column(ForeignKey("Schools.SchoolID"))
    Cohort: Mapped[str] = mapped_column(String(20))  # "High" / "Primary"
    NonConsent: Mapped[bool] = mapped_column(Boolean, default=False)
    IsRef: Mapped[bool] = mapped_column(Boolean, default=False)
    IsAdmin: Mapped[bool] = mapped_column(Boolean, default=False)

    school: Mapped["School"] = relationship(back_populates="students")

# Points catalogue and per-game overrides
class Points(Base):
    __tablename__ = "Points"
    Code: Mapped[str] = mapped_column(String(40), primary_key=True)   # e.g. "1st","Win","TimeLap"
    Label: Mapped[str] = mapped_column(String(80))
    Value: Mapped[int] = mapped_column(Integer, default=0)
    SortOrder: Mapped[int] = mapped_column(Integer, default=0)
    Active: Mapped[bool] = mapped_column(Boolean, default=True)

class Game(Base):
    __tablename__ = "Games"
    GameID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GameName: Mapped[str] = mapped_column(String(120), unique=True)
    Platform: Mapped[Optional[str]] = mapped_column(String(40), default=None)
    ScoringMode: Mapped[ScoringMode] = mapped_column(SAEnum(ScoringMode))
    FinalsMetric: Mapped[Optional[FinalsMetric]] = mapped_column(SAEnum(FinalsMetric), nullable=True)
    Notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    OverridePoints: Mapped[bool] = mapped_column(Boolean, default=False)

class GamePoints(Base):
    __tablename__ = "GamePoints"
    GPID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GameID: Mapped[int] = mapped_column(ForeignKey("Games.GameID"))
    Code: Mapped[str] = mapped_column(ForeignKey("Points.Code"))
    Value: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("GameID", "Code", name="uq_game_code"),)

class Round(Base):
    __tablename__ = "Rounds"
    RoundID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Label: Mapped[str] = mapped_column(String(60), unique=True)
    StartTime: Mapped[time] = mapped_column(Time)

class Event(Base):
    __tablename__ = "Events"
    EventID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GameID: Mapped[int] = mapped_column(ForeignKey("Games.GameID"))
    Stream: Mapped[StreamEnum] = mapped_column(SAEnum(StreamEnum))

class Area(Base):
    __tablename__ = "Areas"
    AreaID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GameID: Mapped[int] = mapped_column(ForeignKey("Games.GameID"))
    Stream: Mapped[StreamEnum] = mapped_column(SAEnum(StreamEnum))
    AreaName: Mapped[str] = mapped_column(String(120))
    __table_args__ = (UniqueConstraint("GameID","Stream","AreaName", name="uq_area_name"),)

# Matches and results
class Match(Base):
    __tablename__ = "Matches"
    MatchID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EventID: Mapped[int] = mapped_column(ForeignKey("Events.EventID"))
    AreaID: Mapped[int] = mapped_column(ForeignKey("Areas.AreaID"))
    RoundID: Mapped[int] = mapped_column(ForeignKey("Rounds.RoundID"))
    Stage: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # "Group","Quarter","Semi","Final"
    Cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    CancelReason: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class MatchParticipant(Base):
    __tablename__ = "MatchParticipants"
    MPID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    MatchID: Mapped[int] = mapped_column(ForeignKey("Matches.MatchID"))
    UID4: Mapped[int] = mapped_column(Integer)  # student’s public ID
    Slot: Mapped[int] = mapped_column(Integer)  # 1..4
    Outcome: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)  # "Win","Lose","1st",...
    PointsAwarded: Mapped[int] = mapped_column(Integer, default=0)
    MetricValueMs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # for time/score in finals/groups
    UniqueConstraint("MatchID","UID4")

# Settings
class Setting(Base):
    __tablename__ = "Settings"
    Key: Mapped[str] = mapped_column(String(80), primary_key=True)
    Value: Mapped[str] = mapped_column(String(400))

# --- Helpers: auto 4-digit IDs for Schools and Students
def _next_uid4(session: Session, table, column) -> int:
    used = {row[0] for row in session.query(column).all()}
    # keep 1000..2000 “guest window” unused for students, as requested; we still avoid collisions for both tables
    for candidate in range(3000, 10000):
        if candidate not in used:
            return candidate
    # last resort try rest of the pool
    for candidate in range(1000, 3000):
        if candidate not in used:
            return candidate
    raise RuntimeError("UID pool exhausted")

@event.listens_for(School, "before_insert")
def school_uid_before_insert(mapper, connection, target):
    if target.SchoolUID4 is None:
        with Session(bind=connection) as s:
            target.SchoolUID4 = _next_uid4(s, School, School.SchoolUID4)

@event.listens_for(Student, "before_insert")
def student_uid_before_insert(mapper, connection, target):
    if target.UID4 is None:
        with Session(bind=connection) as s:
            target.UID4 = _next_uid4(s, Student, Student.UID4)

# --- DB init and dependency
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
