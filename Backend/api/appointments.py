from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import Appointment, AppointmentStatus

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


def _parse_time_hhmm(s: str) -> None:
    # validate "HH:MM"
    try:
        datetime.strptime(s, "%H:%M")
    except Exception:
        raise ValueError("Invalid time format. Use HH:MM.")


def _validate_not_past(appt_date: date, appt_time: str) -> None:
    _parse_time_hhmm(appt_time)
    dt = datetime.strptime(f"{appt_date.isoformat()} {appt_time}", "%Y-%m-%d %H:%M")
    if dt < datetime.now():
        raise ValueError("Appointment date/time must be in the future.")


class AppointmentCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=6, max_length=50)
    email: Optional[str] = Field(default=None, max_length=200)
    reason: str = Field(min_length=1, max_length=5000)
    doctor: Optional[str] = Field(default=None, max_length=200)
    appointment_date: date
    appointment_time: str = Field(min_length=4, max_length=10)  # HH:MM


class AppointmentReschedule(BaseModel):
    appointment_date: date
    appointment_time: str = Field(min_length=4, max_length=10)


class AppointmentOut(BaseModel):
    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    reason: str
    doctor: Optional[str] = None
    appointment_date: str
    appointment_time: str
    status: str
    booking_timestamp: str

    @staticmethod
    def from_model(a: Appointment) -> "AppointmentOut":
        return AppointmentOut(
            id=a.id,
            full_name=a.full_name,
            phone=a.phone,
            email=a.email,
            reason=a.reason,
            doctor=a.doctor,
            appointment_date=a.appointment_date.isoformat(),
            appointment_time=a.appointment_time,
            status=a.status.value if hasattr(a.status, "value") else str(a.status),
            booking_timestamp=a.booking_timestamp.isoformat(),
        )


@router.post("", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)) -> AppointmentOut:
    try:
        _validate_not_past(payload.appointment_date, payload.appointment_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    appt = Appointment(
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip(),
        email=payload.email.strip() if payload.email else None,
        reason=payload.reason.strip(),
        doctor=payload.doctor.strip() if payload.doctor else None,
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time,
        status=AppointmentStatus.Upcoming,
    )

    db.add(appt)
    db.commit()
    db.refresh(appt)
    return AppointmentOut.from_model(appt)


@router.get("", response_model=List[AppointmentOut])
def list_appointments(db: Session = Depends(get_db)) -> List[AppointmentOut]:
    rows = db.query(Appointment).order_by(desc(Appointment.booking_timestamp)).all()
    return [AppointmentOut.from_model(a) for a in rows]


@router.get("/upcoming", response_model=List[AppointmentOut])
def upcoming_appointments(db: Session = Depends(get_db)) -> List[AppointmentOut]:
    today = date.today()
    rows = (
        db.query(Appointment)
        .filter(Appointment.status == AppointmentStatus.Upcoming)
        .filter(Appointment.appointment_date >= today)
        .order_by(asc(Appointment.appointment_date), asc(Appointment.appointment_time))
        .all()
    )
    return [AppointmentOut.from_model(a) for a in rows]


@router.get("/history", response_model=List[AppointmentOut])
def appointment_history(db: Session = Depends(get_db)) -> List[AppointmentOut]:
    today = date.today()
    rows = (
        db.query(Appointment)
        .filter(
            or_(
                Appointment.status.in_([AppointmentStatus.Completed, AppointmentStatus.Cancelled]),
                Appointment.appointment_date < today,
            )
        )
        .order_by(desc(Appointment.appointment_date), desc(Appointment.appointment_time))
        .all()
    )
    return [AppointmentOut.from_model(a) for a in rows]


@router.patch("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(appointment_id: int, db: Session = Depends(get_db)) -> AppointmentOut:
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if appt.status == AppointmentStatus.Cancelled:
        return AppointmentOut.from_model(appt)

    appt.status = AppointmentStatus.Cancelled
    db.commit()
    db.refresh(appt)
    return AppointmentOut.from_model(appt)


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule(appointment_id: int, payload: AppointmentReschedule, db: Session = Depends(get_db)) -> AppointmentOut:
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if appt.status != AppointmentStatus.Upcoming:
        raise HTTPException(status_code=400, detail="Only upcoming appointments can be rescheduled.")

    try:
        _validate_not_past(payload.appointment_date, payload.appointment_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    appt.appointment_date = payload.appointment_date
    appt.appointment_time = payload.appointment_time
    db.commit()
    db.refresh(appt)
    return AppointmentOut.from_model(appt)

