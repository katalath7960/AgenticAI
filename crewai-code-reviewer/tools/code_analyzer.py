"""
Code Analyzer
==============
Loads source files, computes basic metrics, and prepares code content
for consumption by the review agents.
"""

from pathlib import Path
from tools.file_scanner import generate_file_tree


# Truncation limit per file (characters). Keeps total prompt within
# context-window budgets even for large projects.
MAX_CHARS_PER_FILE = 12_000
MAX_TOTAL_CHARS = 120_000


class CodeAnalyzer:
    """Load project files and prepare structured content for agents."""

    def load_files(self, file_manifest: dict, max_files: int = 50) -> dict:
        """
        Read file contents and prepare context blocks for the agents.

        Args:
            file_manifest: Output from ProjectScanner.scan()
            max_files: Maximum number of files to load

        Returns:
            dict with keys:
                frontend_code – formatted string of all frontend files
                backend_code  – formatted string of all backend files
                all_code      – combined formatted string
                all_files     – list of {"path", "content"} dicts
                file_tree     – text-based tree of the project
                stats         – summary statistics dict
        """
        frontend_entries = file_manifest.get("frontend_files", [])
        backend_entries = file_manifest.get("backend_files", [])
        config_entries = file_manifest.get("config_files", [])

        # Sort largest first so we pick the meatiest files when capping
        all_entries = sorted(
            frontend_entries + backend_entries + config_entries,
            key=lambda f: f["size"],
            reverse=True,
        )[:max_files]

        loaded_files: list[dict] = []
        frontend_blocks: list[str] = []
        backend_blocks: list[str] = []
        total_chars = 0

        for entry in all_entries:
            content = self._read_file(entry["path"])
            if content is None:
                continue

            # Truncate individual files
            if len(content) > MAX_CHARS_PER_FILE:
                content = (
                    content[: MAX_CHARS_PER_FILE // 2]
                    + "\n\n... [TRUNCATED — file too large] ...\n\n"
                    + content[-MAX_CHARS_PER_FILE // 4 :]
                )

            # Respect total budget
            if total_chars + len(content) > MAX_TOTAL_CHARS:
                break

            total_chars += len(content)
            block = self._format_block(entry["relative_path"], content)
            loaded_files.append(
                {"path": entry["relative_path"], "content": content}
            )

            if entry["category"] == "frontend":
                frontend_blocks.append(block)
            elif entry["category"] == "backend":
                backend_blocks.append(block)
            else:
                # Config files go into "all" but not into specific blocks
                pass

        # Build file tree from the first entry's root
        file_tree = ""
        if all_entries:
            root = str(
                Path(all_entries[0]["path"]).parents[
                    len(Path(all_entries[0]["relative_path"]).parts) - 1
                ]
            )
            try:
                file_tree = generate_file_tree(root)
            except Exception:
                file_tree = "\n".join(e["relative_path"] for e in all_entries)

        # Compute stats
        stats = self._compute_stats(file_manifest, loaded_files)

        return {
            "frontend_code": "\n\n".join(frontend_blocks) or "No frontend files found.",
            "backend_code": "\n\n".join(backend_blocks) or "No backend files found.",
            "all_code": "\n\n".join(frontend_blocks + backend_blocks)
            or "No files found.",
            "all_files": loaded_files,
            "file_tree": file_tree,
            "stats": stats,
        }

    # ── helpers ─────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str | None:
        """Read a file, returning None if unreadable."""
        try:
            return Path(path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

    @staticmethod
    def _format_block(relative_path: str, content: str) -> str:
        """Wrap file content in a labelled code block."""
        ext = Path(relative_path).suffix.lstrip(".")
        lang = {
            "cs": "csharp",
            "tsx": "tsx",
            "ts": "typescript",
            "jsx": "jsx",
            "js": "javascript",
        }.get(ext, ext)

        return (
            f"### File: `{relative_path}`\n"
            f"```{lang}\n{content}\n```"
        )

    @staticmethod
    def _compute_stats(manifest: dict, loaded: list[dict]) -> dict:
        """Compute summary statistics."""
        total_lines = sum(c["content"].count("\n") for c in loaded)
        return {
            "total_frontend_files": len(manifest.get("frontend_files", [])),
            "total_backend_files": len(manifest.get("backend_files", [])),
            "total_config_files": len(manifest.get("config_files", [])),
            "total_test_files": len(manifest.get("test_files", [])),
            "files_loaded": len(loaded),
            "total_lines": total_lines,
            "total_characters": sum(len(c["content"]) for c in loaded),
        }
