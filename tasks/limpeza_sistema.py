import os
import time
from core.logger import logger

# Essential task declarations for dynamic loader discovery
TASK_NAME = "limpeza_sistema"
TASK_DESCRIPTION = "Remove arquivos temporários ou antigos de um diretório alvo baseado na idade do arquivo."
TASK_TRIGGER_TYPE = "interval"
# Configured by default to run every 6 hours
TASK_TRIGGER_ARGS = {
    "hours": 6
}

def execute():
    """
    Cleans up old files from a target temporary directory.
    - Path and minimum age limits can be customized with environment variables.
    """
    # Defaults to a safe internal folder 'logs' or custom folder 'temp_purge' so we don't wipe crucial files.
    target_dir = os.getenv("CLEANUP_TARGET_DIR", "temp_purge")
    # Maximum allowed age of files in seconds (Default is 7 days = 604800 seconds)
    max_age_seconds = int(os.getenv("CLEANUP_MAX_AGE_SECONDS", "604800"))

    logger.info(f"[limpeza_sistema] Starting purge check in directory: '{target_dir}' (Max age: {max_age_seconds}s)")

    if not os.path.exists(target_dir):
        logger.info(f"[limpeza_sistema] Creating temporary purge target directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
        return

    now = time.time()
    deleted_files_count = 0
    failed_files_count = 0

    for root, dirs, files in os.walk(target_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                # Retrieve file details
                file_stat = os.stat(file_path)
                # Compare last modification time
                file_age = now - file_stat.st_mtime

                if file_age > max_age_seconds:
                    logger.info(f"[limpeza_sistema] File '{filename}' is {file_age:.1f}s old (older than {max_age_seconds}s). Purging...")
                    os.remove(file_path)
                    deleted_files_count += 1
            except Exception as e:
                logger.error(f"[limpeza_sistema] Failed to analyze/delete '{file_path}': {e}")
                failed_files_count += 1

    logger.info(
        f"[limpeza_sistema] Purge check completed. Deleted {deleted_files_count} files, "
        f"failed on {failed_files_count} files."
    )
