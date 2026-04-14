"""CSV → DB importer. Upserts attendees keyed on email.

Usage:
    python -m api.import_csv --csv data/input/WFHAttendees.csv
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models import Attendee
from api.schemas import ImportSummary

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

REQUIRED_COLUMNS = {"Sno", "FirstName", "LastName", "Color", "EmailAddress", "EventName"}


def import_attendees(csv_path: str | Path, db: Session) -> ImportSummary:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    imported = updated = skipped = 0
    errors: list[str] = []
    seen_emails: set[str] = set()

    for idx, row in df.iterrows():
        row_num = idx + 2  # +1 for header, +1 for 1-based
        try:
            email = row["EmailAddress"].strip().lower()
            if not email:
                skipped += 1
                errors.append(f"row {row_num}: blank email")
                continue
            if email in seen_emails:
                skipped += 1
                errors.append(f"row {row_num}: duplicate email in CSV ({email})")
                continue
            seen_emails.add(email)

            sno = int(row["Sno"])
            first_name = row["FirstName"].strip().title()
            last_name = row["LastName"].strip().title()
            color = row["Color"].strip().title()
            event_name = row["EventName"].strip()

            existing = db.query(Attendee).filter(Attendee.email == email).one_or_none()
            if existing is None:
                db.add(Attendee(
                    sno=sno,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    color=color,
                    event_name=event_name,
                    status="Pending",
                ))
                imported += 1
            else:
                existing.sno = sno
                existing.first_name = first_name
                existing.last_name = last_name
                existing.color = color
                existing.event_name = event_name
                updated += 1
        except Exception as exc:  # per-row resilience
            skipped += 1
            errors.append(f"row {row_num}: {exc}")

    db.commit()
    return ImportSummary(imported=imported, updated=updated, skipped=skipped, errors=errors)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import attendees from CSV into the DB.")
    parser.add_argument(
        "--csv",
        default=os.getenv("INPUT_CSV", "data/input/WFHAttendees.csv"),
        help="Path to the attendees CSV",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        summary = import_attendees(args.csv, db)
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
