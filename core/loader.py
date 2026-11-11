import os
import sys
import importlib.util
from core.logger import logger

class TaskMetadata:
    """
    Holds information parsed from a dynamically loaded task module.
    """
    def __init__(self, name, description, trigger_type, trigger_args, execute_fn, module):
        self.name = name
        self.description = description
        self.trigger_type = trigger_type  # 'interval', 'cron', 'watchdog', or 'manual'
        self.trigger_args = trigger_args  # dict containing schedule parameters (e.g. seconds, hour, path)
        self.execute_fn = execute_fn      # callable function to run
        self.module = module              # imported python module object

    def __repr__(self):
        return f"<TaskMetadata name={self.name} trigger={self.trigger_type}>"


def load_tasks_from_directory(directory_path="tasks") -> list[TaskMetadata]:
    """
    Dynamically scans and imports Python scripts inside the specified directory.
    To be identified as a valid task, the script should define:
    - TASK_NAME (str)
    - TASK_DESCRIPTION (str)
    - TASK_TRIGGER_TYPE (str): 'cron', 'interval', 'watchdog', or 'manual'
    - TASK_TRIGGER_ARGS (dict): arguments for the trigger configuration
    - execute (callable): The function to execute.

    Args:
        directory_path (str): Relative or absolute path to scan for task files.

    Returns:
        list[TaskMetadata]: List of metadata for loaded valid tasks.
    """
    loaded_tasks = []

    if not os.path.exists(directory_path):
        logger.warning(f"Task directory '{directory_path}' does not exist.")
        return loaded_tasks

    # Add the tasks directory to sys.path to resolve any internal relative imports
    absolute_dir = os.path.abspath(directory_path)
    if absolute_dir not in sys.path:
        sys.path.insert(0, absolute_dir)

    for filename in os.listdir(directory_path):
        if filename.endswith(".py") and not filename.startswith("_"):
            file_path = os.path.join(directory_path, filename)
            module_name = filename[:-3]

            try:
                # Load the Python module dynamically
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    logger.warning(f"Could not build spec for module '{module_name}' at {file_path}")
                    continue

                module = importlib.util.module_from_spec(spec)
                # Keep system module catalog updated for consistency
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Retrieve expected metadata parameters
                task_name = getattr(module, "TASK_NAME", module_name)
                task_desc = getattr(module, "TASK_DESCRIPTION", "No description provided.")
                trigger_type = getattr(module, "TASK_TRIGGER_TYPE", "manual")
                trigger_args = getattr(module, "TASK_TRIGGER_ARGS", {})
                execute_fn = getattr(module, "execute", None)

                if execute_fn is None or not callable(execute_fn):
                    logger.warning(
                        f"Skipping potential task file '{filename}': "
                        f"Does not define a callable 'execute' function."
                    )
                    continue

                task_meta = TaskMetadata(
                    name=task_name,
                    description=task_desc,
                    trigger_type=trigger_type,
                    trigger_args=trigger_args,
                    execute_fn=execute_fn,
                    module=module
                )

                loaded_tasks.append(task_meta)
                logger.info(f"Successfully loaded automation task: {task_name} (Trigger: {trigger_type})")

            except Exception as e:
                logger.error(f"Failed to load task from file '{filename}': {e}", exc_info=True)

    return loaded_tasks
