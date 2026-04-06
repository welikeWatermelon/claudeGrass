"""scheduler 모듈 테스트"""

import unittest
from unittest.mock import patch, MagicMock

from claudegrass.scheduler import register_task, unregister_task, check_task_exists


class TestRegisterTask(unittest.TestCase):
    @patch("claudegrass.scheduler.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = register_task(18)
        self.assertTrue(result)
        args = mock_run.call_args[0][0]
        self.assertIn("schtasks", args)
        self.assertIn("/create", args)
        self.assertIn("18:00", args)

    @patch("claudegrass.scheduler.subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="access denied")
        result = register_task(9)
        self.assertFalse(result)

    @patch("claudegrass.scheduler.subprocess.run")
    def test_custom_hour(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        register_task(7)
        args = mock_run.call_args[0][0]
        self.assertIn("07:00", args)


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
