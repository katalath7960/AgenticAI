#!/usr/bin/env python3
"""
Azure DevOps Pull Request Review
==================================
Review the latest (or a specific) PR from an Azure DevOps repository
and optionally post the results back as a PR comment.

Setup:
    export AZURE_DEVOPS_ORG=myorg
    export AZURE_DEVOPS_PROJECT=myproject
    export AZURE_DEVOPS_PAT=xxxxxxxxxxxxxxxxxxxxxxx
    export OPENAI_API_KEY=sk-...

Usage:
    # Review the latest active PR
    python review_ado_pr.py --repo MyApp

    # Review a specific PR by ID
    python review_ado_pr.py --repo MyApp --pr 1234

    # Review latest PR targeting a specific branch
    python review_ado_pr.py --repo MyApp --target-branch main

    # Review and post the report as a PR comment
    python review_ado_pr.py --repo MyApp --post-comment

    # Override org/project inline
    python review_ado_pr.py --repo MyApp --org contoso --project WebTeam
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env from this folder, then fall back to parent directory
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

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

from tools.azure_devops_integration import AzureDevOpsIntegration


def parse_args():
    parser = argparse.ArgumentParser(
        description="Review an Azure DevOps Pull Request with CrewAI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (can also be passed as flags):
  AZURE_DEVOPS_ORG       Organisation name
  AZURE_DEVOPS_PROJECT   Project name
  AZURE_DEVOPS_PAT       Personal Access Token (Code Read & Write scope)
  OPENAI_API_KEY         LLM provider key
        """,
    )

    parser.add_argument(
        "--repo", required=True, help="Azure DevOps Git repository name"
    )
    parser.add_argument(
        "--pr", type=int, default=None, help="PR number (default: latest active PR)"
    )
    parser.add_argument(
        "--org", type=str, default=None, help="Azure DevOps organisation (overrides env)"
    )
    parser.add_argument(
        "--project", type=str, default=None, help="Azure DevOps project (overrides env)"
    )
    parser.add_argument(
        "--target-branch",
        type=str,
        default=None,
        help="Filter latest PR by target branch (e.g., main, develop)",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the review as a PR comment thread",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Save report to a file"
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--max-files",
        type=int,
        default=50,
        help="Maximum number of changed files to review (default: 50)",
    )

    return parser.parse_args()


def build_code_context(files: list[dict]) -> dict:
    """
    Categorise the changed files into frontend / backend blocks and
    build the context dict expected by the task definitions.
    """
    frontend_blocks = []
    backend_blocks = []

    for f in files:
        ext = os.path.splitext(f["filename"])[1].lower()
        lang_map = {
            ".tsx": "tsx", ".ts": "typescript", ".jsx": "jsx",
            ".js": "javascript", ".cs": "csharp",
        }
        lang = lang_map.get(ext, "")
        block = (
            f"### File: `{f['filename']}` ({f['change_type']})\n"
            f"```{lang}\n{f['content']}\n```"
        )

        if ext in {".js", ".jsx", ".ts", ".tsx"}:
            frontend_blocks.append(block)
        elif ext == ".cs":
            backend_blocks.append(block)

    file_tree = "\n".join(
        f"  {f['change_type'].upper():8s} {f['filename']}"
        for f in files
    )

    return {
        "frontend_code": "\n\n".join(frontend_blocks) or "No frontend changes.",
        "backend_code": "\n\n".join(backend_blocks) or "No backend changes.",
        "all_code": "\n\n".join(frontend_blocks + backend_blocks) or "No reviewable changes.",
        "file_tree": file_tree,
        "stats": {
            "total_frontend_files": len(frontend_blocks),
            "total_backend_files": len(backend_blocks),
            "total_config_files": 0,
            "total_test_files": 0,
            "files_loaded": len(files),
            "total_lines": sum(f["content"].count("\n") for f in files),
        },
    }


def build_crew(context: dict, verbose: bool = False) -> Crew:
    """Wire up agents and tasks based on what changed."""
    agents_list = []
    tasks = []

    has_frontend = context["frontend_code"] != "No frontend changes."
    has_backend = context["backend_code"] != "No backend changes."

    if has_frontend:
        fe = create_frontend_reviewer()
        agents_list.append(fe)
        tasks.append(create_frontend_review_task(fe, context))

    if has_backend:
        be = create_backend_reviewer()
        agents_list.append(be)
        tasks.append(create_backend_review_task(be, context))

    sec = create_security_reviewer()
    agents_list.append(sec)
    tasks.append(create_security_review_task(sec, context))

    perf = create_performance_reviewer()
    agents_list.append(perf)
    tasks.append(create_performance_review_task(perf, context))

    qa = create_quality_auditor()
    agents_list.append(qa)
    tasks.append(create_quality_audit_task(qa, context))

    # Final aggregation
    tasks.append(create_aggregation_task(qa, context))

    return Crew(
        agents=agents_list,
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
    )


