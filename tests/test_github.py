"""github 모듈 테스트"""

import unittest
from unittest.mock import patch, MagicMock

from claudegrass.github import validate_pat, push_file, create_readme


class TestValidatePat(unittest.TestCase):
    @patch("claudegrass.github._api_request")
    def test_valid_pat(self, mock_req):
        mock_req.return_value = MagicMock(status_code=200)
        self.assertTrue(validate_pat("ghp_valid"))

    @patch("claudegrass.github._api_request")
    def test_invalid_pat(self, mock_req):
        mock_req.return_value = MagicMock(status_code=401)
        self.assertFalse(validate_pat("ghp_invalid"))


class TestPushFile(unittest.TestCase):
    @patch("claudegrass.github._api_request")
    def test_create_new_file(self, mock_req):
        # GET returns 404 (file doesn't exist), PUT returns 201
        mock_req.side_effect = [
            MagicMock(status_code=404),
            MagicMock(status_code=201),
        ]
        config = {"github_pat": "ghp_test", "repo": "user/repo"}
        result = push_file(config, "test.svg", "<svg></svg>")
        self.assertTrue(result)
        self.assertEqual(mock_req.call_count, 2)

    @patch("claudegrass.github._api_request")
    def test_update_existing_file(self, mock_req):
        # GET returns 200 with sha, PUT returns 200
        mock_req.side_effect = [
            MagicMock(status_code=200, json=lambda: {"sha": "abc123"}),
            MagicMock(status_code=200),
        ]
        config = {"github_pat": "ghp_test", "repo": "user/repo"}
        result = push_file(config, "test.svg", "<svg></svg>")
        self.assertTrue(result)
        # PUT 호출 시 sha가 포함되어야 함
        put_call = mock_req.call_args_list[1]
        # _api_request("PUT", url, pat, data) → data는 4번째 positional arg
        data_arg = put_call[0][3] if len(put_call[0]) > 3 else {}
        self.assertIn("sha", data_arg)

    @patch("claudegrass.github._api_request")
    def test_push_failure(self, mock_req):
        mock_req.side_effect = [
            MagicMock(status_code=404),
            MagicMock(status_code=403, text="Forbidden"),
        ]
        config = {"github_pat": "ghp_test", "repo": "user/repo"}
        result = push_file(config, "test.svg", "<svg></svg>")
        self.assertFalse(result)


class TestCreateReadme(unittest.TestCase):
    @patch("claudegrass.github.push_file")
    @patch("claudegrass.github._api_request")
    def test_skip_existing_readme(self, mock_req, mock_push):
        mock_req.return_value = MagicMock(status_code=200)
        config = {"github_pat": "ghp_test", "repo": "user/repo"}
        create_readme(config)
        mock_push.assert_not_called()

    @patch("claudegrass.github.push_file")
    @patch("claudegrass.github._api_request")
    def test_create_new_readme(self, mock_req, mock_push):
        mock_req.return_value = MagicMock(status_code=404)
        mock_push.return_value = True
        config = {"github_pat": "ghp_test", "repo": "user/repo"}
        create_readme(config)
        mock_push.assert_called_once()


if __name__ == "__main__":
    unittest.main()
