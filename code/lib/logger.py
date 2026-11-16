"""统一日志：控制台 + 文件双写，业务代码不直接 print。"""

import logging
import os
import sys
from datetime import datetime

from .config import LOG_DIR

FORMAT = "%(asctime)s %(levelname)-5s %(name)s: %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"
_configured = set()


def get_logger(name="x", logfile=None, quiet=False):
    """取（并按需初始化）一个双写 logger。"""
    logger = logging.getLogger(name)
    if name in _configured:
        return logger

    os.makedirs(LOG_DIR, exist_ok=True)
    if logfile is None:
        logfile = datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
    path = logfile if os.path.isabs(logfile) else os.path.join(LOG_DIR, logfile)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(logging.WARNING if quiet else logging.INFO)
    stream.setFormatter(logging.Formatter(FORMAT, DATEFMT))

    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FORMAT, DATEFMT))

    logger.addHandler(stream)
    logger.addHandler(file_handler)
    _configured.add(name)
    return logger


def setup(logfile=None, quiet=False, name="x"):
    """入口调用：初始化日志，返回 (logger, 日志文件路径)。"""
    logger = get_logger(name, logfile=logfile, quiet=quiet)
    level = logging.WARNING if quiet else logging.INFO
    path = ""
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            path = handler.baseFilename
        else:
            handler.setLevel(level)
    return logger, path
