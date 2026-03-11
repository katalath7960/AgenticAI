"""
GitHub Integration
===================
Clone repositories and support pull-request review workflows.
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional


class GitHubIntegration:
    """
    Provides GitHub repository cloning and pull-request utilities.

    Environment variables:
        GITHUB_TOKEN – Personal access token for private repos (optional)
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._temp_dirs: list[str] = []

    def clone_repo(self, repo: str, branch: str = "main") -> str:
        """
        Clone a GitHub repository to a temporary directory.

        Args:
            repo: Repository in "owner/repo" format
            branch: Branch name to clone

        Returns:
            Absolute path to the cloned directory
        """
        tmp = tempfile.mkdtemp(prefix="crewai_review_")
        self._temp_dirs.append(tmp)

        if self.token:
            url = f"https://{self.token}@github.com/{repo}.git"
        else:
            url = f"https://github.com/{repo}.git"

        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            branch,
            url,
            tmp,
        ]

        print(f"📥 Cloning {repo} (branch: {branch})...")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"git clone failed:\n{result.stderr.strip()}"
            )

        print(f"   Cloned to: {tmp}")
        return tmp

    def get_pr_diff(self, repo: str, pr_number: int) -> str:
        """
        Fetch the diff of a pull request using the GitHub API.

        Args:
            repo: Repository in "owner/repo" format
            pr_number: Pull request number

        Returns:
            The unified diff as a string
        """
        import urllib.request

        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "CrewAI-CodeReview",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")

    def get_pr_files(self, repo: str, pr_number: int) -> list[dict]:
        """
        Fetch the list of changed files in a pull request.

        Returns:
            List of dicts with keys: filename, status, additions,
            deletions, patch
        """
        import urllib.request

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CrewAI-CodeReview",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        return [
            {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "patch": f.get("patch", ""),
            }
            for f in data
        ]

    def post_review_comment(
        self,
        repo: str,
        pr_number: int,
        body: str,
    ) -> dict:
        """
        Post a review comment on a pull request.

        Args:
            repo: Repository in "owner/repo" format
            pr_number: Pull request number
            body: Comment body (Markdown)

        Returns:
            API response as a dict
        """
        import urllib.request

        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN is required to post review comments."
            )

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "CrewAI-CodeReview",
        }

        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        payload = json.dumps({"body": body}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def cleanup(self):
        """Remove temporary directories created during cloning."""
        import shutil

        for d in self._temp_dirs:
            shutil.rmtree(d, ignore_errors=True)
        self._temp_dirs.clear()
