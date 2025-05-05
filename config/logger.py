import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Formatting
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler (rotating logs)
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=1024 * 1024 * 5,  # 5MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger(name='Log')