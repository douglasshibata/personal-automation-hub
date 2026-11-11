from apscheduler.schedulers.background import BackgroundScheduler
from core.logger import logger
from core.runner import run_task_safely

class HubScheduler:
    """
    Wrapper around APScheduler's BackgroundScheduler to handle interval and cron-based automation scheduling.
    """
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        """Starts the scheduler in the background."""
        logger.info("Starting background task scheduler...")
        self.scheduler.start()

    def shutdown(self):
        """Shuts down the scheduler gracefully."""
        logger.info("Shutting down background task scheduler...")
        self.scheduler.shutdown(wait=False)

    def schedule_task(self, task_metadata):
        """
        Schedules a task based on its trigger type and arguments.

        Args:
            task_metadata (TaskMetadata): The metadata object of the dynamically loaded task.
        """
        name = task_metadata.name
        trigger_type = task_metadata.trigger_type
        args = task_metadata.trigger_args
        execute_fn = task_metadata.execute_fn

        # Define wrapper callback using the safe task runner
        def job_callback():
            run_task_safely(name, execute_fn)

        if trigger_type == "interval":
            # Expecting seconds or minutes in args
            seconds = args.get("seconds")
            minutes = args.get("minutes")
            hours = args.get("hours")

            # Map parameters
            interval_args = {}
            if seconds is not None:
                interval_args["seconds"] = int(seconds)
            if minutes is not None:
                interval_args["minutes"] = int(minutes)
            if hours is not None:
                interval_args["hours"] = int(hours)

            if not interval_args:
                logger.error(f"Task '{name}' has interval trigger but no valid interval parameters (seconds, minutes, hours). Skipping.")
                return

            self.scheduler.add_job(
                job_callback,
                trigger="interval",
                id=f"job_interval_{name}",
                replace_existing=True,
                **interval_args
            )
            logger.info(f"Scheduled interval task '{name}' with params: {interval_args}")

        elif trigger_type == "cron":
            # Map standard cron terms: second, minute, hour, day, month, day_of_week
            cron_args = {
                "second": args.get("second", "0"),
                "minute": args.get("minute", "*"),
                "hour": args.get("hour", "*"),
                "day": args.get("day", "*"),
                "month": args.get("month", "*"),
                "day_of_week": args.get("day_of_week", "*"),
            }

            self.scheduler.add_job(
                job_callback,
                trigger="cron",
                id=f"job_cron_{name}",
                replace_existing=True,
                **cron_args
            )
            logger.info(f"Scheduled CRON task '{name}' with schedule: {cron_args}")

        else:
            logger.debug(f"Task '{name}' is not scheduled (trigger_type: {trigger_type}).")
