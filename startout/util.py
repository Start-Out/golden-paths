import os
import platform
import re
import shlex
import shutil
import subprocess
import sys


def type_tool(type_str: str) -> type or None:
    """
    Return the corresponding Python type based on the input string.

    :param type_str: A string representing the desired Python type.
                     Possible values are "int", "float", "str", or "string".
    :return: The corresponding Python type if it exists, otherwise None.
    """
    types = {
        "int": int,
        "float": float,
        "str": str,
        "string": str,
    }
    try:
        return types[type_str.lower()]
    except KeyError:
        return None


def replace_env(string: str) -> str:
    """
    :param string: The string in which to replace environment variable placeholders.
    :return: The string with all environment variable placeholders replaced with their corresponding values.

    This method takes a string as input and replaces all occurrences of environment variable placeholders in the
    format ${variable_name} with their corresponding values. It uses regular expressions to find all placeholders
    in the string, then checks if the corresponding environment variable is set. If the variable is set, it replaces
    the placeholder with the variable's value. If the variable is not set, it raises a ValueError.

    Example usage:

    >>> replace_env("Hello ${USERNAME}, your home directory is ${HOME}")
    'Hello John, your home directory is /home/john'
    """
    pattern = re.compile(r'\$\{(.+?)}')
    matches = pattern.findall(string)

    for match in matches:
        env_value = os.getenv(match)
        if env_value is None:
            raise ValueError(f'Environment variable {match} not set.')
        string = string.replace(f'${{{match}}}', env_value)

    return string


def run_script_with_env_substitution(script_str: str, verbose: bool = False) -> tuple[str, int]:
    """
    Run a script with environment variable substitution. If the script fails to run as a shlex'd list, run it as a
    string instead.

    :param verbose: Whether to print warning if the script fails to run as a shlex'd list or not.
    :param script_str: The script to be executed as a string.
    :return: A tuple containing the stdout output and the return code of the script.
    """

    # Inject environment variables
    substituted_script = replace_env(script_str)
    multiline = "\n" in substituted_script

    _script = shlex.split(substituted_script)

    try:
        # If shutil can't find the command or the script is multiline, run as shell
        if shutil.which(_script[0]) is None or multiline:
            if verbose:
                print(f"'{_script[0]}' is not installed. Trying script in shell.", file=sys.stderr)

            _os = platform.system().lower()
            windows = _os in ["windows", "win32"]

            if windows:
                windows_shell = "pwsh" if shutil.which("pwsh") is not None else "powershell"
                result = subprocess.run([
                    windows_shell,
                    "-Command",
                    substituted_script
                ])
            else:
                result = subprocess.run(
                    substituted_script,
                    shell=True,
                    text=True,
                    capture_output=True
                )
        # Else, run the shlex'd cmd list
        else:
            result = subprocess.run(
                _script,
                text=True,
                capture_output=True
            )
    except OSError as e:
        return f"{e}", 1
    except subprocess.CalledProcessError as e:
        return f"{e.stdout}\n{e.stderr}", e.returncode

    return result.stdout, result.returncode
