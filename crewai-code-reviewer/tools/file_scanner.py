"""
Project Scanner
================
Scans a project directory and categorizes files by type.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field


# File extension categories
FRONTEND_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}
BACKEND_EXTENSIONS = {".cs"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".env", ".config", ".csproj", ".sln"}
STYLE_EXTENSIONS = {".css", ".scss", ".less", ".styled.ts", ".styled.tsx"}
TEST_PATTERNS = {"test", "spec", "__tests__", ".test.", ".spec."}

# Directories to skip
SKIP_DIRS = {
    "node_modules",
    "bin",
    "obj",
    ".git",
    ".vs",
    ".vscode",
    ".idea",
    "dist",
    "build",
    "coverage",
    ".next",
    "wwwroot",
    "packages",
    "TestResults",
    "__pycache__",
}

# Max file size to read (500 KB)
MAX_FILE_SIZE = 500_000


@dataclass
class FileInfo:
    """Metadata about a single source file."""

    path: str
    relative_path: str
    extension: str
    size: int
    category: str  # frontend | backend | config | style | test | other
    is_test: bool = False


@dataclass
class ScanResult:
    """Result of a project scan."""

    frontend_files: list[FileInfo] = field(default_factory=list)
    backend_files: list[FileInfo] = field(default_factory=list)
    config_files: list[FileInfo] = field(default_factory=list)
    style_files: list[FileInfo] = field(default_factory=list)
    test_files: list[FileInfo] = field(default_factory=list)
    other_files: list[FileInfo] = field(default_factory=list)

    @property
    def all_files(self) -> list[FileInfo]:
        return (
            self.frontend_files
            + self.backend_files
            + self.config_files
            + self.style_files
            + self.test_files
            + self.other_files
        )


class ProjectScanner:
    """Scans a project directory for reviewable source files."""

    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"Project directory not found: {self.root}")

    def scan(self) -> dict:
        """
        Walk the project tree and return a dict compatible with the rest
        of the pipeline.

        Returns:
            dict with keys:
                frontend_files, backend_files, config_files, style_files,
                test_files, other_files  – each a list of FileInfo dicts
        """
        result = ScanResult()

        for dirpath, dirnames, filenames in os.walk(self.root):
            # Prune skipped directories in-place
            dirnames[:] = [
                d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
            ]

            for fname in filenames:
                fpath = Path(dirpath) / fname
                ext = fpath.suffix.lower()

                # Skip hidden files and very large files
                if fname.startswith(".") or fpath.stat().st_size > MAX_FILE_SIZE:
                    continue

                rel = str(fpath.relative_to(self.root))
                info = FileInfo(
                    path=str(fpath),
                    relative_path=rel,
                    extension=ext,
                    size=fpath.stat().st_size,
                    category=self._categorize(ext, rel),
                    is_test=self._is_test(rel, fname),
                )

                # Distribute into buckets
                if info.is_test:
                    result.test_files.append(info)
                elif info.category == "frontend":
                    result.frontend_files.append(info)
                elif info.category == "backend":
                    result.backend_files.append(info)
                elif info.category == "config":
                    result.config_files.append(info)
                elif info.category == "style":
                    result.style_files.append(info)
                else:
                    result.other_files.append(info)

        # Convert to plain dicts for JSON-friendliness
        return {
            "frontend_files": [self._to_dict(f) for f in result.frontend_files],
            "backend_files": [self._to_dict(f) for f in result.backend_files],
            "config_files": [self._to_dict(f) for f in result.config_files],
            "style_files": [self._to_dict(f) for f in result.style_files],
            "test_files": [self._to_dict(f) for f in result.test_files],
            "other_files": [self._to_dict(f) for f in result.other_files],
        }

    # ── helpers ─────────────────────────────────────────────

    @staticmethod
    def _categorize(ext: str, rel_path: str) -> str:
        if ext in FRONTEND_EXTENSIONS:
            return "frontend"
        if ext in BACKEND_EXTENSIONS:
            return "backend"
        if ext in CONFIG_EXTENSIONS:
            return "config"
        if ext in STYLE_EXTENSIONS:
            return "style"
        return "other"

    @staticmethod
    def _is_test(rel_path: str, filename: str) -> bool:
        lower = (rel_path + filename).lower()
        return any(p in lower for p in TEST_PATTERNS)

    @staticmethod
    def _to_dict(info: FileInfo) -> dict:
        return {
            "path": info.path,
            "relative_path": info.relative_path,
            "extension": info.extension,
            "size": info.size,
            "category": info.category,
            "is_test": info.is_test,
        }


def generate_file_tree(root_path: str, max_depth: int = 4) -> str:
    """Generate a text-based file tree for display."""
    root = Path(root_path).resolve()
    lines = [f"{root.name}/"]

    def _walk(directory: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name))
        entries = [
            e
            for e in entries
            if e.name not in SKIP_DIRS and not e.name.startswith(".")
        ]
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1)

    _walk(root, "", 0)
    return "\n".join(lines)
