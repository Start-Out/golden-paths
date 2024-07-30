import pytest

from startout.tool import Tool


def test_init_valid_scripts():
    name = "test_tool"
    dependencies = ["dep1", "dep2"]
    scripts = {
        "install": "echo install",
        "uninstall": "echo uninstall",
        "check": "echo check",
    }

    tool = Tool(name, dependencies, scripts)
    assert tool.name == name
    assert tool.dependencies == dependencies
    assert tool.scripts == scripts


def test_init_missing_install_script():
    name = "test_tool"
    dependencies = ["dep1", "dep2"]
    scripts = {
        "uninstall": "echo uninstall",
    }

    with pytest.raises(TypeError):
        Tool(name, dependencies, scripts)


def test_init_missing_uninstall_script():
    name = "test_tool"
    dependencies = ["dep1", "dep2"]
    scripts = {
        "install": "echo install",
    }

    with pytest.raises(TypeError):
        Tool(name, dependencies, scripts)


def test_init_no_scripts():
    name = "test_tool"
    dependencies = ["dep1", "dep2"]
    scripts = {}

    with pytest.raises(TypeError):
        Tool(name, dependencies, scripts)


@pytest.fixture
def valid_portable_tool():
    scripts = {
        'install': 'exit 0',
        'uninstall': 'exit 0',
        'check': 'exit 0'
    }
    return Tool("test_tool", [], scripts)


@pytest.fixture
def valid_portable_tool_with_failing_scripts():
    scripts = {
        'install': 'exit 1',
        'uninstall': 'exit 1',
        'check': 'exit 1'
    }
    return Tool("failing_test_tool", [], scripts)


def test_check_success(valid_portable_tool):
    assert valid_portable_tool.check()


def test_check_failure(valid_portable_tool_with_failing_scripts):
    assert not valid_portable_tool_with_failing_scripts.check()


# Initialize function tests

def test_initialize_success(valid_portable_tool):
    assert valid_portable_tool.initialize()


def test_initialize_failure(valid_portable_tool_with_failing_scripts):
    assert not valid_portable_tool_with_failing_scripts.initialize()


# Destroy function tests

def test_destroy_success(valid_portable_tool):
    assert valid_portable_tool.destroy()


def test_destroy_failure(valid_portable_tool_with_failing_scripts):
    assert not valid_portable_tool_with_failing_scripts.destroy()
