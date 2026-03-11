#!/usr/bin/env python3
"""
Pull Request Review Mode
=========================
Review a GitHub pull request and optionally post the results as a comment.

Usage:
    python review_pr.py --repo owner/repo --pr 42
    python review_pr.py --repo owner/repo --pr 42 --post-comment
"""

import argparse
import sys
import os
from datetime import datetime

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

from tools.github_integration import GitHubIntegration


def parse_args():
    parser = argparse.ArgumentParser(description="Review a GitHub Pull Request")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="PR number")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the review as a PR comment (requires GITHUB_TOKEN)",
    )
    parser.add_argument("--output", type=str, default=None, help="Save report to file")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    gh = GitHubIntegration()

    print(f"📋 Fetching PR #{args.pr} from {args.repo}...")
    try:
        files = gh.get_pr_files(args.repo, args.pr)
    except Exception as e:
        print(f"❌ Failed to fetch PR: {e}")
        sys.exit(1)

    if not files:
        print("⚠️  No changed files in this PR.")
        sys.exit(0)

    print(f"   Changed files: {len(files)}")

    # Build code context from PR diff patches
    frontend_blocks = []
    backend_blocks = []

    for f in files:
        ext = os.path.splitext(f["filename"])[1].lower()
        block = f"### File: `{f['filename']}` ({f['status']})\n```\n{f['patch']}\n```"

        if ext in {".js", ".jsx", ".ts", ".tsx"}:
            frontend_blocks.append(block)
        elif ext == ".cs":
            backend_blocks.append(block)

    file_tree = "\n".join(
        f"  {'M' if f['status']=='modified' else f['status'][0].upper()} {f['filename']} "
        f"(+{f['additions']}/-{f['deletions']})"
        for f in files
    )

    context = {
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
            "total_lines": sum(f["additions"] + f["deletions"] for f in files),
        },
    }

    # Build agents and tasks
    agents_list = []
    tasks = []

    if frontend_blocks:
        fe = create_frontend_reviewer()
        agents_list.append(fe)
        tasks.append(create_frontend_review_task(fe, context))

    if backend_blocks:
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

    # Aggregation
    tasks.append(create_aggregation_task(qa, context))

    crew = Crew(
        agents=agents_list,
        tasks=tasks,
        process=Process.sequential,
        verbose=args.verbose,
    )

    print("🚀 Running PR review...")
    result = crew.kickoff()
    report = str(result)

    # Wrap with PR metadata
    header = (
        f"# 🔍 Automated PR Review: {args.repo}#{args.pr}\n\n"
        f"**Generated:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n---\n\n"
    )
    full_report = header + report

    # Save to file
    output_path = args.output or f"pr_review_{args.repo.replace('/', '_')}_#{args.pr}.md"
    with open(output_path, "w") as f:
        f.write(full_report)
    print(f"✅ Report saved to: {output_path}")

    # Optionally post as PR comment
    if args.post_comment:
        try:
            # Truncate for GitHub comment limit (~65K chars)
            comment_body = full_report[:60_000]
            if len(full_report) > 60_000:
                comment_body += "\n\n*...report truncated for GitHub comment limit...*"

            gh.post_review_comment(args.repo, args.pr, comment_body)
            print("💬 Review posted as PR comment.")
        except Exception as e:
            print(f"⚠️  Failed to post comment: {e}")


if __name__ == "__main__":
    main()
