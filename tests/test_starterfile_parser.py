import os
import unittest

import pytest
import schema

from startout.module import ScriptModule
from startout.starterfile import parse_starterfile, Starter
from startout.tool import Tool

# replace this with the path to your test data directory
TEST_DATA_DIR = "./tests/resources/starterfiles"


# factories for constructing expected Starter objects
def build_starter_1():
    return Starter(
        tools=[
            Tool(
                name="tool",
                scripts={
                    "check": "exit 0",
                    "install": "exit 0",
                    "uninstall": "exit 0"
                },
                dependencies=None
            )
        ],
        modules=[
            ScriptModule(
                name="module",
                dest="path/to/module",
                source="exit 0",
                scripts={
                    "init": "exit 0",
                    "destroy": "exit 0"
                }
            )
        ],
        tool_dependencies=[["tool"]], module_dependencies=[["module"]]
    )


def build_starter_2():
    return Starter(
        tools=[
            Tool(
                name="tool",
                scripts={
                    "check": "exit 0",
                    "install": "exit 0",
                    "uninstall": "exit 0"
                },
                dependencies=None
            ),
            Tool(
                name="dependent_tool",
                scripts={
                    "check": "exit 0",
                    "install": "exit 0",
                    "uninstall": "exit 0"
                },
                dependencies=["tool"]
            )
        ],
        modules=[
            ScriptModule(
                name="module",
                dest="path/to/module",
                source="exit 0",
                scripts={
                    "init": "exit 0",
                    "destroy": "exit 0"
                }
            ),
            ScriptModule(
                name="dependent_module",
                dest="2/equals/TWO",
                source="exit 0",
                scripts={
                    "init": "echo HAHAHA\nexit 0\n",
                    "destroy": "exit 0"
                },
                dependencies=["module"]
            )
        ],
        tool_dependencies=[["tool"], ["dependent_tool"]],
        module_dependencies=[["module"], ["dependent_module"]]
    )


@pytest.mark.parametrize("starterfile_path, expected_starter_factory", [
    ("starter1.yaml", build_starter_1),
    ("starter2.yaml", build_starter_2),
    # add more pairs as needed
])
def test_parse_starterfile_succeeds(starterfile_path: str, expected_starter_factory):
    """
    Test the parse_starterfile function with different starter files.
    """
    starterfile_path = os.path.join(TEST_DATA_DIR, starterfile_path)
    with open(starterfile_path, 'r') as file:
        actual_starter = parse_starterfile(file)

        expected_starter = expected_starter_factory()

        assert actual_starter == expected_starter


class TestParseStarterfileFails(unittest.TestCase):
    def setUp(self):
        self.broken = "non_starter.yaml"

        self.circular_tools = "circular_tool_starter.yaml"
        self.circular_modules = "circular_module_starter.yaml"

    def test_parse_starterfile_fails_with_circular_dependencies(self):
        starterfile_path = os.path.join(TEST_DATA_DIR, self.circular_tools)
        with open(starterfile_path, 'r') as file:
            with self.assertRaises(SystemExit):
                parse_starterfile(file)

        starterfile_path = os.path.join(TEST_DATA_DIR, self.circular_modules)
        with open(starterfile_path, 'r') as file:
            with self.assertRaises(SystemExit):
                parse_starterfile(file)

    def test_parse_starterfile_fails_with_invalid_file(self):
        starterfile_path = os.path.join(TEST_DATA_DIR, self.broken)
        with open(starterfile_path, 'r') as file:
            with self.assertRaises(schema.SchemaMissingKeyError):
                parse_starterfile(file)
