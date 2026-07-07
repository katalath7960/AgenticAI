import shutil
from pathlib import Path


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def backup_file(file_path: str) -> str:
    from utilities.time_utils import now_str
    src = Path(file_path)
    dst = src.with_name(f"{src.stem}_backup_{now_str()}{src.suffix}")
    shutil.copy2(src, dst)
    return str(dst)
