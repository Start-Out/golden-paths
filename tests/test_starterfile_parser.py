import os
from io import StringIO
from typing import TextIO

import pytest

from startout.starterfile import parse_starterfile, Starter

# replace this with the path to your test data directory
TEST_DATA_DIR = "./resources/starterfiles"


# factories for constructing expected Starter objects
def build_starter_1():
    # pseudo code, replace with actual object construction code
    return Starter(...)


def build_starter_2():
    # pseudo code, replace with actual object construction code
    return Starter(...)


@pytest.mark.parametrize("starterfile_path, expected_starter_factory", [
    ("starter1.yaml", build_starter_1),
    ("starter2.yaml", build_starter_2),
    # add more pairs as needed
])
def test_parse_starterfile(starterfile_path: str, expected_starter_factory):
    """
    Test the parse_starterfile function with different starter files.
    """
    starterfile_path = os.path.join(TEST_DATA_DIR, starterfile_path)
    with open(starterfile_path, 'r') as file:
        starterfile_stream: TextIO = StringIO(file.read())
        actual_starter = parse_starterfile(starterfile_stream)

        expected_starter = expected_starter_factory()

        assert actual_starter == expected_starter
