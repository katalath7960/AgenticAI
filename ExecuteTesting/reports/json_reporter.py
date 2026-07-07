import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from excel_reader.models import TestCase
from utilities.logger import get_logger

log = get_logger(test="JSONReporter")


def generate_json(run_meta: dict, test_cases: List[TestCase], output_folder: str) -> str:
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    filename = f"report_{run_meta['run_id']}.json"
    out_path = str(Path(output_folder) / filename)

    payload = {
        **run_meta,
        "test_cases": [asdict(tc) for tc in test_cases],
    }

    Path(out_path).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info(f"JSON report: {out_path}")
    return out_path
