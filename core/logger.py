import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name="automation_hub", log_file="logs/automation.log", level=logging.INFO):
    """
    Sets up a thread-safe logger that outputs both to the console and a rotating log file.

    Args:
        name (str): Name of the logger.
        log_file (str): Path to the log file.
        level (int): Logging level.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure the directory for the log file exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if the logger is already initialized
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(filename)s:%(lineno)d] - %(message)s"
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

        # Rotating File handler (max 5MB per file, keeping up to 5 backups)
        try:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to standard logging on error
            print(f"Failed to initialize rotating file handler for logging: {e}")

    return logger

# Default package-level logger
logger = setup_logger()
