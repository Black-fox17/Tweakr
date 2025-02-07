
import logging
import sys
import os
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# import boto3
import zipfile
import shutil
from datetime import datetime, timedelta
from typing import Optional

# from app.core.constants import BUCKET_NAME
# from app.core.storage import s3_client

# Constants and log directory setup
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Default log file path and rotation settings
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "app.log")
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Number of backup files to keep
RETENTION_PERIOD_DAYS = 7  # Retention period for logs


class CustomFormatter(logging.Formatter):
    """
    A custom formatter that makes the recorded pathname relative to the current working directory.
    """

    def format(self, record):
        if record.pathname.startswith(os.getcwd()):
            record.pathname = os.path.relpath(record.pathname, os.getcwd())
        return super().format(record)


# class S3Handler(RotatingFileHandler):
#     """
#     A file handler that compresses rotated logs and uploads them to an S3 bucket.
#     """

#     def __init__(self, *args, **kwargs):
#         self.s3_client = s3_client
#         super().__init__(*args, **kwargs)

#     def doRollover(self):
#         super().doRollover()
#         self.compress_and_upload_to_s3()

#     def compress_and_upload_to_s3(self):
#         now = datetime.utcnow()
#         zip_filename = os.path.join(LOG_DIR, f"logs_{now.strftime('%Y%m%d%H%M%S')}.zip")
#         with zipfile.ZipFile(zip_filename, "w") as zipf:
#             for root, _, files in os.walk(LOG_DIR):
#                 for file in files:
#                     if file.endswith(".log") and not file.endswith(".zip"):
#                         zipf.write(os.path.join(root, file), arcname=file)
#         self.upload_to_s3(zip_filename, f"logs/{os.path.basename(zip_filename)}")
#         os.remove(zip_filename)

#     def upload_to_s3(self, file_path, s3_key):
#         self.s3_client.upload_file(file_path, BUCKET_NAME, s3_key)


def remove_old_logs():
    """
    Delete log files older than the configured retention period.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(days=RETENTION_PERIOD_DAYS)
    for root, _, files in os.walk(LOG_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            if (
                file.endswith(".log")
                and datetime.fromtimestamp(os.path.getmtime(file_path)) < cutoff
            ):
                os.remove(file_path)


# Base logging configuration dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": CustomFormatter,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        },
        "file": {
            # You can switch to S3Handler by changing the "class" value below:
            "class": "logging.handlers.RotatingFileHandler",
            "filename": DEFAULT_LOG_FILE,
            "formatter": "detailed",
            "maxBytes": MAX_LOG_SIZE,
            "backupCount": BACKUP_COUNT,
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "error.log"),
            "formatter": "detailed",
            "level": "ERROR",
        },
    },
    "loggers": {
        "": {  # Root logger configuration
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
        },
    },
}


def setup_logging(
    log_level: Optional[int] = None,
    use_s3_handler: bool = True,
    output_file: Optional[str] = DEFAULT_LOG_FILE,
) -> None:
    """
    Set up standardized logging configuration for the podcast generation system.

    Args:
        log_level: Optional logging level to set. If None, defaults to INFO.
                   (e.g., logging.DEBUG for debug output)
        output_file: Optional file path to write logs to. If provided, overrides the default file handler path.
        use_s3_handler: If True, use the S3Handler for the file handler to compress and upload logs to S3.

    The final log message format is:
        YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE [in pathname:lineno]
    """
    # Remove any existing handlers to avoid duplicate logs
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Update file handler destination if output_file is provided
    if output_file:
        LOGGING_CONFIG["handlers"]["file"]["filename"] = output_file

    # Optionally switch the file handler to use the S3Handler for S3 uploads
    if use_s3_handler:
        LOGGING_CONFIG["handlers"]["file"][
            "class"
        ] = "app.core.logging_config.S3Handler"

    # Set the log level for the root logger
    LOGGING_CONFIG["loggers"][""]["level"] = (
        log_level if log_level is not None else logging.INFO
    )

    # Apply the logging configuration
    dictConfig(LOGGING_CONFIG)
