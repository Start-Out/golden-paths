import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest
from rich.console import Console

from startout import module


@pytest.fixture
def finished_process():
    return subprocess.CompletedProcess(
        args="command", returncode=0,
        stdout="stdout_output", stderr="process.stderr"
    )


@pytest.fixture
def basic_module():
    name = "successfully_initialized_module"
    dest = "/path/to/dest"
    source = "source"
    scripts = {'init': 'exit 0', 'destroy': 'exit 0'}
    return module.Module(name, dest, source, scripts)


@pytest.fixture
def script_module():
    name = "successfully_initialized_module"
    dest = "/path/to/dest"
    source = "exit 0"
    scripts = {'init': 'exit 0', 'destroy': 'exit 0'}
    return module.ScriptModule(name, dest, source, scripts)


@pytest.fixture
def git_module():
    name = "successfully_initialized_module"
    dest = "/path/to/dest"
    source = "git"
    scripts = {'init': 'exit 0', 'destroy': 'exit 0'}
    return module.GitModule(name, dest, source, scripts)


def setup_module_mocks():
    subprocess_run_mocked = mock.Mock()
    subprocess_run_mocked.return_value.returncode = 0
    run_mocked = mock.Mock()
    run_mocked.return_value = ("success message", 0)
    console_mocked = Console()
    log_mocked = os.path.join(Path(__file__).parent, "logs", "startout.log")
    return subprocess_run_mocked, run_mocked, console_mocked, log_mocked


def test_Module_initialize_with_monitor(basic_module):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()
    with mock.patch('shutil.which', return_value='/usr/bin/git'), \
            mock.patch('startout.util.monitored_subprocess', new=subprocess_run_mocked), \
            mock.patch.object(basic_module, 'run', new=run_mocked):
        assert basic_module.initialize(console_mocked, log_mocked)


def test_Module_destroy_with_monitor(basic_module):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()
    with mock.patch('shutil.which', return_value='/usr/bin/git'), \
            mock.patch('startout.util.monitored_subprocess', new=subprocess_run_mocked), \
            mock.patch.object(basic_module, 'run', new=run_mocked):
        assert basic_module.destroy(console_mocked, log_mocked)


@mock.patch('startout.module.monitored_subprocess')
def test_Module_initialize_with_monitor(mock_monitored_subprocess, basic_module, finished_process):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()

    # Define interactions for the monitored_subprocess mock
    mock_monitored_subprocess.return_value = finished_process

    assert basic_module.initialize(console_mocked, log_mocked)


@mock.patch('startout.module.monitored_subprocess')
def test_Module_destroy_with_monitor(mock_monitored_subprocess, basic_module, finished_process):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()

    # Define interactions for the monitored_subprocess mock
    mock_monitored_subprocess.return_value = finished_process

    assert basic_module.destroy(console_mocked, log_mocked)


@mock.patch('startout.module.monitored_subprocess')
def test_ScriptModule_initialize_with_monitor(mock_monitored_subprocess, script_module, finished_process):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()

    # Define interactions for the monitored_subprocess mock
    mock_monitored_subprocess.return_value = finished_process

    assert script_module.initialize(console_mocked, log_mocked)


@mock.patch('startout.module.monitored_subprocess')
def test_ScriptModule_destroy_with_monitor(mock_monitored_subprocess, script_module, finished_process):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()

    # Define interactions for the monitored_subprocess mock
    mock_monitored_subprocess.return_value = finished_process

    assert script_module.destroy(console_mocked, log_mocked)


@mock.patch('startout.module.monitored_subprocess')
def test_GitModule_initialize_with_monitor(mock_monitored_subprocess, git_module, finished_process):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()

    # Define interactions for the monitored_subprocess mock
    mock_monitored_subprocess.return_value = finished_process

    assert git_module.initialize(console_mocked, log_mocked)


@mock.patch('startout.module.monitored_subprocess')
def test_GitModule_destroy_with_monitor(mock_monitored_subprocess, git_module, finished_process):
    # Using extracted setup function
    subprocess_run_mocked, run_mocked, console_mocked, log_mocked = setup_module_mocks()

    # Define interactions for the monitored_subprocess mock
    mock_monitored_subprocess.return_value = finished_process

    assert git_module.destroy(console_mocked, log_mocked)
