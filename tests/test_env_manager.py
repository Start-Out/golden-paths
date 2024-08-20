import os
from typing import Tuple
from unittest.mock import patch
import pytest
from startout.env_manager import EnvironmentVariableManager


@pytest.fixture
def test_env_vars():
    return {"TEST_VAR_1": "VALUE_1", "TEST_VAR_2": "VALUE_2"}


@pytest.fixture
def sensitive_env_vars():
    return {"SECRET_VAR_3": "VALUE_3", "SECRET_VAR_4": "VALUE_4", "INNOCUOUS_VAR_5": "Fhd@aF+88nZV$h4YFe445"}


def test_capture_final_env(test_env_vars, sensitive_env_vars):
    with patch.dict(os.environ, {**test_env_vars, **sensitive_env_vars}):
        env_var_manager = EnvironmentVariableManager()
        os.environ["NEW_VAR"] = "NEW_VALUE"
        output = env_var_manager.capture_final_env()
        assert output == {"NEW_VAR": "NEW_VALUE"}


def test_get_captured_vars(test_env_vars, sensitive_env_vars):
    env_var_manager = EnvironmentVariableManager()

    # Adding the environment variables from test_env_vars and sensitive_env_vars
    for key, value in {**test_env_vars, **sensitive_env_vars}.items():
        os.environ[key] = value

    env_var_manager.capture_final_env()
    not_sens, sens = env_var_manager.get_captured_vars()
    assert not_sens == test_env_vars
    assert sens == sensitive_env_vars