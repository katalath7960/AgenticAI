"""Pytest fixtures: isolated test DB per test."""

from __future__ import annotations

import os
from pathlib import Path

# Point at an isolated test DB *before* importing api.database
TEST_DB = Path(__file__).parent / "_test_wfh.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["BARCODE_OUTPUT_DIR"] = str(Path(__file__).parent / "_barcodes")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "x")

import pytest

from api.database import Base, SessionLocal, engine


@pytest.fixture(autouse=True)
def _clean_db():
    """Drop + recreate all tables before every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def sample_csv(tmp_path) -> Path:
    csv = tmp_path / "attendees.csv"
    csv.write_text(
        "Sno,FirstName,LastName,Color,EmailAddress,Status,EventName\n"
        "1,Alice,Anderson,Blue,alice@example.com,,WFH Test\n"
        "2,Bob,Brown,Red,bob@example.com,,WFH Test\n"
        "3,Carol,Cole,Green,carol@example.com,,WFH Test\n"
    )
    return csv


@pytest.fixture()
def bad_csv(tmp_path) -> Path:
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "Sno,FirstName,LastName,Color,EmailAddress,Status,EventName\n"
        "1,Alice,Anderson,Blue,,,WFH Test\n"            # blank email
        "2,Bob,Brown,Red,bob@example.com,,WFH Test\n"
        "3,Duplicate,Row,Red,bob@example.com,,WFH Test\n"  # duplicate email
    )
    return csv


@pytest.fixture()
def barcode_dir(tmp_path) -> Path:
    d = tmp_path / "barcodes"
    d.mkdir()
    return d
