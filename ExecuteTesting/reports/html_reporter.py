from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from excel_reader.models import TestCase
from utilities.logger import get_logger
from utilities.time_utils import ms_to_human, now_str

log = get_logger(test="HTMLReporter")

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html(run_meta: dict, test_cases: List[TestCase], output_folder: str) -> str:
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("report_template.html")

    flaky_ids = [tc.tc_id for tc in test_cases if tc.is_flaky]

    html = template.render(run=run_meta, test_cases=test_cases, flaky_ids=flaky_ids)

    filename = f"report_{run_meta['run_id']}.html"
    out_path = str(Path(output_folder) / filename)
    Path(out_path).write_text(html, encoding="utf-8")
    log.info(f"HTML report: {out_path}")
    return out_path
