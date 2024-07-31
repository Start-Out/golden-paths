import pytest

from startout.module import create_module, check_for_key, Module


def test_check_for_key_top_level():
    name = "test"
    key = "init"
    scripts = {
        "init": "some_value",
        "windows": {},
        "mac": {},
        "linux": {}
    }
    # Expect no exception to be raised
    check_for_key(name, key, scripts)


def test_check_for_key_all_platforms():
    name = "test"
    key = "init"
    scripts = {
        "windows": {"init": "some_value"},
        "mac": {"init": "some_value"},
        "linux": {"init": "some_value"}
    }
    # Expect no exception to be raised
    check_for_key(name, key, scripts)


def test_check_for_key_missing_top_level():
    name = "test"
    key = "init"
    scripts = {
        "windows": {},
        "mac": {},
        "linux": {}
    }
    with pytest.raises(TypeError):
        check_for_key(name, key, scripts)


def test_check_for_key_missing_platforms():
    name = "test"
    key = "init"
    scripts = {
        "windows": {"init": "some_value"},
        "mac": {},
        "linux": {}
    }
    with pytest.raises(TypeError):
        check_for_key(name, key, scripts)


@pytest.fixture
def dummy_module():
    return {
        "source": {
            "git": "https://github.com/repo.git"
        },
        "dest": "/dest/path",
        "scripts": {'init': 'exit 0', 'destroy': 'exit 0'},
        "init_options": [
            {
                "env_name": "OPTION",
                "type": "str",
                "default": "1",
                "prompt": "Set option to?"
            },
        ],
        "depends_on": ["module1", "module2"]
    }


@pytest.fixture
def dummy_module_string_dep(dummy_module):
    new_module = dummy_module.copy()
    new_module["depends_on"] = "module1"
    return new_module


def test_create_module(dummy_module):
    result = create_module(dummy_module, "test_module")

    assert isinstance(result, Module), "Must return instance of Module"
    assert result.get_name() == "test_module", "Module name must be as expected"
    assert result.get_dest() == "/dest/path", "Module destination must be as expected"
    assert result.get_source() == "https://github.com/repo.git", "Module source must be as expected"
    assert result.scripts == {"init": "exit 0", "destroy": "exit 0"}, "Script must be as expected"
    assert result.dependencies == ["module1", "module2"], "Dependencies must be as expected"

    assert result.init_options[0].name == dummy_module["init_options"][0][
        "env_name"], "InitOption should be as expected"
    assert result.init_options[0].prompt == dummy_module["init_options"][0][
        "prompt"], "InitOption should be as expected"
    assert result.init_options[0].default == dummy_module["init_options"][0][
        "default"], "InitOption should be as expected"


def test_create_module_with_string_depends_on(dummy_module_string_dep):
    result = create_module(dummy_module_string_dep, "test_module")

    assert result.dependencies == ["module1"], "Dependencies must be as expected when given a string"


def test_create_module_with_empty_module():
    empty_module = {}
    with pytest.raises(Exception):
        create_module(empty_module, "test_module")
