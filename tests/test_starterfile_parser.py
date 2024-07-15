import os
from io import StringIO
from typing import TextIO

import pytest

from startout.module import Module, ScriptModule
from startout.starterfile import parse_starterfile, Starter
from startout.tool import Tool

# replace this with the path to your test data directory
TEST_DATA_DIR = "./resources/starterfiles"


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
    # pseudo code, replace with actual object construction code
    return Starter(...)


@pytest.mark.parametrize("starterfile_path, expected_starter_factory", [
    ("starter1.yaml", build_starter_1),
    # ("starter2.yaml", build_starter_2),
    # add more pairs as needed
])
def test_parse_starterfile(starterfile_path: str, expected_starter_factory):
    """
    Test the parse_starterfile function with different starter files.
    """
    starterfile_path = os.path.join(TEST_DATA_DIR, starterfile_path)
    with open(starterfile_path, 'r') as file:
        actual_starter = parse_starterfile(file)

        expected_starter = expected_starter_factory()

        assert actual_starter == expected_starter
