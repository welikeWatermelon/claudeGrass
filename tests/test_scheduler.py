"""scheduler 모듈 테스트"""

import unittest
from unittest.mock import patch, MagicMock

from claudegrass.scheduler import (
    register_run_task, register_analyze_task,
    unregister_task, check_task_exists,
)


class TestRegisterRunTask(unittest.TestCase):
    @patch("claudegrass.scheduler.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = register_run_task(18)
        self.assertTrue(result)
        args = mock_run.call_args[0][0]
        self.assertIn("schtasks", args)
        self.assertIn("/create", args)
        self.assertIn("18:00", args)
        self.assertIn("daily", args)

    @patch("claudegrass.scheduler.subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="access denied")
        result = register_run_task(9)
        self.assertFalse(result)

    @patch("claudegrass.scheduler.subprocess.run")
    def test_custom_hour(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        register_run_task(7)
        args = mock_run.call_args[0][0]
        self.assertIn("07:00", args)


class TestRegisterAnalyzeTask(unittest.TestCase):
    @patch("claudegrass.scheduler.subprocess.run")
    def test_weekly(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        schedule = {"mode": "weekly", "weekday": 4}
        result = register_analyze_task(schedule, 18)
        self.assertTrue(result)
        args = mock_run.call_args[0][0]
        self.assertIn("weekly", args)
        self.assertIn("FRI", args)
        self.assertIn("18:00", args)

    @patch("claudegrass.scheduler.subprocess.run")
    def test_daily_interval(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        schedule = {"mode": "daily_interval", "interval_days": 3}
        result = register_analyze_task(schedule, 20)
        self.assertTrue(result)
        args = mock_run.call_args[0][0]
        self.assertIn("daily", args)
        self.assertIn("3", args)
        self.assertIn("20:00", args)


class TestUnregisterTask(unittest.TestCase):
    @patch("claudegrass.scheduler.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(unregister_task())

    @patch("claudegrass.scheduler.subprocess.run")
    def test_not_found(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(unregister_task())


class TestCheckTaskExists(unittest.TestCase):
    @patch("claudegrass.scheduler.subprocess.run")
    def test_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(check_task_exists())

    @patch("claudegrass.scheduler.subprocess.run")
    def test_not_exists(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(check_task_exists())


if __name__ == "__main__":
    unittest.main()
