import os
import unittest
from unittest import mock
from unittest.mock import patch

import startout.paths


class TestStarterFileEnvironmentVariableFunctions(unittest.TestCase):

    def setUp(self):
        self.safe_dir = os.getcwd()
        self.safe_env_vars = os.environ.copy()

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
        os.environ.clear()
        os.environ.update(self.safe_env_vars)

    @mock.patch("startout.paths.initialize_repo")
    @mock.patch("startout.paths.gh_api.check_repo_custom_property")
    def test_starterfile_dumps_env_vars(self, mock_check, mock_init_repo):
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
        with open("a.txt", "r") as f:
            a_file_contents = f.read()

        startout.paths.initialize_path_instance(
            template=self.fully_formed_template_name,
            new_repo_name=self.new_repo_name,
            new_repo_owner=self.new_repo_owner,
            public=self.public,
        )

        with open("final.env", "r") as f:
            updated = f.read()

        print("==== UPDATED: ")  # TODO debug
        print(updated)

        with open("final.env", "w") as f:
            f.write(original_file_contents)
        with open("a.txt", "w") as f:
            f.write(a_file_contents)

        assert updated == self.final_env_file

    @mock.patch("startout.paths.initialize_repo")
    @mock.patch("startout.paths.gh_api.check_repo_custom_property")
    def test_starterfile_does_env_replacement(self, mock_check, mock_init_repo):
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

        test_file_expected = {
            "a.txt": "1\nThe line previous to this should be '1'",
            "b.txt": "${THIS_IS_NOT_A_REAL_ENVIRONMENT_VARIABLE_DUCK_1}\nThe line previous to this should be '${THIS_IS_NOT_A_REAL_ENVIRONMENT_VARIABLE_DUCK_1}'",
            "c.txt": "${ONE}\nThe line previous to this should be '${ONE}'"
        }

        test_file_contents = {
            "a.txt": "",
            "b.txt": "",
            "c.txt": ""
        }

        for file_name, _ in test_file_contents.items():
            with open(file_name, "r") as f:
                test_file_contents[file_name] = f.read()

        startout.paths.initialize_path_instance(
            template=self.fully_formed_template_name,
            new_repo_name=self.new_repo_name,
            new_repo_owner=self.new_repo_owner,
            public=self.public,
        )

        for file_name, _ in test_file_contents.items():
            with open(file_name, "r") as f:
                assert test_file_expected[file_name] == f.read()

        for file_name, _ in test_file_contents.items():
            with open(file_name, "w") as f:
                f.write(test_file_contents[file_name])

        with open("final.env", "w") as f:
            f.write(original_file_contents)

