#!/usr/bin/env python3
"""
CrewAI Code Review Agent
========================
Automated code review system for React frontend and .NET Core backend projects.
Analyzes code quality, security, performance, and best practices.

Usage:
    python main.py --path /path/to/project
    python main.py --path /path/to/project --output report.md
    python main.py --github owner/repo --branch main
"""

import argparse
import sys
import os
import json
from datetime import datetime
from pathlib import Path

from crewai import Crew, Process

from agents.frontend_reviewer import create_frontend_reviewer
from agents.backend_reviewer import create_backend_reviewer
from agents.security_reviewer import create_security_reviewer
from agents.performance_reviewer import create_performance_reviewer
from agents.quality_auditor import create_quality_auditor

from tasks.review_tasks import (
    create_frontend_review_task,
    create_backend_review_task,
    create_security_review_task,
    create_performance_review_task,
    create_quality_audit_task,
    create_aggregation_task,
)

from tools.file_scanner import ProjectScanner
from tools.code_analyzer import CodeAnalyzer
from tools.github_integration import GitHubIntegration
from utils.report_generator import ReportGenerator


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="CrewAI Code Review Agent for React & .NET Core projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --path ./my-project
  %(prog)s --path ./my-project --output review-report.md
  %(prog)s --github owner/repo --branch main
  %(prog)s --path ./my-project --verbose
        """,
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--path", type=str, help="Local path to the project directory"
    )
    source_group.add_argument(
        "--github", type=str, help="GitHub repository (format: owner/repo)"
    )

    parser.add_argument(
        "--branch", type=str, default="main", help="Git branch to review (default: main)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output report file path (default: review_report_<timestamp>.md)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=50,
        help="Maximum number of files to review (default: 50)",
    )
    parser.add_argument(
        "--focus",
        nargs="+",
        choices=["frontend", "backend", "security", "performance", "quality"],
        default=["frontend", "backend", "security", "performance", "quality"],
        help="Focus areas for review (default: all)",
    )

    return parser.parse_args()


def load_project_files(
    project_path: str, max_files: int = 50
) -> dict:
    """Scan and load project files."""
    scanner = ProjectScanner(project_path)
    file_manifest = scanner.scan()

    print(f"\n📁 Project scanned: {project_path}")
    print(f"   React files found:   {len(file_manifest['frontend_files'])}")
    print(f"   .NET files found:    {len(file_manifest['backend_files'])}")
    print(f"   Config files found:  {len(file_manifest['config_files'])}")

    # Load file contents (respecting max_files limit)
    analyzer = CodeAnalyzer()
    loaded = analyzer.load_files(file_manifest, max_files=max_files)

    print(f"   Total files loaded:  {len(loaded['all_files'])}")
    return loaded


def load_github_repo(
    repo: str, branch: str, max_files: int = 50
) -> dict:
    """Clone and load a GitHub repository."""
    gh = GitHubIntegration()
    project_path = gh.clone_repo(repo, branch)
    return load_project_files(project_path, max_files)


def build_crew(
    loaded_files: dict,
    focus_areas: list[str],
    verbose: bool = False,
) -> Crew:
    """Build the CrewAI crew with agents and tasks."""

    # ── Agents ──────────────────────────────────────────────
    agents = {}
    if "frontend" in focus_areas:
        agents["frontend"] = create_frontend_reviewer()
    if "backend" in focus_areas:
        agents["backend"] = create_backend_reviewer()
    if "security" in focus_areas:
        agents["security"] = create_security_reviewer()
    if "performance" in focus_areas:
        agents["performance"] = create_performance_reviewer()
    if "quality" in focus_areas:
        agents["quality"] = create_quality_auditor()

    # ── Shared context ──────────────────────────────────────
    code_context = {
        "frontend_code": loaded_files.get("frontend_code", "No frontend files found."),
        "backend_code": loaded_files.get("backend_code", "No backend files found."),
        "all_code": loaded_files.get("all_code", "No files found."),
        "file_tree": loaded_files.get("file_tree", ""),
        "stats": loaded_files.get("stats", {}),
    }

    # ── Tasks ───────────────────────────────────────────────
    tasks = []
    if "frontend" in focus_areas and agents.get("frontend"):
        tasks.append(
            create_frontend_review_task(agents["frontend"], code_context)
        )
    if "backend" in focus_areas and agents.get("backend"):
        tasks.append(
            create_backend_review_task(agents["backend"], code_context)
        )
    if "security" in focus_areas and agents.get("security"):
        tasks.append(
            create_security_review_task(agents["security"], code_context)
        )
    if "performance" in focus_areas and agents.get("performance"):
        tasks.append(
            create_performance_review_task(agents["performance"], code_context)
        )
    if "quality" in focus_areas and agents.get("quality"):
        tasks.append(
            create_quality_audit_task(agents["quality"], code_context)
        )

    # Aggregation task – uses the quality auditor (or first available agent)
    aggregator_agent = agents.get("quality") or list(agents.values())[0]
    tasks.append(create_aggregation_task(aggregator_agent, code_context))

    # ── Crew ────────────────────────────────────────────────
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
        max_rpm=10,
        memory=True,
    )

    return crew


def main():
    """Main entry point."""
    args = parse_arguments()

    print("=" * 60)
    print("🔍 CrewAI Code Review Agent")
    print("=" * 60)
    print(f"   Timestamp:    {datetime.now().isoformat()}")
    print(f"   Focus areas:  {', '.join(args.focus)}")
    print()

    # ── Load project files ──────────────────────────────────
    try:
        if args.path:
            project_path = os.path.abspath(args.path)
            if not os.path.isdir(project_path):
                print(f"❌ Error: Directory not found: {project_path}")
                sys.exit(1)
            loaded_files = load_project_files(project_path, args.max_files)
        else:
            loaded_files = load_github_repo(args.github, args.branch, args.max_files)
    except Exception as e:
        print(f"❌ Error loading project: {e}")
        sys.exit(1)

    if not loaded_files["all_files"]:
        print("⚠️  No reviewable files found. Exiting.")
        sys.exit(0)

    # ── Build and run crew ──────────────────────────────────
    print("\n🤖 Initializing review agents...")
    crew = build_crew(loaded_files, args.focus, args.verbose)

    print("🚀 Starting code review...\n")
    result = crew.kickoff()

    # ── Generate report ─────────────────────────────────────
    output_path = args.output or f"review_report_{datetime.now():%Y%m%d_%H%M%S}.md"

    generator = ReportGenerator()
    report = generator.generate(
        crew_output=str(result),
        stats=loaded_files.get("stats", {}),
        focus_areas=args.focus,
        project_path=args.path or args.github,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Review complete! Report saved to: {output_path}")
    print(f"   Total files reviewed: {len(loaded_files['all_files'])}")

    return output_path


if __name__ == "__main__":
    main()
