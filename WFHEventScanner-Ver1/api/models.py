"""SQLAlchemy ORM models: Attendee + ScanLog."""

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, func,
)
from sqlalchemy.orm import relationship

from api.database import Base


class Attendee(Base):
    __tablename__ = "attendees"

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sno            = Column(Integer, unique=True, index=True)
    first_name     = Column(String(100))
    last_name      = Column(String(100))
    email          = Column(String(200), unique=True, index=True, nullable=False)
    color          = Column(String(50))
    event_name     = Column(String(200))
    status         = Column(String(50), default="Pending", nullable=False)
    barcode_path   = Column(String(500), nullable=True)
    email_sent_at  = Column(DateTime, nullable=True)
    checked_in_at  = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, server_default=func.now(), nullable=False)

    scan_logs = relationship(
        "ScanLog", back_populates="attendee", cascade="all, delete-orphan"
    )


class ScanLog(Base):
    __tablename__ = "scan_log"

    id           = Column(Integer, primary_key=True, index=True, autoincrement=True)
    attendee_id  = Column(Integer, ForeignKey("attendees.id"), index=True, nullable=False)
    scanned_at   = Column(DateTime, server_default=func.now(), nullable=False)
    scanned_by   = Column(String(100))
    is_duplicate = Column(Boolean, default=False, nullable=False)

    attendee = relationship("Attendee", back_populates="scan_logs")
