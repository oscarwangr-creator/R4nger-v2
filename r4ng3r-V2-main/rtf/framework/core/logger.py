"""RedTeam Framework - Logging System"""
from __future__ import annotations
import logging, logging.handlers, sys
from pathlib import Path
from typing import Optional

try:
    from rich.logging import RichHandler
    from rich.console import Console
    _RICH = True
except ImportError:
    _RICH = False

_FMT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"
_configured: set = set()

def get_logger(name: str = "rtf", level: str = "INFO", log_file: Optional[str] = None, rich_console: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    if name in _configured:
        return logger
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    if _RICH and rich_console:
        h = RichHandler(rich_tracebacks=True, show_path=False, markup=True)
        h.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    else:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    logger.addHandler(h)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        fh.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
        logger.addHandler(fh)
    _configured.add(name)
    return logger

def configure_root_logger(level: str = "INFO", log_file: Optional[str] = None) -> None:
    get_logger("rtf", level=level, log_file=log_file, rich_console=True)
