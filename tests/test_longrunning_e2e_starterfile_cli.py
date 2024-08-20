import os
import unittest
from unittest import mock
from unittest.mock import patch

from parameterized import parameterized

import startout.paths


# @mock.patch('startout.paths.prompt_init_option')
# @mock.patch('startout.paths.parse_starterfile')
# @mock.patch('startout.paths.open')
# @mock.patch('startout.paths.os.chdir')
# @mock.patch('startout.paths.initialize_repo')
# @mock.patch('startout.paths.new_repo_owner_interactive')
# @mock.patch('startout.paths.gh_api.check_repo_custom_property')
# @mock.patch('startout.paths.re.match')
class TestStarterFileCLIEndToEnd(unittest.TestCase):

    def setUp(self):
        self.safe_dir = os.getcwd()

        # Test parameters
        self.fully_formed_template_name = "Github/Repository"
        self.startout_path_template_name = "test-test"
        self.new_repo_name = "NewRepo"
        self.new_repo_owner = "Owner"
        self.public = True
        self.created_repo_path = "path/to/repo"

        self.console_patcher = patch("startout.paths.console", autospec=True)
        self.mock_console = self.console_patcher.start()

        self.console_height_patcher = patch("startout.paths.console.height", new=4)
        self.console_height_patcher.start()

    def tearDown(self):
        self.console_patcher.stop()
        self.console_height_patcher.stop()
        os.chdir(self.safe_dir)

    @mock.patch("startout.paths.initialize_repo")
    @mock.patch("startout.paths.gh_api.check_repo_custom_property")
    def test_starterfile_up_init_options(self, mock_check, mock_init_repo):
        #####################
        # Define interactions
        self.mock_console.input.side_effect = [
            "n",
            "",
            "",
            "",
        ]  # Simulate declining optional tool and pressing enter to take default
        mock_check.return_value = True  # The template is a valid Path
        mock_init_repo.return_value = (
            self.created_repo_path
        )  # Successfully initialized the repo
        #####################

        os.chdir("tests/resources/workspaces/complex_starter")

        startout.paths.starterfile_up_only("complex_starter.yaml")
