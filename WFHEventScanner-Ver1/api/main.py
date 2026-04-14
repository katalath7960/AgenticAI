"""FastAPI app — WFH Event Scanner API."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Attendee, ScanLog
from api.routers import agent, attendees, scanner
from api.schemas import StatsResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] [%(request_id)s] %(message)s",
)


class _RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


for h in logging.getLogger().handlers:
    h.addFilter(_RequestIDFilter())

logger = logging.getLogger("api")


app = FastAPI(title="WFH Event Scanner API", version="0.1.0")

cors_origins = [
    "http://localhost:5173",   # Vite/React
    "http://localhost:8501",   # Streamlit
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    logger.info("→ %s %s", request.method, request.url.path, extra={"request_id": request_id})
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    rid = getattr(request.state, "request_id", "-")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "request_id": rid},
        headers={"X-Request-ID": rid},
    )


@app.exception_handler(RequestValidationError)
async def validation_exc_handler(request: Request, exc: RequestValidationError):
    rid = getattr(request.state, "request_id", "-")
    return JSONResponse(
        status_code=422,
        content={"error": "validation error", "details": exc.errors(), "request_id": rid},
    )


@app.exception_handler(SQLAlchemyError)
async def db_exc_handler(request: Request, exc: SQLAlchemyError):
    rid = getattr(request.state, "request_id", "-")
    logger.exception("db error", extra={"request_id": rid})
    return JSONResponse(
        status_code=500,
        content={"error": "database error", "request_id": rid},
    )


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    rid = getattr(request.state, "request_id", "-")
    logger.exception("unhandled error", extra={"request_id": rid})
    return JSONResponse(
        status_code=500,
        content={"error": "internal server error", "request_id": rid},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats", response_model=StatsResponse, tags=["stats"])
def stats(db: Session = Depends(get_db)):
    today_start = datetime.combine(date.today(), datetime.min.time())
    total = db.query(Attendee).count()
    pending = db.query(Attendee).filter(Attendee.status == "Pending").count()
    sent = db.query(Attendee).filter(Attendee.status == "Sent").count()
    checked_in = db.query(Attendee).filter(Attendee.status == "CheckedIn").count()
    scans_today = db.query(ScanLog).filter(ScanLog.scanned_at >= today_start).count()
    return StatsResponse(
        total=total, pending=pending, sent=sent,
        checked_in=checked_in, scans_today=scans_today,
    )


app.include_router(attendees.router)
app.include_router(scanner.router)
app.include_router(agent.router)
