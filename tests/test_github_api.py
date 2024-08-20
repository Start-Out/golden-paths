import json
from unittest import mock

import pytest

from startout.github_api import check_repo_custom_property
from startout.github_api import create_repo_from_temp


class MockCompleteProcess:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout.encode("utf-8")
        self.stderr = stderr.encode("utf-8")


@mock.patch("subprocess.run")
def test_create_repo_from_temp_success(mock_subprocess):
    mock_subprocess.return_value = MockCompleteProcess(0, "", "")

    response = create_repo_from_temp("owner", "repo_name", "template-repo")
    assert response.endswith("repo_name")


@mock.patch("subprocess.run")
def test_create_repo_from_temp_failure(mock_subprocess):
    mock_subprocess.return_value = MockCompleteProcess(1, "", "")

    response = create_repo_from_temp("owner", "repo_name", "template-repo", True)
    assert response is False


@pytest.fixture
def subprocess_run_success():
    with mock.patch("subprocess.run") as m:
        m.return_value.returncode = 0
        m.return_value.stdout = json.dumps(
            [
                {"property_name": "test_property", "value": "test_value"},
            ]
        ).encode()
        yield m


@pytest.fixture
def subprocess_run_failure():
    with mock.patch("subprocess.run") as m:
        m.return_value.returncode = 1
        m.return_value.stdout = "Sample error message".encode()
        yield m


@pytest.mark.usefixtures("subprocess_run_success")
def test_check_repo_custom_property_success():
    template_owner = "owner"
    template_name = "repo"
    custom_properties = {"test_property": "test_value"}

    assert (
        check_repo_custom_property(template_owner, template_name, custom_properties)
        is True
    )


@pytest.mark.usefixtures("subprocess_run_failure")
def test_check_repo_custom_property_failure():
    template_owner = "owner"
    template_name = "repo"
    custom_properties = {"test_property": "test_value"}

    assert (
        check_repo_custom_property(template_owner, template_name, custom_properties)
        is False
    )


@pytest.mark.usefixtures("subprocess_run_success")
def test_check_repo_custom_property_bad_json():
    template_owner = "owner"
    template_name = "repo"
    custom_properties = {"test_property": "test_value"}

    with mock.patch("subprocess.run") as m:
        m.return_value.returncode = 0
        m.return_value.stdout = "bad json".encode()

        assert (
            check_repo_custom_property(template_owner, template_name, custom_properties)
            is False
        )


@pytest.mark.usefixtures("subprocess_run_success")
def test_check_repo_custom_property_wrong_properties():
    template_owner = "owner"
    template_name = "repo"
    custom_properties = {"test_property": "wrong_value"}

    assert (
        check_repo_custom_property(template_owner, template_name, custom_properties)
        is False
    )
