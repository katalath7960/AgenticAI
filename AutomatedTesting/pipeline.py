"""Main pipeline — crawl → analyze → generate → export."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from analyzer.analyzer import analyze_site
from analyzer.diff import detect_changes, save_baseline
from config.settings import OutputFormat, Settings
from crawler.crawler import crawl
from generator.generator import generate_test_suite
from generator.models import TestSuite
from output.exporters.excel_export import export_csv, export_excel
from output.exporters.html_report import export_html
from output.exporters.jira_export import export_jira_csv, export_testrail_xml
from output.exporters.json_export import export_json
from scripts.api.gen_api_tests import generate_api_tests
from scripts.ci_template import generate_ci_config
from scripts.playwright.gen_playwright import generate_playwright_scripts

log = logging.getLogger("autotester")


async def run_pipeline(settings: Settings) -> dict:
    output_dir = Path(settings.output_dir)
    results: dict = {"outputs": []}

    # Phase 2 — Crawl
    log.info("=== Phase 2: Crawling %s ===", settings.target_url)
    site_map = await crawl(settings)
    results["pages_crawled"] = len(site_map.pages)
    results["broken_links"] = len(site_map.broken_links)

    # Phase 7.2 — Diff against baseline
    baseline_path = output_dir / "baseline.json"
    changes = detect_changes(site_map.pages, baseline_path)
    if changes:
        log.info("UI changes detected: %s", changes)
        results["ui_changes"] = changes
    save_baseline(site_map.pages, baseline_path)

    # Phase 3 — Analyze
    log.info("=== Phase 3: Analyzing site structure ===")
    analysis = analyze_site(site_map, api_key=settings.openai_api_key, ai_model=settings.ai_model.value)
    results["total_forms"] = analysis.total_forms
    results["total_api_endpoints"] = analysis.total_api_endpoints

    # Phase 4 — Generate test cases
    log.info("=== Phase 4: Generating test cases ===")
    suite = generate_test_suite(
        analysis,
        api_key=settings.openai_api_key,
        ai_model=settings.ai_model.value,
        include_security=settings.run_security_tests,
    )
    results["test_cases"] = len(suite.test_cases)
    results["summary"] = suite.summary

    # Phase 5 — Export
    log.info("=== Phase 5: Exporting results ===")
    json_path = export_json(suite, output_dir)
    results["outputs"].append(str(json_path))

    if settings.output_format in (OutputFormat.EXCEL, OutputFormat.CSV):
        excel_path = export_excel(suite, output_dir)
        csv_path = export_csv(suite, output_dir)
        results["outputs"].extend([str(excel_path), str(csv_path)])

    html_path = export_html(suite, output_dir)
    results["outputs"].append(str(html_path))

    jira_path = export_jira_csv(suite, output_dir)
    testrail_path = export_testrail_xml(suite, output_dir)
    results["outputs"].extend([str(jira_path), str(testrail_path)])

    # Phase 6 — Generate scripts
    if settings.generate_scripts:
        log.info("=== Phase 6: Generating automation scripts ===")
        pw_dir = output_dir / "generated_tests" / "playwright"
        pw_files = generate_playwright_scripts(suite, pw_dir)
        results["outputs"].extend([str(f) for f in pw_files])

        api_dir = output_dir / "generated_tests" / "api"
        api_file = generate_api_tests(analysis, api_dir)
        if api_file:
            results["outputs"].append(str(api_file))

        ci_path = generate_ci_config(output_dir)
        results["outputs"].append(str(ci_path))

    log.info("=== Pipeline complete ===")
    log.info("Results: %s", results["summary"])
    log.info("Outputs saved to: %s", output_dir)
    return results
