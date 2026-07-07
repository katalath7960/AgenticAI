import sys
from datetime import datetime
from pathlib import Path

from loguru import logger as _logger

_configured = False


def setup_logger(log_folder: str = "logs") -> None:
    global _configured
    if _configured:
        return
    Path(log_folder).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_folder}/run_{ts}.log"

    _logger.remove()
    _logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        level="INFO",
    )
    _logger.add(
        log_file,
        rotation="50 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {extra[test]:<30} | {extra[step]:<40} | {message}",
        level="DEBUG",
    )
    _configured = True


def get_logger(test: str = "-", step: str = "-"):
    return _logger.bind(test=test, step=step)


logger = _logger.bind(test="-", step="-")
