import math
import os
import unittest
from unittest.mock import patch

import pytest

from startout import util
from startout.util import bool_to_yn, bool_to_strings, string_to_bool, calculate_entropy
from startout.util import is_yaml_loadable_type, SchemaError


def test_is_yaml_loadable_type_with_str():
    assert is_yaml_loadable_type("example") == "example"


def test_is_yaml_loadable_type_with_int():
    assert is_yaml_loadable_type(123) == 123


def test_is_yaml_loadable_type_with_float():
    assert is_yaml_loadable_type(123.45) == 123.45


def test_is_yaml_loadable_type_with_bool():
    assert is_yaml_loadable_type(True) == True


def test_is_yaml_loadable_type_with_list():
    assert is_yaml_loadable_type([1, 2, 3]) == [1, 2, 3]


def test_is_yaml_loadable_type_with_dict():
    assert is_yaml_loadable_type({"key": "value"}) == {"key": "value"}


def test_is_yaml_loadable_type_with_none():
    assert is_yaml_loadable_type(None) == None


def test_is_yaml_loadable_type_with_unloadable_type():
    class UnloadableType:
        pass

    with pytest.raises(SchemaError):
        is_yaml_loadable_type(UnloadableType())


def test_calculate_entropy_empty_data():
    data = []
    result = calculate_entropy(data)
    assert result == 0, 'Entropy of empty set should be 0'


def test_calculate_entropy_all_same():
    data = ['a', 'a', 'a', 'a', 'a']
    result = calculate_entropy(data)
    assert result == 0, 'Entropy of set with all same elements should be 0'


def test_calculate_entropy_half_half():
    data = ['a', 'a', 'a', 'b', 'b', 'b']
    result = calculate_entropy(data)
    assert math.isclose(result, 1.0, abs_tol=1e-6), 'Entropy of set with 50-50 distribution should be 1'


def test_calculate_entropy_diff_distribution():
    data = ['a', 'a', 'b', 'b', 'b', 'c']
    result = calculate_entropy(data)
    assert math.isclose(result, 1.4591, abs_tol=1e-4), 'Entropy should match the calculated value'


def test_calculate_entropy_single_distinct():
    data = ['a', 'a', 'a', 'b']
    result = calculate_entropy(data)
    assert math.isclose(result, 0.8112, abs_tol=1e-4), 'Entropy should match the calculated value'


def test_calculate_entropy_all_distinct():
    data = ['a', 'b', 'c', 'd']
    result = calculate_entropy(data)
    assert math.isclose(result, 2.0, abs_tol=1e-6), 'Entropy of set with all distinct elements should be 2'


class TestGetScript(unittest.TestCase):

    @patch("platform.system", return_value="Windows")
    def test_get_script_for_windows(self, _):
        script = "test_script"
        scripts_dict = {
            "test_script": 'echo "Top level script"',
            "windows": {"test_script": 'echo "Windows script"'},
        }
        name = "script_tool"
        expected_result = 'echo "Windows script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    @patch("platform.system", return_value="Darwin")
    def test_get_script_for_mac(self, _):
        script = "test_script"
        scripts_dict = {
            "test_script": 'echo "Top level script"',
            "mac": {"test_script": 'echo "Mac script"'},
        }
        name = "script_tool"
        expected_result = 'echo "Mac script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    @patch("platform.system", return_value="Linux")
    def test_get_script_for_linux(self, _):
        script = "test_script"
        scripts_dict = {
            "test_script": 'echo "Top level script"',
            "linux": {"test_script": 'echo "Linux script"'},
        }
        name = "script_tool"
        expected_result = 'echo "Linux script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    @patch("platform.system", return_value="Linux")
    def test_get_script_top_level(self, _):
        script = "test_script"
        scripts_dict = {
            "test_script": 'echo "Top level script"',
        }
        name = "script_tool"
        expected_result = 'echo "Top level script"'

        result = util.get_script(script, scripts_dict, name)
        self.assertEqual(result, expected_result)

    def test_get_script_none(self):
        script = "not_a_script"
        scripts_dict = {"test_script": "exit 0"}
        name = "script_tool"
        expected_result = None

        with self.assertRaises(TypeError):
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
        os.environ["FOO"] = "Bar"
        self.assertEqual(util.replace_env("Hello ${FOO}"), "Hello Bar")

    def test_replace_env_multiple_variables(self):
        os.environ["USERNAME"] = "John"
        os.environ["HOME"] = "/home/john"
        self.assertEqual(
            util.replace_env("Hello ${USERNAME}, your home directory is ${HOME}"),
            "Hello John, your home directory is /home/john",
        )

    def test_replace_env_no_variables(self):
        self.assertEqual(util.replace_env("Hello world"), "Hello world")

    def test_replace_env_empty_string(self):
        self.assertEqual(util.replace_env(""), "")

    def test_replace_env_variable_not_set(self):
        expected = "Hello ${UNDEFINED_VAR}"
        assert expected == util.replace_env(expected)


class TestBoolConversion(unittest.TestCase):

    def test_bool_to_yn(self):
        self.assertEqual(bool_to_yn(True), "y")
        self.assertEqual(bool_to_yn(False), "n")

    def test_bool_to_strings(self):
        self.assertListEqual(bool_to_strings(True), ["yes", "y", "true"])
        self.assertListEqual(bool_to_strings(False), ["no", "n", "false"])

    def test_string_to_bool(self):
        self.assertEqual(string_to_bool("yes"), True)
        self.assertEqual(string_to_bool("y"), True)
        self.assertEqual(string_to_bool("true"), True)
        self.assertEqual(string_to_bool("no"), False)
        self.assertEqual(string_to_bool("n"), False)
        self.assertEqual(string_to_bool("false"), False)
        self.assertEqual(string_to_bool("unknown"), None)


if __name__ == "__main__":
    unittest.main()
