import pytest
from unittest import mock
from startout import module


@pytest.fixture
def git_module():
    name = "successfully_initialized_module"
    dest = "/path/to/dest"
    source = "git"
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
    return module.GitModule(name, dest, source, scripts, dependencies, init_options)


def test_GitModule_initialization_error(git_module):
    git_module.source = "https://github.com/username/repo.git"
    git_module.dest = "/path/to/destination"

    with mock.patch("shutil.which", return_value=None):
        with pytest.raises(OSError):
            git_module.initialize()


def test_GitModule_initialization_fail_cloning(git_module):
    git_module.source = "https://github.com/username/repo.git"
    git_module.dest = "/path/to/destination"

    mocked_run = mock.Mock(return_value=mock.Mock(returncode=1))
    patched_run = mock.patch("subprocess.run", new=mocked_run)

    with mock.patch("shutil.which", return_value="/usr/bin/git"), patched_run:
        assert not git_module.initialize()


def test_GitModule_initialization_fail_init_script(git_module):
    git_module.source = "https://github.com/username/repo.git"
    git_module.dest = "/path/to/destination"

    subprocess_run_mocked = mock.Mock()
    subprocess_run_mocked.return_value.returncode = 0
    run_mocked = mock.Mock()
    run_mocked.return_value = ("error message", 1)

    with mock.patch("shutil.which", return_value="/usr/bin/git"), mock.patch(
        "subprocess.run", new=subprocess_run_mocked
    ), mock.patch.object(git_module, "run", new=run_mocked):
        assert not git_module.initialize()


def test_GitModule_initialization_success(git_module):
    git_module.source = "https://github.com/username/repo.git"
    git_module.dest = "/path/to/destination"

    subprocess_run_mocked = mock.Mock()
    subprocess_run_mocked.return_value.returncode = 0
    run_mocked = mock.Mock()
    run_mocked.return_value = ("success message", 0)

    with mock.patch("shutil.which", return_value="/usr/bin/git"), mock.patch(
        "subprocess.run", new=subprocess_run_mocked
    ), mock.patch.object(git_module, "run", new=run_mocked):
        assert git_module.initialize()
