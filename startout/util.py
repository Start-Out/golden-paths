import math
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from collections import deque
from io import TextIOWrapper
from pathlib import Path
from typing import List, Dict, Tuple

import click
import rich
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from schema import SchemaError


class MonitorOutput:
    def __init__(self, title: str, subtitle: str, console: Console, log_path: Path):
        self.title = title
        self.subtitle = subtitle
        self.console = console
        self.log_path = log_path


SENSITIVE_PATTERNS = [
    re.compile(r"API_KEY", re.IGNORECASE),
    re.compile(r"TOKEN", re.IGNORECASE),
    re.compile(r"PASSWORD", re.IGNORECASE),
    re.compile(r"SECRET", re.IGNORECASE),
    re.compile(r"PRIVATE_KEY", re.IGNORECASE),
    re.compile(r"ACCESS_KEY", re.IGNORECASE),
]

HIGH_ENTROPY_THRESHOLD = 3.5


def calculate_entropy(data):
    if not data:
        return 0
    entropy = 0
    for x in set(data):
        p_x = data.count(x) / len(data)
        entropy += -p_x * math.log2(p_x)
    return entropy


def is_potentially_sensitive_key_value(key, value):
    # Check if key matches sensitive patterns
    if any(pattern.search(key) for pattern in SENSITIVE_PATTERNS):
        return True
    # Check if value has high entropy
    if calculate_entropy(value) > HIGH_ENTROPY_THRESHOLD:
        return True
    return False


def validate_str_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def is_yaml_loadable_type(value):
    yaml_loadable_types = (str, int, float, bool, list, dict, type(None))
    if not isinstance(value, yaml_loadable_types):
        raise SchemaError(
            f"Provided type {type(value).__name__} cannot be loaded by yaml.safe_load"
        )
    return value


def bool_to_yn(bool_input: bool) -> str:
    """
    Converts a boolean value to a 'y' or 'n' string representation.

    :param bool_input: The boolean value to be converted.
        - True: Represented by 'y'
        - False: Represented by 'n'
    :return: The string representation of the boolean value.
        - 'y' if bool_input is True
        - 'n' if bool_input is False

    """
    lex = {True: "y", False: "n"}

    return lex[bool_input]


def bool_to_strings(bool_input: bool) -> List[str]:
    """
    Converts a boolean value to a list of corresponding strings.

    :param bool_input: The boolean value to be converted.
    :return: A list of strings representing the boolean value. The list will contain one or more of the following strings:
        - "yes"
        - "y"
        - "true" (if bool_input is True)
        - "no"
        - "n"
        - "false" (if bool_input is False)
    """
    lex = {
        True: ["yes", "y", "true"],
        False: ["no", "n", "false"],
    }

    return lex[bool_input]


def string_to_bool(string_input: str) -> bool or None:
    """
    Convert a string representation of boolean to a boolean value.

    :param string_input: The input string to be converted.
    :type string_input: str
    :return: The corresponding boolean value or None if the input string is not recognized as boolean.
    :rtype: bool or None
    """
    lex = {
        "yes": True,
        "y": True,
        "true": True,
        "no": False,
        "n": False,
        "false": False,
    }

    return lex.get(string_input.lower(), None)


