import unittest
from unittest.mock import patch

from startout.paths import prompt_init_option, InitOption, console


class TestPromptInitOption(unittest.TestCase):

    # Setup and teardown methods for the test class
    def setUp(self):
        self.option = InitOption(
            {
                "default": "default_value",
                "env_name": "name",
                "prompt": "Prompt for input: ",
            }
        )

    def tearDown(self):
        pass

    @patch.object(console, "input")
    def test_prompt_init_option_when_default_type_bool_and_response_yes(
        self, input_mock
    ):
        input_mock.return_value = "y"
        self.option.default = True
        self.assertEqual(prompt_init_option(self.option), True)

    @patch.object(console, "input")
    def test_prompt_init_option_when_default_type_bool_and_response_no(
        self, input_mock
    ):
        input_mock.return_value = "n"
        self.option.default = True
        self.assertEqual(prompt_init_option(self.option), False)

    @patch.object(console, "input")
    def test_prompt_init_option_when_default_type_int(self, input_mock):
        input_mock.return_value = "10"
        self.option.default = 0
        self.assertEqual(prompt_init_option(self.option), 10)

    @patch.object(console, "input")
    def test_prompt_init_option_when_default_type_float(self, input_mock):
        input_mock.return_value = "10.5"
        self.option.default = float(0)
        self.assertEqual(prompt_init_option(self.option), 10.5)

    @patch.object(console, "input")
    def test_prompt_init_option_when_default_type_is_other(self, input_mock):
        input_mock.return_value = "response"
        self.option.default = "default"
        self.assertEqual(prompt_init_option(self.option), "response")

    @patch.object(console, "input")
    def test_prompt_init_option_when_input_empty_return_default(self, input_mock):
        input_mock.return_value = ""
        self.option.default = "default_value"
        self.assertEqual(prompt_init_option(self.option), "default_value")

    @patch.object(console, "input")
    def test_prompt_init_option_when_input_invalid(self, input_mock):
        input_mock.side_effect = [
            "zero",
            "1",
        ]  # First input is invalid, second is valid.
        self.option.default = 0
        self.assertEqual(prompt_init_option(self.option), 1)


if __name__ == "__main__":
    unittest.main()
