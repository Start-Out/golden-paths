import subprocess
import unittest
from unittest.mock import patch

from parameterized import parameterized

import startout
from startout.paths import initialize_repo, new_repo_owner_interactive


class TestInitializeRepo(unittest.TestCase):
    def setUp(self):
        self.patcher1 = patch('startout.github_api.create_repo_from_temp', autospec=True)
        self.patcher2 = patch('startout.paths.console', autospec=True)
        self.mock_create_repo = self.patcher1.start()
        self.mock_console = self.patcher2.start()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()

    # fmt: off
    @parameterized.expand([
        ("successfully creates repo",  # Basic public repo
         "template_owner", "template_name", "new_repo_owner", "new_repo_name", True, "path/to/repo"),

        ("fails to create repo",  # Basic private repo
         "template_owner", "template_name", "new_repo_owner", "new_repo_name", False, False),
    ])
    # fmt: on
    def test_initialize_repo_no_interactions(self, name, template_owner, template_name, new_repo_owner, new_repo_name,
                                             public, expected_result
                                             ):
        self.mock_create_repo.return_value = expected_result
        self.mock_console.input.return_value = "input_value"

        given_result = initialize_repo(template_owner, template_name, new_repo_owner, new_repo_name, public)

        assert given_result == expected_result

    # fmt: off
    @parameterized.expand([
        ("successfully creates repo",  # Basic public repo
         "path/to/repo"),

        ("fails to create repo",  # Basic private repo
         False),
    ])
    # fmt: on
    def test_initialize_repo_interactively(self, name, expected_result):
        self.mock_create_repo.return_value = expected_result
        self.mock_console.input.return_value = "input_value"

        given_result = initialize_repo(None, None, None, None)

        assert given_result == expected_result
        self.assertEqual(self.mock_console.input.call_count, 4)  # One for each prompt


@unittest.mock.patch('subprocess.run')
class TestNewRepoOwnerInteractive(unittest.TestCase):
    def setUp(self):
        self.username = "goose"

        self.console_patcher = patch('startout.paths.console', autospec=True)
        self.mock_console = self.console_patcher.start()

    def tearDown(self):
        self.console_patcher.stop()

    def default_subprocess_side_effect(self, *args, **kwargs):
        if args[0] == ['gh', 'auth', 'status']:
            user_string = b'\naccount ' + self.username.encode('utf-8')
            user_string += b' (keyring)\n'

            return subprocess.CompletedProcess(args=args, returncode=0, stdout=user_string,
                                               stderr=None)
        elif args[0] == ['gh', 'org', 'list']:
            return subprocess.CompletedProcess(args=args, returncode=0, stdout=b'org1\norg2\n', stderr=None)

        return subprocess.CompletedProcess(args=args, returncode=-1, stdout=None, stderr=None)

    def test_error_from_cli(self, mock_subprocess):
        mock_subprocess.return_value = subprocess.CompletedProcess(args=['gh', 'auth', 'status'], returncode=-1,
                                                                   stdout=None, stderr=None)

        with self.assertRaises(SystemExit):
            new_repo_owner_interactive()

    def test_no_orgs(self, mock_subprocess):
        mock_subprocess.side_effect = self.default_subprocess_side_effect
        new_repo_owner_interactive()

    def test_valid_user_choice(self, mock_subprocess):
        self.mock_console.input.return_value = "0"
        mock_subprocess.side_effect = self.default_subprocess_side_effect

        result = new_repo_owner_interactive()
        self.assertEqual(result, self.username)

    def test_invalid_user_choice_prompts_again(self, mock_subprocess):
        self.mock_console.input.side_effect = ["duck", "duck", "0"]  # Invalid input first, followed by valid input
        mock_subprocess.side_effect = self.default_subprocess_side_effect

        result = new_repo_owner_interactive()

        self.assertEqual(result, self.username)

        # The 'input' should have been called thrice: twice for the invalid input and once for the valid input.
        self.assertEqual(self.mock_console.input.call_count, 3)