def get_script(script: str, scripts_dict: Dict[str, str], name: str) -> str or None:
    """
    Get the script based on the platform and provided parameters.

    :param script: The name of the script to retrieve.
    :param scripts_dict: A dictionary containing the scripts for different platforms.
    :param name: The name of the tool.
    :return: The script for the given platform and script name, or None if not found.
    :raises ValueError: If the tool does not have the specified script in any platform.
    """
    _os = platform.system().lower()
    windows = _os in ["windows", "win32"]
    macos = _os in ["darwin"]

    _script = None

    # Default to top-level definition of the script (not platform-dependent)
    if script in scripts_dict:
        _script = scripts_dict[script]

    # Any platform-dependent scripts will override the top-level definition
    if type(scripts_dict) is dict:
        if windows and "windows" in scripts_dict.keys():
            if script in scripts_dict["windows"]:
                _script = scripts_dict["windows"][script]
        elif macos and "mac" in scripts_dict.keys():
            if script in scripts_dict["mac"]:
                _script = scripts_dict["mac"][script]
        elif (not windows and not macos) and "linux" in scripts_dict.keys():
            if script in scripts_dict["linux"]:
                _script = scripts_dict["linux"][script]

    if _script is None:
        raise TypeError(
            f"Tool \"{name}\" does not have script '{script}' "
            f"in {list(scripts_dict.keys())}"
        )

    return _script


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
    the placeholder with the variable's value. If the variable is not set, it does not do any replacement and returns
    the string unchanged.

    Example usage:

    >>> replace_env("Hello ${USERNAME}, your home directory is ${HOME}")
    'Hello John, your home directory is /home/john'
    """
    pattern = re.compile(r"\$\{(.+?)}")
    matches = pattern.findall(string)

    for match in matches:
        env_value = os.getenv(match)
        if env_value is not None:
            string = string.replace(f"${{{match}}}", env_value)

    return string


def run_script_with_env_substitution(
    script_str: str, verbose: bool = False, monitor_output: MonitorOutput or None = None
) -> Tuple[str, int]:
    """
    Run a script with environment variable substitution. If the script fails to run as a shlex'd list, run it as a
    string instead.

    :param monitor_output: Options for running the script with monitored output
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
            if shutil.which(_script[0]) is None and verbose:
                print(
                    f"'{_script[0]}' is not installed. Trying script in shell.",
                    file=sys.stderr,
                )

            _os = platform.system().lower()
            windows = _os in ["windows", "win32"]

            if windows:
                windows_shell = (
                    "pwsh" if shutil.which("pwsh") is not None else "powershell"
                )
                cmd = [windows_shell, "-Command", substituted_script]

                if monitor_output is None:
                    result = subprocess.run(cmd)
                else:
                    result = monitored_subprocess(
                        command=cmd,
                        title=monitor_output.title,
                        subtitle=monitor_output.subtitle,
                        console=monitor_output.console,
                    )
            else:
                if monitor_output is None:
                    result = subprocess.run(
                        substituted_script, shell=True, text=True, capture_output=True
                    )
                else:
                    result = monitored_subprocess(
                        command=substituted_script,
                        title=monitor_output.title,
                        subtitle=monitor_output.subtitle,
                        console=monitor_output.console,
                        shell=True,
                    )
        # Else, run the shlex'd cmd list
        else:
            if monitor_output is None:
                result = subprocess.run(_script, text=True, capture_output=True)
            else:
                result = monitored_subprocess(
                    command=_script,
                    title=monitor_output.title,
                    subtitle=monitor_output.subtitle,
                    console=monitor_output.console,
                )
    except subprocess.CalledProcessError as e:
        return f"{e.stderr.strip()}", e.returncode

    if isinstance(result.stdout, TextIOWrapper):
        result.stdout = result.stdout.read()

    return str(result.stdout), result.returncode


# Code snippet used with permission @Hubro https://github.com/Textualize/rich/discussions/2885#discussioncomment-5382390
def monitored_subprocess(
    command: List[str] or str,
    title: str or None,
    subtitle: str or None,
    console: Console,
    shell: bool = False,
):
    """
    Run a subprocess while displaying the output in a temporary box with Rich
    """
    stdout_output = ""

    box_height = min(max([console.height // 4, 6]), 12)
    box_inner_height = box_height - 2  # The panel has 1 row of padding on each side
    box_width = console.width - 4  # The panel has 2 cols of padding on each side

    buffer = deque(maxlen=box_inner_height)

    def process_panel() -> Panel:
        return Panel(
            "\n".join(buffer), height=box_height, title=title, subtitle=subtitle
        )

    with rich.live.Live(
        get_renderable=process_panel, refresh_per_second=30, transient=True
    ):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="UTF-8",
            shell=shell,
        )

        assert process.stdout

        try:
            for line in process.stdout:
                buffer.append(line[:box_width].rstrip())
                stdout_output += line
        except KeyboardInterrupt:
            process.terminate()
            raise click.Abort()
        finally:
            # Always wait for the process to terminate, or we might fail later
            # cleanup steps
            process.wait()

        # create a CompletedProcess instance
        completed_process = subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout=stdout_output,
            stderr=process.stderr,
        )

    return completed_process
