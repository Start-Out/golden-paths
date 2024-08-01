import os
import unittest

import pytest

from startout.starterfile import Starter


class InitOption:
    def __init__(self, name):
        self.name = name
        self.value = None

    def __eq__(self, other):
        return True


class Tool:
    def __init__(self, name, mock_check: bool = False, mock_initialize: bool = False, mock_destroy: bool = False):
        self.name = name
        self.mock_check = mock_check
        self.mock_destroy = mock_destroy
        self.mock_initialize = mock_initialize

    def check(self):
        return self.mock_check  # mock uninitialized tool

    def initialize(self):
        return self.mock_initialize  # mock successful installation

    def destroy(self):
        return self.mock_destroy


class Module:
    def __init__(self, name, mock_check: bool = False, mock_initialize: bool = False, mock_destroy: bool = False,
                 mock_init_options: bool = False):
        self.name = name
        self.mock_check = mock_check
        self.mock_destroy = mock_destroy
        self.mock_initialize = mock_initialize

        if mock_init_options:
            self.init_options = [InitOption(str(i)) for i in range(5)]

    def check(self):
        return self.mock_check  # mock uninitialized module

    def initialize(self):
        return self.mock_initialize  # mock successful installation

    def destroy(self):
        return self.mock_destroy


class TestStarter(unittest.TestCase):
    def setUp(self):
        self.mock_modules = [Module("", mock_init_options=True) for _ in range(5)]
        self.mock_tools = [Tool("") for _ in range(5)]

        self.module_deps = [['mod1', 'mod2'], ['mod3', 'mod4', 'mod5']]
        self.tool_deps = [['tool1', 'tool2'], ['tool3', 'tool4', 'tool5']]

        self.starter_successful_init = Starter(self.mock_modules, self.mock_tools, self.module_deps, self.tool_deps)
        self.starter_failure_init = Starter([], [], [], [])

    def test_starter_init(self):
        assert self.starter_successful_init.modules == self.mock_modules
        assert self.starter_successful_init.tools == self.mock_tools
        assert self.starter_successful_init.module_dependencies == self.module_deps
        assert self.starter_successful_init.tool_dependencies == self.tool_deps

    def test_get_init_options(self):
        assert self.starter_successful_init.get_init_options() == [("", InitOption(str(i))) for i in range(5)]

    def test_set_init_options(self):
        test_options = {
            ("", "1"): "Value"
        }
        self.starter_successful_init.set_init_options(test_options)

        assert os.environ["1"] == "Value"
        _, options = self.starter_successful_init.get_init_options()[0]
        option = [option for option in options if option.name == "1"][0]
        assert option.value == "Value"

    def test_up_succeeds(self):
        assert self.starter_successful_init.up()

    def test_up_fails(self):
        assert not self.starter_failure_init.up()


def test_install_tools_no_tools():
    starter = Starter([], [], [], [])
    assert not starter.install_tools(), "Should return False when there are no tools to install."


def test_install_tools_all_tools_installed():
    # Mock already installed tools
    tools = [Tool(str(i), True, True, True) for i in range(10)]
    starter = Starter([], tools, [], [[t.name for t in tools]])
    assert starter.install_tools(), "Should return True when all tools are already installed."


def test_install_tools_all_tools_uninstalled():
    # Mock uninitialized tools
    tools = [Tool(str(i), False, True, True) for i in range(10)]
    starter = Starter([], tools, [], [[t.name for t in tools]])
    assert starter.install_tools(), "Should return True when all tools are successfully installed."


def test_install_tools_fail_early():
    # Mock tools
    tools = [Tool(str(i), False, (i != 5), True) for i in range(10)]
    starter = Starter([], tools, [], [[t.name for t in tools]])
    assert not starter.install_tools(fail_early=True), "Should return False as tool '5' fails to initialize."


def test_install_tools_teardown_on_failure():
    # Mock tools
    tools = [Tool(str(i), False, (i != 5), (i != 6)) for i in range(10)]
    starter = Starter([], tools, [], [[t.name for t in tools]])
    with pytest.raises(SystemExit):
        starter.install_tools(teardown_on_failure=True), "Should raise SystemExit as tool '6' fails to destroy."


def test_install_tools_no_teardown_on_failure():
    # Mock tools
    tools = [Tool(str(i), False, (i != 5), (i != 6)) for i in range(10)]
    starter = Starter([], tools, [], [[t.name for t in tools]])
    assert not starter.install_tools(teardown_on_failure=False), "Should return False as tool '5' fails to initialize."


def test_install_modules_no_modules():
    starter = Starter([], [], [], [])
    assert not starter.install_modules(), "Should return False when there are no modules to install."


def test_install_modules_all_modules_installed():
    # Mock already installed modules
    modules = [Module(str(i), True, True, True) for i in range(10)]
    starter = Starter(modules, [], [[m.name for m in modules]], [])
    assert starter.install_modules(), "Should return True when all modules are already installed."


def test_install_modules_all_modules_uninstalled():
    # Mock uninitialized modules
    modules = [Module(str(i), False, True, True) for i in range(10)]
    starter = Starter(modules, [], [[m.name for m in modules]], [])
    assert starter.install_modules(), "Should return True when all modules are successfully installed."


def test_install_modules_fail_early():
    # Mock modules
    modules = [Module(str(i), False, (i != 5), True) for i in range(10)]
    starter = Starter(modules, [], [[m.name for m in modules]], [])
    assert not starter.install_modules(fail_early=True), "Should return False as module '5' fails to initialize."


def test_install_modules_teardown_on_failure():
    # Mock modules
    modules = [Module(str(i), False, (i != 5), (i != 6)) for i in range(10)]
    starter = Starter(modules, [], [[m.name for m in modules]], [])
    with pytest.raises(SystemExit):
        starter.install_modules(teardown_on_failure=True), "Should raise SystemExit as module '6' fails to destroy."


def test_install_modules_no_teardown_on_failure():
    # Mock tools
    modules = [Module(str(i), False, (i != 5), (i != 6)) for i in range(10)]
    starter = Starter(modules, [], [[m.name for m in modules]], [])
    assert not starter.install_modules(
        teardown_on_failure=False), "Should return False as module '5' fails to initialize."


if __name__ == '__main__':
    unittest.main()
