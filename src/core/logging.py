import sys
from loguru import logger
from src.core.config import get_settings


def setup_logging():
    """Configure Loguru logger based on application settings."""
    settings = get_settings()

    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    return logger


# Initial default configuration
setup_logging()
