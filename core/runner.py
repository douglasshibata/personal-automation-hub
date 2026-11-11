import time
import traceback
from core.logger import logger

class TaskResult:
    """
    Data class representing the outcome of a task execution.
    """
    def __init__(self, task_name, success, execution_time, error=None):
        self.task_name = task_name
        self.success = success
        self.execution_time = execution_time  # in seconds
        self.error = error

    def __repr__(self):
        status = "SUCCESS" if self.success else f"FAILED ({self.error})"
        return f"<TaskResult task={self.task_name} status={status} time={self.execution_time:.3f}s>"


def run_task_safely(task_name, task_callable, *args, **kwargs) -> TaskResult:
    """
    Executes a task callable safely, isolating exceptions to prevent crashes from affecting
    the rest of the Automation Hub, and records performance metrics and outcomes.

    Args:
        task_name (str): Unique name of the task.
        task_callable (callable): Function or callable object representing the task.
        *args: Variable positional arguments for the task.
        **kwargs: Variable keyword arguments for the task.

    Returns:
        TaskResult: Object describing the outcome of the run.
    """
    logger.info(f"Starting execution of task: {task_name}")
    start_time = time.perf_counter()

    try:
        # Run the callable task
        task_callable(*args, **kwargs)
        execution_time = time.perf_counter() - start_time
        logger.info(f"Task '{task_name}' executed successfully in {execution_time:.3f} seconds.")
        return TaskResult(task_name, True, execution_time)

    except Exception as e:
        execution_time = time.perf_counter() - start_time
        err_msg = str(e)
        detailed_traceback = traceback.format_exc()

        logger.error(
            f"Error occurred during execution of task '{task_name}' after {execution_time:.3f}s:\n"
            f"Exception: {type(e).__name__}: {err_msg}\n"
            f"Traceback:\n{detailed_traceback}"
        )

        return TaskResult(task_name, False, execution_time, error=err_msg)
