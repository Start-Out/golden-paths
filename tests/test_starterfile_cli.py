import os
import unittest
from unittest import mock
from unittest.mock import patch

from parameterized import parameterized

import startout.paths


class Starter:
    def __init__(self, name, mock_init_options: list = None, mock_up_succeeds: bool = True):
        self.name = name
        self.mock_init_options = mock_init_options
        self.mock_up_succeeds = mock_up_succeeds

    def get_init_options(self):
        if self.mock_init_options is not None:
            return self.mock_init_options

        return []

    def set_init_options(self, _):
        pass

    def up(self):
        return self.mock_up_succeeds


class InitOption:
    def __init__(self, name):
        self.name = name


# @mock.patch('startout.paths.prompt_init_option')
# @mock.patch('startout.paths.parse_starterfile')
# @mock.patch('startout.paths.open')
# @mock.patch('startout.paths.os.chdir')
# @mock.patch('startout.paths.initialize_repo')
# @mock.patch('startout.paths.new_repo_owner_interactive')
# @mock.patch('startout.paths.gh_api.check_repo_custom_property')
# @mock.patch('startout.paths.re.match')
class TestStarterFileCLI(unittest.TestCase):

    def setUp(self):
        self.safe_dir = os.getcwd()

        # Test parameters
        self.fully_formed_template_name = 'Github/Repository'
        self.startout_path_template_name = 'test-test'
        self.new_repo_name = 'NewRepo'
        self.new_repo_owner = 'Owner'
        self.public = True
        self.created_repo_path = "path/to/repo"

        self.console_patcher = patch('startout.paths.console', autospec=True)
        self.mock_console = self.console_patcher.start()

        self.mock_starter_valid = Starter("MockStarter")

    def tearDown(self):
        self.console_patcher.stop()
        os.chdir(self.safe_dir)

    # fmt: off
    @parameterized.expand([
        "tests/resources/starterfiles/starter1.yaml",  # Basic Starterfile
        "tests/resources/starterfiles/starter2.yaml",  # Starterfile with dependencies
    ])
    # fmt: on
    def test_starterfile_only_up(self, starterfile_path):
        _ = startout.paths.starterfile_up_only(starterfile_path)

    # fmt: off
    @parameterized.expand([
        "tests/resources/starterfiles/circular_module_starter.yaml",  # Basic Starterfile
        "tests/resources/starterfiles/circular_tool_starter.yaml",  # Starterfile with dependencies
    ])
    # fmt: on
    def test_starterfiles_fail_on_up(self, starterfile_path):
        with self.assertRaises(SystemExit):
            _ = startout.paths.starterfile_up_only(starterfile_path)
