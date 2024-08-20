import pytest
from unittest import mock
from startout import module


@pytest.fixture
def script_module():
    name = "successfully_initialized_module"
    dest = "/path/to/dest"
    source = "script"
    scripts = {"init": "exit 0", "destroy": "exit 0"}
    dependencies = ["dependency1", "dependency2"]
    init_options = [
        {
            "env_name": "test",
            "type": "str",
            "default": "default_val",
            "prompt": "prompt_msg",
        }
    ]
    return module.ScriptModule(name, dest, source, scripts, dependencies, init_options)


def test_ScriptModule_initialization_error(script_module):
    script_module.source = "/invalid/script/path.sh"
    script_module.dest = "/path/to/destination"

    with mock.patch("os.path.isfile", return_value=False):
        assert not script_module.initialize()


def test_ScriptModule_initialization_fail_execution(script_module):
    script_module.source = "/valid/script/path.sh"
    script_module.dest = "/path/to/destination"

    run_mocked = mock.Mock()
    run_mocked.return_value = ("error message", 1)

    with mock.patch("os.path.isfile", return_value=True), mock.patch.object(
        script_module, "run", new=run_mocked
    ):
        assert not script_module.initialize()


def test_ScriptModule_initialization_fail_init_script(script_module):
    script_module.source = "/valid/script/path.sh"
    script_module.dest = "/path/to/destination"

    subprocess_run_mocked = mock.Mock()
    subprocess_run_mocked.return_value.returncode = 0
    run_mocked = mock.Mock()
    run_mocked.return_value = ("error message", 1)

    with mock.patch("os.path.isfile", return_value=True), mock.patch(
        "subprocess.run", new=subprocess_run_mocked
    ), mock.patch.object(script_module, "run", new=run_mocked):
        assert not script_module.initialize()


def test_ScriptModule_initialization_success(script_module):
    script_module.source = "/valid/script/path.sh"
    script_module.dest = "/path/to/destination"

    subprocess_run_mocked = mock.Mock()
    subprocess_run_mocked.return_value.returncode = 0
    run_mocked = mock.Mock()
    run_mocked.return_value = ("success message", 0)

    with mock.patch("os.path.isfile", return_value=True), mock.patch(
        "subprocess.run", new=subprocess_run_mocked
    ), mock.patch.object(script_module, "run", new=run_mocked):
        assert script_module.initialize()
