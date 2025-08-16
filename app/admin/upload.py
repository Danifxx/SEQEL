from fastapi import APIRouter, Request, UploadFile, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from io import TextIOWrapper
import csv

from ..db import get_db, School, Student
from ..utils import allocate_uid4  # helper that returns a free 4-digit UID

router = APIRouter()

@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "admin_upload.html",
        {"request": request}
    )

@router.post("/upload")
async def upload_csv(
    request: Request,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    created_schools = 0
    created_students = 0

    # Read CSV (tolerate UTF-8 BOM)
    text = TextIOWrapper(file.file, encoding="utf-8-sig")
    reader = csv.DictReader(text)

    # Map case-insensitive headers
    header_map = { (h or "").lower(): (h or "") for h in (reader.fieldnames or []) }
    def cell(row, key):
        # look up original-cased header from our lower-case map
        source_key = header_map.get(key.lower(), key)
        return (row.get(source_key) or "").strip()

    for row in reader:
        first = cell(row, "first_name")
        last = cell(row, "last_name")
        school_name = cell(row, "school")
        cohort = cell(row, "cohort") or cell(row, "cohurt")
        year = cell(row, "year") or cell(row, "yearlevel")  # optional

        if not (first and last and school_name and cohort):
            # skip incomplete lines
            continue

        # ---- upsert School with auto UID4 ----
        school = db.query(School).filter(School.SchoolName == school_name).one_or_none()
        if not school:
            taken_school_uids = {
                s.UID4 for s in db.query(School.UID4).all() if s.UID4 is not None
            }
            # reserve 1000..1999 if you want that block for other purposes
            school_uid = allocate_uid4(db, taken_school_uids, avoid_range=(1000, 1999))
            school = School(SchoolName=school_name, UID4=school_uid)
            db.add(school)
            db.flush()  # get SchoolID for the student row
            created_schools += 1

        # ---- create Student with auto UID4 ----
        taken_student_uids = {
            s.UID4 for s in db.query(Student.UID4).all() if s.UID4 is not None
        }
        student_uid = allocate_uid4(db, taken_student_uids, avoid_range=(1000, 2000))
        # normalize cohort label a bit
        cohort_norm = cohort.title()  # e.g., "High" / "Primary"

        student = Student(
            UID4=student_uid,
            FirstName=first,
            LastName=last,
            SchoolID=school.SchoolID,
            Cohort=cohort_norm,
            YearLevel=year or None,
        )
        db.add(student)
        created_students += 1

    db.commit()
    # After upload, send users to Students so they can see results
    return RedirectResponse(url="/admin/students", status_code=303)
