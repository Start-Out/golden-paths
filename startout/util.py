import os
import platform
import re
import shlex
import shutil
import subprocess
import sys


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
    lex = {True: 'y', False: 'n'}

    return lex[bool_input]


def bool_to_strings(bool_input: bool) -> list[str]:
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
        "yes": True, "y": True, "true": True,
        "no": False, "n": False, "false": False,
    }

    return lex.get(string_input.lower(), None)


def get_script(script: str, scripts_dict: dict[str, str], name: str) -> str or None:
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
        raise TypeError(f"Tool \"{name}\" does not have script '{script}' "
                        f"in {list(scripts_dict.keys())}")

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
    pattern = re.compile(r'\$\{(.+?)}')
    matches = pattern.findall(string)

    for match in matches:
        env_value = os.getenv(match)
        if env_value is not None:
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
    except subprocess.CalledProcessError as e:
        return f"{e.stderr.strip()}", e.returncode

    return str(result.stdout), result.returncode