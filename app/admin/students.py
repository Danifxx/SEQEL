from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import get_db, Student, School
from ..utils import allocate_uid4

router = APIRouter()

@router.get("/students", response_class=HTMLResponse)
def students_page(
    request: Request,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    # base query (join so we can filter by school name)
    query = db.query(Student).join(School)

    if q:
        qlike = f"%{q.strip()}%"
        # NOTE: .ilike is supported by most dialects; on SQLite LIKE is already case-insensitive
        query = query.filter(
            (Student.FirstName.ilike(qlike)) |
            (Student.LastName.ilike(qlike))  |
            (School.SchoolName.ilike(qlike))
        )

    rows = query.order_by(Student.UID4).all()
    schools = db.query(School).order_by(School.SchoolName).all()

    return request.app.state.templates.TemplateResponse(
        "admin_students.html",
        {"request": request, "students": rows, "schools": schools, "q": q or ""}
    )

@router.post("/students/add")
def students_add(
    FirstName: str = Form(...),
    LastName: str  = Form(...),
    SchoolID: int  = Form(...),
    Cohort: str    = Form(...),
    YearLevel: str | None = Form(None),   # optional year field
    db: Session = Depends(get_db),
):
    # ensure school exists
    school = db.get(School, int(SchoolID))
    if not school:
        return RedirectResponse(url="/admin/students", status_code=303)

    # allocate a unique 4-digit UID, avoiding 1000..1999 if you reserve those
    taken = {s.UID4 for s in db.query(Student.UID4).all() if s.UID4 is not None}
    uid4 = allocate_uid4(db, taken, avoid_range=(1000, 2000))
    if uid4 is None:
        # pool exhausted; redirect back gracefully
        return RedirectResponse(url="/admin/students?q=UID+pool+exhausted", status_code=303)

    st = Student(
        UID4=uid4,
        FirstName=FirstName.strip(),
        LastName=LastName.strip(),
        SchoolID=int(SchoolID),
        Cohort=Cohort.strip(),
        YearLevel=(YearLevel.strip() if YearLevel else None),
    )
    db.add(st)
    db.commit()
    return RedirectResponse(url="/admin/students", status_code=303)
