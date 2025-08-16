from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db, Setting

router = APIRouter()

def get_setting(db: Session, key: str, default: str = "") -> str:
    s = db.get(Setting, key)
    return s.Value if s else default

def set_setting(db: Session, key: str, value: str) -> None:
    s = db.get(Setting, key)
    if s:
        s.Value = value
    else:
        s = Setting(Key=key, Value=value)
        db.add(s)
    db.commit()

@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
):
    sponsor = get_setting(db, "SponsorPath", "D:\\SEQEL\\Sponsors")
    pin_logger = get_setting(db, "PIN_Logger", "0000")
    pin_admin = get_setting(db, "PIN_Admin", "9999")
    drone = get_setting(db, "DRONE_TIMELAP_BONUS", "Yes")
    return request.app.state.templates.TemplateResponse(
        "admin_settings.html",
        {
            "request": request,
            "sponsor": sponsor,
            "pin_logger": pin_logger,
            "pin_admin": pin_admin,
            "drone": drone,
        },
    )

@router.post("/settings")
def settings_save(
    SponsorPath: str = Form(...),
    PIN_Logger: str = Form(...),
    PIN_Admin: str = Form(...),
    DRONE_TIMELAP_BONUS: str = Form(...),
    db: Session = Depends(get_db),
):
    set_setting(db, "SponsorPath", SponsorPath.strip())
    set_setting(db, "PIN_Logger", PIN_Logger.strip())
    set_setting(db, "PIN_Admin", PIN_Admin.strip())
    set_setting(db, "DRONE_TIMELAP_BONUS", DRONE_TIMELAP_BONUS.strip())
    return RedirectResponse(url="/admin/settings", status_code=303)
