import os
import shutil
from core.logger import logger

# Essential task declarations for dynamic loader discovery
TASK_NAME = "organizar_downloads"
TASK_DESCRIPTION = "Organiza arquivos da pasta Downloads automaticamente em subpastas com base nas extensões."
TASK_TRIGGER_TYPE = "watchdog"
# Default path to be monitored - can be customized by environment variables
TASK_TRIGGER_ARGS = {
    "path": os.getenv("DOWNLOADS_WATCH_DIR", "Downloads"),
    "recursive": False
}

# Define mapping rules for folders
EXT_MAP = {
    "imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "documentos_pdf": [".pdf"],
    "documentos_texto": [".docx", ".doc", ".txt", ".xlsx", ".csv", ".pptx", ".odt", ".rtf"],
    "executaveis": [".exe", ".msi", ".sh", ".bat", ".deb", ".dmg"],
    "compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "midia": [".mp3", ".wav", ".mp4", ".mkv", ".avi", ".mov"]
}

def execute(file_path: str = None):
    """
    Called either dynamically by Watchdog on a new file creation (passing file_path),
    or manually to scan the entire designated Downloads folder.
    """
    watch_path = TASK_TRIGGER_ARGS["path"]

    if file_path:
        # Single-file mode (called via Watchdog observer)
        if os.path.exists(file_path):
            logger.info(f"[organizar_downloads] Processing single file event: {file_path}")
            _organize_single_file(file_path, watch_path)
    else:
        # Batch-scan mode (called as startup routine or cron checkup)
        logger.info(f"[organizar_downloads] Executing batch directory scan in: {watch_path}")
        if not os.path.exists(watch_path):
            logger.warning(f"[organizar_downloads] Target folder '{watch_path}' does not exist.")
            return

        for filename in os.listdir(watch_path):
            full_path = os.path.join(watch_path, filename)
            if os.path.isfile(full_path):
                _organize_single_file(full_path, watch_path)


def _organize_single_file(file_path: str, base_dir: str):
    """Helps process and route a file to its matching mapped directory."""
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if not ext:
        logger.debug(f"[organizar_downloads] Skipping file '{filename}' with no extension.")
        return

    # Find the target category
    target_category = "outros"
    for category, extensions in EXT_MAP.items():
        if ext in extensions:
            target_category = category
            break

    target_dir = os.path.join(base_dir, target_category)
    os.makedirs(target_dir, exist_ok=True)

    dest_path = os.path.join(target_dir, filename)

    # Handle filename collision gracefully by renaming
    base_name, file_ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(dest_path):
        new_filename = f"{base_name}_{counter}{file_ext}"
        dest_path = os.path.join(target_dir, new_filename)
        counter += 1

    try:
        shutil.move(file_path, dest_path)
        logger.info(f"[organizar_downloads] Successfully moved '{filename}' -> '{target_category}/'")
    except Exception as e:
        logger.error(f"[organizar_downloads] Failed to move '{filename}': {e}")
