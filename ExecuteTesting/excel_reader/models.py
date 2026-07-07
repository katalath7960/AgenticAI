from dataclasses import dataclass, field
from typing import List


@dataclass
class TestCase:
    file_path: str
    sheet_name: str
    row_index: int              # 1-based row number in sheet (including header)
    tc_id: str
    test_case_name: str
    preconditions: str
    steps: str
    expected_result: str

    # Populated after execution
    status: str = "NOT RUN"     # PASS | FAIL | SKIP | NOT RUN
    actual_result: str = ""
    error_message: str = ""
    screenshot_path: str = ""
    console_errors: List[str] = field(default_factory=list)
    html_snapshot_path: str = ""
    execution_time_ms: int = 0
    failure_analysis: str = ""
    is_flaky: bool = False
