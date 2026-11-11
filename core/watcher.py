import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.logger import logger
from core.runner import run_task_safely

class TaskFileSystemEventHandler(FileSystemEventHandler):
    """
    Subclasses watchdog's FileSystemEventHandler to forward system events to our safe task runner.
    """
    def __init__(self, task_name, execute_fn, watch_path):
        super().__init__()
        self.task_name = task_name
        self.execute_fn = execute_fn
        self.watch_path = watch_path

    def on_created(self, event):
        # We only care about files being created to avoid reacting to folder creation
        if not event.is_directory:
            logger.info(f"Watchdog trigger: New file detected at {event.src_path} for task '{self.task_name}'")
            # Invoke the execution safely, forwarding the new file's path
            run_task_safely(self.task_name, self.execute_fn, event.src_path)


class HubWatcher:
    """
    Coordinates watchdog observers to monitor specific directories and trigger tasks.
    """
    def __init__(self):
        self.observer = Observer()
        self.is_running = False

    def start(self):
        """Starts the filesystem observer in the background."""
        logger.info("Starting Watchdog system filesystem observer...")
        self.observer.start()
        self.is_running = True

    def shutdown(self):
        """Gracefully stops the filesystem observer."""
        if self.is_running:
            logger.info("Stopping Watchdog filesystem observer...")
            self.observer.stop()
            self.observer.join()
            self.is_running = False

    def schedule_watch(self, task_metadata):
        """
        Registers a task to trigger upon a new file in a specific path.

        Args:
            task_metadata (TaskMetadata): Metadata of the dynamic task with trigger_type="watchdog".
        """
        name = task_metadata.name
        args = task_metadata.trigger_args
        execute_fn = task_metadata.execute_fn

        watch_path = args.get("path")
        if not watch_path:
            logger.error(f"Task '{name}' has watchdog trigger but no 'path' defined in trigger_args. Skipping.")
            return

        # Ensure the watch directory exists
        if not os.path.exists(watch_path):
            try:
                os.makedirs(watch_path, exist_ok=True)
                logger.info(f"Created watched directory path: {watch_path}")
            except Exception as e:
                logger.error(f"Could not create watched directory path '{watch_path}' for task '{name}': {e}")
                return

        event_handler = TaskFileSystemEventHandler(
            task_name=name,
            execute_fn=execute_fn,
            watch_path=watch_path
        )

        # Monitor the folder (non-recursive by default, but customizable if specified)
        recursive = args.get("recursive", False)
        self.observer.schedule(event_handler, watch_path, recursive=recursive)
        logger.info(f"Registered directory watch on '{watch_path}' for task '{name}' (recursive={recursive})")
