import os
import sys
import time
import signal
from core.logger import logger
from core.loader import load_tasks_from_directory
from core.scheduler import HubScheduler
from core.watcher import HubWatcher

# Keep track of running flag for the main loop
keep_running = True

def handle_shutdown(signum, frame):
    """Gracefully terminates background processes when shutdown signals are received."""
    global keep_running
    sig_name = signal.Signals(signum).name
    logger.info(f"Received signal {sig_name} ({signum}). Initiating graceful shutdown...")
    keep_running = False


def main():
    logger.info("==============================================")
    logger.info("Initializing Personal Automation Hub (PAH)...")
    logger.info("==============================================")

    # Register termination signals (SIGINT, SIGTERM)
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Initialize schedulers and watchers
    scheduler = HubScheduler()
    watcher = HubWatcher()

    # Load tasks from default directory
    tasks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks")
    tasks = load_tasks_from_directory(tasks_dir)

    # Register/Schedule loaded tasks
    scheduled_count = 0
    watch_count = 0
    manual_count = 0

    for task in tasks:
        if task.trigger_type in ("interval", "cron"):
            scheduler.schedule_task(task)
            scheduled_count += 1
        elif task.trigger_type == "watchdog":
            watcher.schedule_watch(task)
            watch_count += 1
        else:
            logger.info(f"Loaded manual/utility task '{task.name}': {task.description}")
            manual_count += 1

    # Start scheduler & watcher
    if scheduled_count > 0:
        scheduler.start()
    else:
        logger.info("No scheduled tasks found to start the scheduler.")

    if watch_count > 0:
        watcher.start()
    else:
        logger.info("No directory watch tasks found to start the Watchdog monitor.")

    logger.info(
        f"Initialization complete. Total tasks loaded: {len(tasks)} "
        f"({scheduled_count} scheduled, {watch_count} filesystem watch, {manual_count} manual/other)."
    )
    logger.info("Personal Automation Hub is running. Press Ctrl+C to terminate.")

    # Main thread loop
    try:
        while keep_running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt detected. Shutting down...")
    finally:
        # Graceful teardown
        if scheduled_count > 0:
            scheduler.shutdown()
        if watch_count > 0:
            watcher.shutdown()
        logger.info("Personal Automation Hub stopped safely.")
        logger.info("==============================================")


if __name__ == "__main__":
    # Ensure correct working directory is at front of PYTHONPATH
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    main()
