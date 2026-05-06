import enum
from datetime import datetime

from sqlalchemy import Date, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.db import Base


class AppointmentStatus(str, enum.Enum):
    Upcoming = "Upcoming"
    Completed = "Completed"
    Cancelled = "Cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User details
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Appointment details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    doctor: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    appointment_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    appointment_time: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # "HH:MM"

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.Upcoming,
        nullable=False,
        index=True,
    )

    booking_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

