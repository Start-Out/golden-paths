import unittest
from unittest import mock
from unittest.mock import patch

import startout.paths


class Starter:
    def __init__(
        self, name, mock_init_options: list = None, mock_up_succeeds: bool = True
    ):
        self.name = name
        self.mock_init_options = mock_init_options
        self.mock_up_succeeds = mock_up_succeeds
        self.env_dump_file = None
        self.env_dump_mode = None

    def get_init_options(self):
        if self.mock_init_options is not None:
            return self.mock_init_options

        return []

    def set_init_options(self, _):
        pass

    def up(self, _, __):
        return self.mock_up_succeeds


class InitOption:
    def __init__(self, name):
        self.name = name


@mock.patch("startout.paths.prompt_init_option")
@mock.patch("startout.paths.parse_starterfile")
@mock.patch("startout.paths.open")
@mock.patch("startout.paths.os.chdir")
@mock.patch("startout.paths.initialize_repo")
@mock.patch("startout.paths.new_repo_owner_interactive")
@mock.patch("startout.paths.gh_api.check_repo_custom_property")
@mock.patch("startout.paths.re.match")
class TestInitializePathInstance(unittest.TestCase):

    def setUp(self):
        # Test parameters
        self.fully_formed_template_name = "Github/Repository"
        self.startout_path_template_name = "test-test"
        self.new_repo_name = "NewRepo"
        self.new_repo_owner = "Owner"
        self.public = True
        self.created_repo_path = "path/to/repo"

        self.console_patcher = patch("startout.paths.console", autospec=True)
        self.mock_console = self.console_patcher.start()

        self.mock_starter_valid = Starter("MockStarter")

    def tearDown(self):
        self.console_patcher.stop()

    def test_initialize_path_instance_fully_formed(
        self,
        mock_re,
        mock_check,
        mock_new_owner,
        mock_init_repo,
        mock_chdir,
        mock_open,
        mock_parse,
        mock_prompt,
    ):
        #####################
        # Define interactions
        mock_re.return_value = True
        mock_check.return_value = True
        mock_new_owner.return_value = "Owner"
        mock_init_repo.return_value = True
        mock_parse.side_effect = (
            lambda x: x
        )  # This function will simply return what it received
        mock_prompt.side_effect = (
            lambda x: x
        )  # This function will simply return what it received
        #####################

        _ = startout.paths.initialize_path_instance(
            self.fully_formed_template_name,
            self.new_repo_name,
            self.new_repo_owner,
            self.public,
        )

        mock_re.assert_called_once_with(
            r"^[^/]*/[^/]*$", self.fully_formed_template_name
        )

    def test_initialize_path_instance_invalid_template(
        self,
        mock_re,
        mock_check,
        mock_new_owner,
        mock_init_repo,
        mock_chdir,
        mock_open,
        mock_parse,
        mock_prompt,
    ):
        #####################
        # Define interactions
        mock_re.return_value = False  # The template defined is not a valid reference
        #####################

        with self.assertRaises(SystemExit):
            startout.paths.initialize_path_instance(
                self.fully_formed_template_name,
                self.new_repo_name,
                self.new_repo_owner,
                self.public,
            )

    def test_initialize_path_instance_startout_valid_path(
        self,
        mock_re,
        mock_check,
        mock_new_owner,
        mock_init_repo,
        mock_chdir,
        mock_open,
        mock_parse,
        mock_prompt,
    ):
        #####################
        # Define interactions
        self.mock_console.input.side_effect = [
            ""
        ]  # Simulate pressing enter to take default
        mock_re.return_value = False  # The template defined is not a valid reference
        mock_check.return_value = True  # The template is a valid Path
        mock_init_repo.return_value = (
            self.created_repo_path
        )  # Successfully initialized the repo
        mock_parse.return_value = self.mock_starter_valid
        #####################

        startout.paths.initialize_path_instance(
            self.startout_path_template_name,
            self.new_repo_name,
            self.new_repo_owner,
            self.public,
        )

    def test_initialize_path_instance_non_startout_non_path(
        self,
        mock_re,
        mock_check,
        mock_new_owner,
        mock_init_repo,
        mock_chdir,
        mock_open,
        mock_parse,
        mock_prompt,
    ):
        #####################
        # Define interactions
        self.mock_console.input.side_effect = [
            "Not-Start-Out"
        ]  # Give a Non-StartOut owner
        mock_re.return_value = False  # The template defined is not a valid reference
        mock_check.return_value = False  # The template is NOT a valid Path
        #####################

        startout.paths.initialize_path_instance(
            self.startout_path_template_name,
            self.new_repo_name,
            self.new_repo_owner,
            self.public,
        )

        # Assert that there was no attempt to parse a Starterfile
        mock_chdir.assert_not_called()

    def test_initialize_path_with_interactive_new_owner(
        self,
        mock_re,
        mock_check,
        mock_new_owner,
        mock_init_repo,
        mock_chdir,
        mock_open,
        mock_parse,
        mock_prompt,
    ):
        #####################
        # Define interactions
        mock_re.return_value = True
        mock_check.return_value = True
        mock_init_repo.return_value = True
        mock_parse.side_effect = (
            lambda x: x
        )  # This function will simply return what it received
        mock_prompt.side_effect = (
            lambda x: x
        )  # This function will simply return what it received

        mock_check.mock_new_owner = (
            "goose"  # Simulate interactively prompting for the owner if not defined
        )
        #####################

        _ = startout.paths.initialize_path_instance(
            self.fully_formed_template_name, self.new_repo_name, public=self.public
        )

        # Assert that there was an attempt to parse a Starterfile
        mock_chdir.assert_called()

    def test_initialize_path_init_repo_fails(
        self,
        mock_re,
        mock_check,
        mock_new_owner,
        mock_init_repo,
        mock_chdir,
        mock_open,
        mock_parse,
        mock_prompt,
    ):
        #####################
        # Define interactions
        mock_re.return_value = True
        mock_check.return_value = True
        mock_init_repo.return_value = False
        #####################

        # Assert that the program exits with a failure
        with self.assertRaises(SystemExit):
            _ = startout.paths.initialize_path_instance(
                "Valid/Enough", self.new_repo_name, self.new_repo_owner, self.public
            )

    def test_initialize_path_init_options(
        self,
        mock_re,
        mock_check,
        mock_new_owner,
        mock_init_repo,
        mock_chdir,
        mock_open,
        mock_parse,
        mock_prompt,
    ):
        #####################
        # Define interactions
        self.mock_console.input.side_effect = [
            ""
        ]  # Simulate pressing enter to take default
        mock_re.return_value = False  # The template defined is not a valid reference
        mock_check.return_value = True  # The template is a valid Path
        mock_init_repo.return_value = (
            self.created_repo_path
        )  # Successfully initialized the repo

        # Mock the prompt of an InitOption
        self.mock_starter_valid.mock_init_options = [
            ("module_name", [InitOption("init_option")])
        ]
        mock_parse.return_value = self.mock_starter_valid

        mock_prompt.return_value = "option_value"
        #####################

        startout.paths.initialize_path_instance(
            self.startout_path_template_name,
            self.new_repo_name,
            self.new_repo_owner,
            self.public,
        )
