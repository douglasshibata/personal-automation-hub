import os
import sys
import shutil
import time
import pytest
from unittest.mock import MagicMock, patch

# Ensure our modules are discoverable on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import setup_logger
from core.runner import run_task_safely, TaskResult
from core.loader import load_tasks_from_directory, TaskMetadata
from core.scheduler import HubScheduler
from core.watcher import HubWatcher

@pytest.fixture
def test_logger():
    return setup_logger("test_hub", "personal-automation-hub/logs/test_automation.log")


def test_task_runner_success(test_logger):
    """Tests that the task runner correctly catches and records successful task executions."""
    called = False
    def sample_success_task():
        nonlocal called
        called = True

    result = run_task_safely("sample_success", sample_success_task)
    assert called is True
    assert result.success is True
    assert result.task_name == "sample_success"
    assert result.execution_time >= 0
    assert result.error is None
    assert "SUCCESS" in repr(result)


def test_task_runner_failure(test_logger):
    """Tests that the task runner safely catches exceptions and records error details without crashing."""
    def sample_failing_task():
        raise ValueError("Simulated failure")

    result = run_task_safely("sample_failure", sample_failing_task)
    assert result.success is False
    assert result.task_name == "sample_failure"
    assert "ValueError" in result.error or "Simulated failure" in result.error
    assert "FAILED" in repr(result)


def test_dynamic_task_loader(tmp_path):
    """Tests that the loader scans the folder and dynamically imports tasks with accurate metadata."""
    # Write a mock task to the temporary folder
    task_file = tmp_path / "test_task_loaded.py"
    task_file.write_text("""
TASK_NAME = "custom_test_task"
TASK_DESCRIPTION = "A simulated task for tests."
TASK_TRIGGER_TYPE = "interval"
TASK_TRIGGER_ARGS = {"seconds": 10}

def execute():
    return "executed"
""")

    loaded_tasks = load_tasks_from_directory(str(tmp_path))
    assert len(loaded_tasks) == 1
    task_meta = loaded_tasks[0]
    assert task_meta.name == "custom_test_task"
    assert task_meta.description == "A simulated task for tests."
    assert task_meta.trigger_type == "interval"
    assert task_meta.trigger_args == {"seconds": 10}
    assert task_meta.execute_fn() == "executed"


def test_scheduler_register(test_logger):
    """Tests that interval and cron tasks are registered correctly on APScheduler."""
    scheduler_wrapper = HubScheduler()

    # 1. Interval task metadata
    interval_task = TaskMetadata(
        name="interval_task",
        description="Interval Task",
        trigger_type="interval",
        trigger_args={"seconds": 5},
        execute_fn=lambda: None,
        module=None
    )

    # 2. Cron task metadata
    cron_task = TaskMetadata(
        name="cron_task",
        description="Cron Task",
        trigger_type="cron",
        trigger_args={"hour": "10", "minute": "30"},
        execute_fn=lambda: None,
        module=None
    )

    scheduler_wrapper.schedule_task(interval_task)
    scheduler_wrapper.schedule_task(cron_task)

    jobs = scheduler_wrapper.scheduler.get_jobs()
    # Check both tasks are in schedule
    job_ids = [job.id for job in jobs]
    assert "job_interval_interval_task" in job_ids
    assert "job_cron_cron_task" in job_ids


@patch("core.watcher.Observer")
def test_watcher_register(mock_observer_class, tmp_path):
    """Tests that watchdog triggers directories mapping correct callbacks."""
    mock_observer = MagicMock()
    mock_observer_class.return_value = mock_observer

    watcher_wrapper = HubWatcher()

    watchdog_task = TaskMetadata(
        name="watchdog_task",
        description="Watchdog Task",
        trigger_type="watchdog",
        trigger_args={"path": str(tmp_path), "recursive": False},
        execute_fn=lambda x: None,
        module=None
    )

    watcher_wrapper.schedule_watch(watchdog_task)
    watcher_wrapper.start()

    # Assert schedule and start were invoked on Observer
    assert mock_observer.schedule.called
    assert mock_observer.start.called
    watcher_wrapper.shutdown()
    assert mock_observer.stop.called


def test_task_organizar_downloads(tmp_path):
    """Tests the organizar_downloads logic moves files accurately based on mapping."""
    import tasks.organizar_downloads as organize_task

    # Setup directories
    downloads_mock_dir = tmp_path / "Downloads"
    downloads_mock_dir.mkdir()

    # Override path setting for testing
    organize_task.TASK_TRIGGER_ARGS["path"] = str(downloads_mock_dir)

    # Place a pdf, an image, and an executable file
    pdf_file = downloads_mock_dir / "invoice.pdf"
    image_file = downloads_mock_dir / "photo.PNG"
    exe_file = downloads_mock_dir / "installer.msi"
    no_ext_file = downloads_mock_dir / "somefile"

    pdf_file.touch()
    image_file.touch()
    exe_file.touch()
    no_ext_file.touch()

    # Run the organizer task (batch scanning)
    organize_task.execute()

    # Confirm the files were categorized correctly
    assert not pdf_file.exists()
    assert not image_file.exists()
    assert not exe_file.exists()
    assert no_ext_file.exists()  # Kept in original folder since it has no extension

    # Mapped paths checks
    assert (downloads_mock_dir / "documentos_pdf" / "invoice.pdf").exists()
    assert (downloads_mock_dir / "imagens" / "photo.PNG").exists()
    assert (downloads_mock_dir / "executaveis" / "installer.msi").exists()


@patch("tasks.relatorio_diario.requests.post")
@patch("tasks.relatorio_diario.requests.get")
def test_task_relatorio_diario_api_success(mock_get, mock_post):
    """Tests daily report task logic on api success."""
    import tasks.relatorio_diario as report_task

    # Mock response
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = [
        {"userId": 1, "id": 1, "title": "A", "body": "B"},
        {"userId": 1, "id": 2, "title": "C", "body": "D"},
        {"userId": 5, "id": 3, "title": "E", "body": "F"}
    ]
    mock_get.return_value = mock_get_response

    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post.return_value = mock_post_response

    # Force a dummy webhook URL
    with patch.dict(os.environ, {"NOTIFICATIONS_WEBHOOK_URL": "http://mock-webhook"}):
        report_task.execute()

    # Verify requests
    assert mock_get.called
    assert mock_post.called


def test_task_limpeza_sistema(tmp_path):
    """Tests the temporary file purger deletes older files accurately and keeps young ones."""
    import tasks.limpeza_sistema as cleanup_task

    # Setup directories
    temp_purge_dir = tmp_path / "temp_purge"
    temp_purge_dir.mkdir()

    cleanup_task.execute() # Executes and creates folder if empty/none

    # Override target and age
    with patch.dict(os.environ, {
        "CLEANUP_TARGET_DIR": str(temp_purge_dir),
        "CLEANUP_MAX_AGE_SECONDS": "60" # 1 minute
    }):
        old_file = temp_purge_dir / "old.txt"
        new_file = temp_purge_dir / "new.txt"

        old_file.touch()
        new_file.touch()

        # Artificially set back modification time for old_file (e.g., 2 minutes ago)
        two_mins_ago = time.time() - 120
        os.utime(str(old_file), (two_mins_ago, two_mins_ago))

        # Run cleanup task
        cleanup_task.execute()

        # Check results
        assert not old_file.exists()
        assert new_file.exists()
