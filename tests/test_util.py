import os
import unittest
from unittest.mock import patch

from startout import util


class TestGetScript(unittest.TestCase):

    @patch('platform.system', return_value='Windows')
    def test_get_script_for_windows(self, _):
        script = 'test_script'
        scripts_dict = {
            'test_script': 'echo "Top level script"',
            'windows': {
                'test_script': 'echo "Windows script"'
            }
        }
        name = "script_tool"
        expected_result = 'echo "Windows script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    @patch('platform.system', return_value='Darwin')
    def test_get_script_for_mac(self, _):
        script = 'test_script'
        scripts_dict = {
            'test_script': 'echo "Top level script"',
            'mac': {
                'test_script': 'echo "Mac script"'
            }
        }
        name = "script_tool"
        expected_result = 'echo "Mac script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    @patch('platform.system', return_value='Linux')
    def test_get_script_for_linux(self, _):
        script = 'test_script'
        scripts_dict = {
            'test_script': 'echo "Top level script"',
            'linux': {
                'test_script': 'echo "Linux script"'
            }
        }
        name = "script_tool"
        expected_result = 'echo "Linux script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    @patch('platform.system', return_value='Linux')
    def test_get_script_top_level(self, _):
        script = 'test_script'
        scripts_dict = {
            'test_script': 'echo "Top level script"',
        }
        name = "script_tool"
        expected_result = 'echo "Top level script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    def test_get_script_none(self):
        script = 'not_a_script'
        scripts_dict = {
            'test_script': 'exit 0'
        }
        name = "script_tool"
        expected_result = None

        with self.assertRaises(ValueError):
            util.get_script(script, scripts_dict, name)


class TestTypeTool(unittest.TestCase):

    def test_type_tool_when_str_is_int(self):
        result = util.type_tool("int")
        self.assertEqual(result, int)

    def test_type_tool_when_str_is_float(self):
        result = util.type_tool("float")
        self.assertEqual(result, float)

    def test_type_tool_when_str_is_str(self):
        result = util.type_tool("str")
        self.assertEqual(result, str)

    def test_type_tool_when_str_is_string(self):
        result = util.type_tool("string")
        self.assertEqual(result, str)

    def test_type_tool_when_str_is_non_existent_type(self):
        result = util.type_tool("non_existent_type")
        self.assertIsNone(result)


class TestReplaceEnv(unittest.TestCase):

    def test_replace_env_single_variable(self):
        os.environ['FOO'] = 'Bar'
        self.assertEqual(util.replace_env("Hello ${FOO}"), 'Hello Bar')

    def test_replace_env_multiple_variables(self):
        os.environ['USERNAME'] = 'John'
        os.environ['HOME'] = '/home/john'
        self.assertEqual(util.replace_env('Hello ${USERNAME}, your home directory is ${HOME}'),
                         'Hello John, your home directory is /home/john')

    def test_replace_env_no_variables(self):
        self.assertEqual(util.replace_env('Hello world'), 'Hello world')

    def test_replace_env_empty_string(self):
        self.assertEqual(util.replace_env(''), '')

    def test_replace_env_variable_not_set(self):
        with self.assertRaises(ValueError):
            util.replace_env('Hello ${UNDEFINED_VAR}')


if __name__ == '__main__':
    unittest.main()