def main():
    args = parse_args()

    # ── Connect to Azure DevOps ─────────────────────────────
    try:
        ado = AzureDevOpsIntegration(
            org=args.org,
            project=args.project,
        )
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    # ── Resolve PR ──────────────────────────────────────────
    try:
        if args.pr:
            pr = ado.get_pr_by_id(args.repo, args.pr)
            print(f"📋 PR #{pr['pullRequestId']}: {pr['title']}")
        else:
            pr = ado.get_latest_pr(
                args.repo,
                status="active",
                target_branch=args.target_branch,
            )
            print(f"📋 Latest active PR #{pr['pullRequestId']}: {pr['title']}")
    except Exception as e:
        print(f"❌ Failed to fetch PR: {e}")
        sys.exit(1)

    pr_id = pr["pullRequestId"]
    pr_title = pr["title"]
    created_by = pr.get("createdBy", {}).get("displayName", "Unknown")
    source_branch = pr.get("sourceRefName", "").replace("refs/heads/", "")
    target_branch = pr.get("targetRefName", "").replace("refs/heads/", "")

    print(f"   Author:  {created_by}")
    print(f"   Branches: {source_branch} → {target_branch}")

    # ── Fetch changed files ─────────────────────────────────
    print(f"\n📂 Fetching changed files (max {args.max_files})...")
    try:
        files = ado.get_pr_file_contents(args.repo, pr_id, max_files=args.max_files)
    except Exception as e:
        print(f"❌ Failed to fetch file contents: {e}")
        sys.exit(1)

    if not files:
        print("⚠️  No reviewable changed files found in this PR.")
        sys.exit(0)

    reviewable = [
        f for f in files
        if os.path.splitext(f["filename"])[1].lower()
        in {".js", ".jsx", ".ts", ".tsx", ".cs"}
    ]

    print(f"   Total changed files: {len(files)}")
    print(f"   Reviewable (React + .NET): {len(reviewable)}")

    if not reviewable:
        print("⚠️  No React or .NET files changed. Nothing to review.")
        sys.exit(0)

    # ── Build context and run crew ──────────────────────────
    context = build_code_context(reviewable)

    print("\n🤖 Initializing review agents...")
    crew = build_crew(context, verbose=args.verbose)

    print("🚀 Starting code review...\n")
    result = crew.kickoff()
    report = str(result)

    # ── Build final report ──────────────────────────────────
    header = (
        f"# 🔍 Azure DevOps PR Review\n\n"
        f"| Field | Value |\n"
        f"|-------|-------|\n"
        f"| **Organisation** | {ado.org} |\n"
        f"| **Project** | {ado.project} |\n"
        f"| **Repository** | {args.repo} |\n"
        f"| **PR** | #{pr_id} – {pr_title} |\n"
        f"| **Author** | {created_by} |\n"
        f"| **Branches** | `{source_branch}` → `{target_branch}` |\n"
        f"| **Files reviewed** | {len(reviewable)} |\n"
        f"| **Generated** | {datetime.now():%Y-%m-%d %H:%M:%S} |\n\n"
        f"---\n\n"
    )
    full_report = header + report

    # ── Save report ─────────────────────────────────────────
    safe_repo = args.repo.replace("/", "_").replace(" ", "_")
    output_path = args.output or f"ado_pr_review_{safe_repo}_PR{pr_id}.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    print(f"\n✅ Report saved to: {output_path}")

    # ── Post comment to PR ──────────────────────────────────
    if args.post_comment:
        print("💬 Posting review to PR comment thread...")
        try:
            # Azure DevOps comments have a generous size limit (~150K),
            # but we truncate at 100K to be safe
            comment_body = full_report[:100_000]
            if len(full_report) > 100_000:
                comment_body += (
                    "\n\n*...report truncated — "
                    f"full report is {len(full_report):,} characters...*"
                )

            ado.post_pr_comment(args.repo, pr_id, comment_body)
            print("   ✅ Comment posted successfully.")
        except Exception as e:
            print(f"   ⚠️  Failed to post comment: {e}")

    return output_path


if __name__ == "__main__":
    main()
