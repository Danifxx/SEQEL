from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db, School

router = APIRouter()

@router.get("/schools", response_class=HTMLResponse)
def schools_page(
    request: Request,
    db: Session = Depends(get_db),
):
    rows = db.query(School).order_by(School.SchoolName).all()
    return request.app.state.templates.TemplateResponse(
        "admin_schools.html",
        {"request": request, "schools": rows},
    )

def _allocate_school_uid4(db: Session) -> int:
    """
    Return an available 4-digit UID in [1000..9999], avoiding 1000..1999
    (reserve that low block for other uses). Guarantees uniqueness.
    """
    taken = {uid for (uid,) in db.query(School.UID4).all() if uid is not None}
    for candidate in range(2000, 10000):  # start at 2000 to avoid the low block
        if candidate not in taken:
            return candidate
    raise RuntimeError("No available UID4 values for schools")

@router.post("/schools/add")
def schools_add(
    SchoolName: str = Form(...),
    db: Session = Depends(get_db),
):
    name = SchoolName.strip()
    if not name:
        return RedirectResponse(url="/admin/schools", status_code=303)

    exists = db.query(School).filter(School.SchoolName == name).one_or_none()
    if not exists:
        uid4 = _allocate_school_uid4(db)
        db.add(School(SchoolName=name, UID4=uid4))
        db.commit()

    return RedirectResponse(url="/admin/schools", status_code=303)
