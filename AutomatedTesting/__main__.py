"""CLI entry point: python -m AutomatedTesting --url <URL>"""

from __future__ import annotations

import asyncio
import json
import sys

import click

from config.logging import setup_logging
#from AutomatedTesting.config.log_setup import setup_logging
from config.settings import OutputFormat, Settings
from pipeline import run_pipeline


@click.command()
@click.option("--url", required=True, help="Target website URL to test")
@click.option("--depth", default=3, help="Max crawl depth (1-10)")
@click.option("--output", "fmt", default="json", type=click.Choice(["json", "csv", "excel", "html"]))
@click.option("--output-dir", default="output", help="Directory for output files")
@click.option("--security/--no-security", default=False, help="Include security test cases")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--scripts/--no-scripts", "gen_scripts", default=True, help="Generate automation scripts")
@click.option("--rate-limit", default=2.0, help="Requests per second")
def main(url, depth, fmt, output_dir, security, headless, gen_scripts, rate_limit):
    """Crawl a website and generate comprehensive test cases."""
    logger = setup_logging()
    logger.info("Starting AutoTester for: %s", url)

    settings = Settings(
        target_url=url,
        max_depth=depth,
        output_format=OutputFormat(fmt),
        output_dir=output_dir,
        run_security_tests=security,
        headless=headless,
        generate_scripts=gen_scripts,
        rate_limit_rps=rate_limit,
    )

    results = asyncio.run(run_pipeline(settings))

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Pages crawled:    {results['pages_crawled']}")
    print(f"Broken links:     {results['broken_links']}")
    print(f"Forms found:      {results['total_forms']}")
    print(f"API endpoints:    {results['total_api_endpoints']}")
    print(f"Test cases:       {results['test_cases']}")
    print(f"  Breakdown:      {results['summary']}")
    print(f"\nOutputs:")
    for o in results["outputs"]:
        print(f"  - {o}")
    print("=" * 60)


if __name__ == "__main__":
    main()
