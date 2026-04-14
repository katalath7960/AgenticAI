"""Pydantic v2 schemas for request/response payloads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AttendeeBase(BaseModel):
    sno: int
    first_name: str
    last_name: str
    email: EmailStr
    color: str
    event_name: str | None = None


class AttendeeCreate(AttendeeBase):
    pass


class AttendeeRead(AttendeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    barcode_path: str | None = None
    email_sent_at: datetime | None = None
    checked_in_at: datetime | None = None
    created_at: datetime


class ScanRequest(BaseModel):
    payload: str = Field(..., description="Decoded barcode/QR string")
    scanned_by: str = Field(default="staff", max_length=100)


class ScanResult(BaseModel):
    duplicate: bool
    already_checked_in: bool
    attendee: AttendeeRead | None = None
    message: str


class ImportSummary(BaseModel):
    imported: int
    updated: int
    skipped: int
    errors: list[str] = []


class StatsResponse(BaseModel):
    total: int
    pending: int
    sent: int
    checked_in: int
    scans_today: int
