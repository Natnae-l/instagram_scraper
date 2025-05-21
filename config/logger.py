import logging
from logging import StreamHandler


def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler only (no file writing)
    handler = StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = setup_logger(name='Log')
