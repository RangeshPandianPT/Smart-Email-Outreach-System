import logging
import sys
import os
from logging.handlers import RotatingFileHandler

os.makedirs('logs', exist_ok=True)

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler (5 MB max size, keep 5 backups)
        fh = RotatingFileHandler('logs/app.log', maxBytes=5 * 1024 * 1024, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
