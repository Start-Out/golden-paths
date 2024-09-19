import os

from typing import Tuple

from startout.util import is_potentially_sensitive_key_value


class EnvironmentVariableManager:
    def __init__(self):
        self.initial_vars = {k: v for k, v in os.environ.items()}

        self.final_vars = {}

    def capture_final_env(self):
        current_vars = {key: value for key, value in os.environ.items()}
        new_vars = {
            key: value
            for key, value in current_vars.items()
            if key not in self.initial_vars
        }
        self.final_vars.update(new_vars)

        return self.final_vars

    def get_captured_vars(self) -> Tuple[dict, dict]:
        """
        Returns two dictionaries: one containing the not potentially sensitive variables and their values, and the other
        containing the potentially sensitive variables and their values.

        **Returns:**

        - `not_potentially_sensitive` (dict): A dictionary containing the not potentially sensitive variables and their values.
        - `potentially_sensitive` (dict): A dictionary containing the potentially sensitive variables and their values.

        """

        potentially_sensitive = {
            key: value
            for key, value in self.final_vars.items()
            if is_potentially_sensitive_key_value(key, value)
        }
        not_potentially_sensitive = {
            key: value
            for key, value in self.final_vars.items()
            if not is_potentially_sensitive_key_value(key, value)
        }
        return not_potentially_sensitive, potentially_sensitive
