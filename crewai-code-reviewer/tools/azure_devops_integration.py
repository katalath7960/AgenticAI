"""
Azure DevOps Integration
==========================
Clone repositories, fetch pull-request diffs, post review comments,
and retrieve the latest PR from Azure DevOps.

Authentication:
    Set the AZURE_DEVOPS_PAT environment variable to a Personal Access Token
    with at least **Code (Read & Write)** scope.

Azure DevOps REST API reference:
    https://learn.microsoft.com/en-us/rest/api/azure-devops/git/
"""

import os
import json
import base64
import subprocess
import tempfile
from typing import Optional
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import HTTPError


class AzureDevOpsIntegration:
    """
    Interact with Azure DevOps Git repositories and pull requests.

    Args:
        org:     Azure DevOps organisation name  (or set AZURE_DEVOPS_ORG)
        project: Azure DevOps project name        (or set AZURE_DEVOPS_PROJECT)
        pat:     Personal Access Token             (or set AZURE_DEVOPS_PAT)
    """

    API_VERSION = "7.1-preview.1"

    def __init__(
        self,
        org: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None,
    ):
        self.org = org or os.getenv("AZURE_DEVOPS_ORG", "")
        self.project = project or os.getenv("AZURE_DEVOPS_PROJECT", "")
        self.pat = pat or os.getenv("AZURE_DEVOPS_PAT", "")
        self._temp_dirs: list[str] = []

        if not self.org:
            raise ValueError(
                "Azure DevOps organisation is required. "
                "Pass org= or set AZURE_DEVOPS_ORG."
            )
        if not self.project:
            raise ValueError(
                "Azure DevOps project is required. "
                "Pass project= or set AZURE_DEVOPS_PROJECT."
            )
        if not self.pat:
            raise ValueError(
                "A Personal Access Token is required. "
                "Pass pat= or set AZURE_DEVOPS_PAT."
            )

    # ── URL helpers ─────────────────────────────────────────

    @property
    def _base_url(self) -> str:
        return (
            f"https://dev.azure.com/{quote(self.org)}"
            f"/{quote(self.project)}/_apis/git"
        )

    def _auth_header(self) -> dict:
        """Build the Basic-auth header from the PAT."""
        token_bytes = base64.b64encode(f":{self.pat}".encode()).decode()
        return {
            "Authorization": f"Basic {token_bytes}",
            "Content-Type": "application/json",
        }

    def _get(self, url: str) -> dict:
        """HTTP GET → parsed JSON."""
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}api-version={self.API_VERSION}"
        req = Request(full_url, headers=self._auth_header())
        try:
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    raise RuntimeError(
                        f"Non-JSON response from {full_url}:\n{raw[:500]}"
                    )
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Azure DevOps API error {e.code} on GET {full_url}:\n{body}"
            ) from e

    def _post(self, url: str, payload: dict) -> dict:
        """HTTP POST → parsed JSON."""
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}api-version={self.API_VERSION}"
        data = json.dumps(payload).encode("utf-8")
        req = Request(full_url, data=data, headers=self._auth_header(), method="POST")
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Azure DevOps API error {e.code} on POST {full_url}:\n{body}"
            ) from e

    # ── Repository operations ───────────────────────────────

    def list_repos(self) -> list[dict]:
        """Return all Git repositories in the project."""
        data = self._get(f"{self._base_url}/repositories")
        return [
            {"id": r["id"], "name": r["name"], "url": r["remoteUrl"]}
            for r in data.get("value", [])
        ]

    def clone_repo(self, repo_name: str, branch: str = "main") -> str:
        """
        Clone an Azure DevOps repo to a temp directory.

        Returns:
            Absolute path to the cloned directory.
        """
        tmp = tempfile.mkdtemp(prefix="crewai_ado_review_")
        self._temp_dirs.append(tmp)

        clone_url = (
            f"https://{self.pat}@dev.azure.com/"
            f"{quote(self.org)}/{quote(self.project)}/_git/{quote(repo_name)}"
        )

        cmd = ["git", "clone", "--depth", "1", "--branch", branch, clone_url, tmp]
        print(f"📥 Cloning {self.org}/{self.project}/{repo_name} (branch: {branch})...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            raise RuntimeError(f"git clone failed:\n{result.stderr.strip()}")

        print(f"   Cloned to: {tmp}")
        return tmp

    # ── Pull-request operations ─────────────────────────────

    def get_latest_pr(
        self,
        repo_name: str,
        status: str = "active",
        target_branch: Optional[str] = None,
    ) -> dict:
        """
        Get the most recent pull request for a repository.

        Args:
            repo_name:     Repository name
            status:        active | completed | abandoned | all
            target_branch: Filter by target branch (e.g. "refs/heads/main")

        Returns:
            dict with PR metadata (pullRequestId, title, createdBy, etc.)
        """
        url = (
            f"{self._base_url}/repositories/{quote(repo_name)}"
            f"/pullrequests?searchCriteria.status={status}"
            f"&$top=1&$orderby=createdDate%20desc"
        )
        if target_branch:
            ref = target_branch if target_branch.startswith("refs/") else f"refs/heads/{target_branch}"
            url += f"&searchCriteria.targetRefName={quote(ref)}"

        data = self._get(url)
        prs = data.get("value", [])
        if not prs:
            raise ValueError(
                f"No {status} pull requests found in {repo_name}"
                + (f" targeting {target_branch}" if target_branch else "")
            )
        return prs[0]

    def get_pr_by_id(self, repo_name: str, pr_id: int) -> dict:
        """Fetch a specific PR by its numeric ID."""
        url = f"{self._base_url}/repositories/{quote(repo_name)}/pullrequests/{pr_id}"
        return self._get(url)

    def get_pr_iterations(self, repo_name: str, pr_id: int) -> list[dict]:
        """
        Get PR iterations (each push to the source branch creates one).
        Useful for reviewing only the latest changes.
        """
        url = (
            f"{self._base_url}/repositories/{quote(repo_name)}"
            f"/pullrequests/{pr_id}/iterations"
        )
        data = self._get(url)
        return data.get("value", [])

    def get_pr_changes(self, repo_name: str, pr_id: int) -> list[dict]:
        """
        Get the list of changed files (and their change types) in a PR.

        Returns:
            List of dicts:
                filename, change_type (add/edit/delete), is_folder
        """
        # Get iterations to find the merge-base comparison
        iterations = self.get_pr_iterations(repo_name, pr_id)
        if not iterations:
            return []

        latest_iter = iterations[-1]["id"]
        url = (
            f"{self._base_url}/repositories/{quote(repo_name)}"
            f"/pullrequests/{pr_id}/iterations/{latest_iter}/changes"
        )
        data = self._get(url)

        changes = []
        for entry in data.get("changeEntries", []):
            item = entry.get("item", {})
            if item.get("isFolder", False):
                continue
            changes.append({
                "filename": item.get("path", "unknown"),
                "change_type": entry.get("changeType", "edit"),
                "original_path": entry.get("originalPath"),
            })

        return changes

    def get_file_content(
        self,
        repo_name: str,
        file_path: str,
        version: Optional[str] = None,
        version_type: str = "branch",
    ) -> str:
        """
        Retrieve the content of a single file from the repo.

        Args:
            repo_name:    Repository name
            file_path:    Path within the repo (e.g., "/src/App.tsx")
            version:      Branch name, commit SHA, or tag
            version_type: "branch" | "commit" | "tag"

        Returns:
            File content as a UTF-8 string
        """
        url = (
            f"{self._base_url}/repositories/{quote(repo_name)}"
            f"/items?path={quote(file_path)}"
        )
        if version:
            url += f"&versionDescriptor.version={quote(version)}"
            url += f"&versionDescriptor.versionType={version_type}"
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}api-version={self.API_VERSION}"
        req = Request(full_url, headers=self._auth_header())
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Azure DevOps API error {e.code} fetching {file_path}:\n{body}"
            ) from e

    def get_pr_file_contents(
        self, repo_name: str, pr_id: int, max_files: int = 50
    ) -> list[dict]:
        """
        Fetch the full content of every changed file in the PR's source
        branch (new / modified only — deleted files are skipped).

        Returns:
            List of dicts:
                filename, change_type, content
        """
        pr = self.get_pr_by_id(repo_name, pr_id)
        source_branch = pr["sourceRefName"].replace("refs/heads/", "")

        changes = self.get_pr_changes(repo_name, pr_id)
        results = []

        for ch in changes[:max_files]:
            if ch["change_type"] in ("delete",):
                continue  # nothing to review for deleted files
            try:
                content = self.get_file_content(
                    repo_name, ch["filename"], version=source_branch
                )
                results.append({
                    "filename": ch["filename"],
                    "change_type": ch["change_type"],
                    "content": content,
                })
            except Exception as exc:
                print(f"   ⚠️  Could not fetch {ch['filename']}: {exc}")

        return results

    # ── Commenting ──────────────────────────────────────────

    def post_pr_comment(
        self,
        repo_name: str,
        pr_id: int,
        body: str,
        status: int = 1,
    ) -> dict:
        """
        Post a top-level comment thread on a pull request.

        Args:
            repo_name: Repository name
            pr_id:     Pull request ID
            body:      Markdown-formatted comment body
            status:    1 = Active, 2 = Fixed, 3 = WontFix, 4 = Closed, 5 = Pending

        Returns:
            API response dict
        """
        url = (
            f"{self._base_url}/repositories/{quote(repo_name)}"
            f"/pullrequests/{pr_id}/threads"
        )
        payload = {
            "comments": [
                {
                    "parentCommentId": 0,
                    "content": body,
                    "commentType": 1,  # text
                }
            ],
            "status": status,
        }
        return self._post(url, payload)

    def post_pr_file_comment(
        self,
        repo_name: str,
        pr_id: int,
        file_path: str,
        line: int,
        body: str,
    ) -> dict:
        """
        Post an inline comment on a specific file and line in the PR.

        Useful for pointing out issues right where they occur.
        """
        url = (
            f"{self._base_url}/repositories/{quote(repo_name)}"
            f"/pullrequests/{pr_id}/threads"
        )
        payload = {
            "comments": [
                {
                    "parentCommentId": 0,
                    "content": body,
                    "commentType": 1,
                }
            ],
            "status": 1,
            "threadContext": {
                "filePath": file_path,
                "rightFileStart": {"line": line, "offset": 1},
                "rightFileEnd": {"line": line, "offset": 1},
            },
        }
        return self._post(url, payload)

    def set_pr_vote(
        self,
        repo_name: str,
        pr_id: int,
        vote: int,
        reviewer_id: Optional[str] = None,
    ) -> None:
        """
        Cast a vote on the PR (requires the reviewer's identity ID).

        Vote values:
            10  = Approved
             5  = Approved with suggestions
             0  = No vote
            -5  = Waiting for author
           -10  = Rejected
        """
        if not reviewer_id:
            print("   ⚠️  reviewer_id is required to cast a vote. Skipping.")
            return

        url = (
            f"{self._base_url}/repositories/{quote(repo_name)}"
            f"/pullrequests/{pr_id}/reviewers/{reviewer_id}"
        )
        # Use PUT for voting
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}api-version={self.API_VERSION}"
        data = json.dumps({"vote": vote}).encode("utf-8")
        req = Request(full_url, data=data, headers=self._auth_header(), method="PUT")
        try:
            with urlopen(req, timeout=30) as resp:
                resp.read()
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Vote failed ({e.code}): {body}") from e

    # ── Cleanup ─────────────────────────────────────────────

    def cleanup(self):
        """Remove temporary directories created during cloning."""
        import shutil

        for d in self._temp_dirs:
            shutil.rmtree(d, ignore_errors=True)
        self._temp_dirs.clear()
