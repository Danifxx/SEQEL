from __future__ import annotations

from typing import Optional, Iterable, Tuple, Set, Union
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Points, GamePoints


def points_lookup(db: Session, game_id: int, code: str) -> Optional[int]:
    """
    Return the points value for an outcome `code`, preferring per-game overrides.
    Falls back to global Points table if no override exists.
    """
    # Per-game override?
    gp = db.execute(
        select(GamePoints.Value).where(
            GamePoints.GameID == game_id,
            GamePoints.Code == code,
        )
    ).scalar_one_or_none()
    if gp is not None:
        return int(gp)

    # Global default
    pv = db.execute(
        select(Points.Value).where(Points.Code == code)
    ).scalar_one_or_none()
    return int(pv) if pv is not None else None


def allocate_uid4(
    db_or_taken: Union[Session, Set[int]],
    taken: Optional[Set[int]] = None,
    avoid_range: Tuple[int, int] = (1000, 2000),
    search_range: Tuple[int, int] = (1000, 9999),
) -> Optional[int]:
    """
    Allocate a free 4-digit UID in search_range while skipping avoid_range and any already-taken values.

    Flexible call signature so it works with existing code:
      - allocate_uid4(taken_set)                                  # simplest
      - allocate_uid4(taken_set, avoid_range=(1000,1999))         # custom avoid block
      - allocate_uid4(db_session, taken_set, avoid_range=(...))   # if you previously passed a db first

    Returns:
        int UID in [search_range[0]..search_range[1]] or None if pool exhausted.
    """
    # Support both calling styles: (taken_set) OR (db, taken_set)
    if isinstance(db_or_taken, set):
        taken_set = set(db_or_taken)
    else:
        # First param was likely a Session; use the explicit `taken` set
        taken_set = set(taken or ())

    low, high = search_range
    avoid_lo, avoid_hi = avoid_range

    # First pass: outside avoid_range
    for candidate in range(low, high + 1):
        if avoid_lo <= candidate <= avoid_hi:
            continue
        if candidate not in taken_set:
            return candidate

    # Second pass (if we truly must): include avoid_range too
    for candidate in range(low, high + 1):
        if candidate not in taken_set:
            return candidate

    return None  # exhausted


def normalize_cohort(value: str) -> str:
    """
    Normalize cohort labels to 'High' or 'Primary'.
    Any non-'primary' string defaults to 'High'.
    """
    v = (value or "").strip().lower()
    if v.startswith("pri"):
        return "Primary"
    return "High"
