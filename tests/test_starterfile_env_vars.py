import os
import unittest
from unittest import mock
from unittest.mock import patch

import startout.paths


# @mock.patch('startout.paths.prompt_init_option')
# @mock.patch('startout.paths.parse_starterfile')
# @mock.patch('startout.paths.open')
# @mock.patch('startout.paths.os.chdir')
# @mock.patch('startout.paths.initialize_repo')
# @mock.patch('startout.paths.new_repo_owner_interactive')
# @mock.patch('startout.paths.gh_api.check_repo_custom_property')
# @mock.patch('startout.paths.re.match')
class TestStarterFileEnvironmentVariableFunctions(unittest.TestCase):

    def setUp(self):
        self.safe_dir = os.getcwd()

        # Test parameters
        self.fully_formed_template_name = "Github/Repository"
        self.startout_path_template_name = "test-test"
        self.new_repo_name = "NewRepo"
        self.new_repo_owner = "Owner"
        self.public = True
        self.created_repo_path = "path/to/repo"
        self.mock_api_key = "Fhd@aF+88nZV$h4YFe445"

        self.final_env_file = f"""EXISTING_VAR=wasAlreadyHere
RESULT=A
ONE=1
API_KEY={self.mock_api_key}
"""

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
    def test_starterfile_env_vars(self, mock_check, mock_init_repo):
        #####################
        # Define interactions
        self.mock_console.input.side_effect = [
            "",
            self.mock_api_key,
            "y",
        ]  # Simulate input
        mock_check.return_value = True  # The template is a valid Path
        mock_init_repo.return_value = "."  # Successfully initialized the repo
        #####################

        os.chdir("tests/resources/workspaces/environment_variables")

        with open("final.env", "r") as f:
            original_file_contents = f.read()

        startout.paths.initialize_path_instance(
            template=self.fully_formed_template_name,
            new_repo_name=self.new_repo_name,
            new_repo_owner=self.new_repo_owner,
            public=self.public,
        )

        with open("final.env", "r") as f:
            updated = f.read()
            matching_contents = updated == self.final_env_file

        with open("final.env", "w") as f:
            f.write(original_file_contents)

        assert matching_contents