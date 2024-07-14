import platform

from schema import Schema, And, Or, Optional

from startout.util import run_script_with_env_substitution


class Tool:
    """
    Class representing a tool with installation and uninstallation scripts.

    Attributes:
        tool_scripts_schema (Schema): Schema definition for tool scripts.
        tool_schema (Schema): Schema definition for the entire tool object.

    Methods:
        __init__(self, name: str, dependencies: list[str], scripts: dict[str, str or dict[str, str]]):
            Initialize a Tool instance with the provided name, dependencies, and scripts.
            Raises a TypeError if 'install' or 'uninstall' scripts are not defined.

        get_script(self, script: str, scripts_list, name: str or None = None) -> str or None:
            Get the script for the given name and platform. May be run basically static, used for instantiation.
            Returns the script string if found, else None.

        run(self, script: str) -> tuple[str, int]:
            Execute the specified script and return the output and return code.
            Returns a tuple of the stdout and return code.

        check(self) -> bool:
            Run the 'check' script and return True if the return code is 0, else False.

        initialize(self) -> bool:
            Run the 'install' script and print the output.
            Returns True if the return code is 0, else False.

        destroy(self) -> bool:
            Run the 'uninstall' script and print the output.
            Returns True if the return code is 0, else False.
    """
    tool_scripts_schema = Schema(
        Or(
            {
                Optional("install"): And(str),
                Optional("uninstall"): And(str),
                Optional("check"): And(str),
                Optional("windows"): {
                    Optional("install"): And(str),
                    Optional("uninstall"): And(str),
                    Optional("check"): And(str),
                },
                Optional("mac"): {
                    Optional("install"): And(str),
                    Optional("uninstall"): And(str),
                    Optional("check"): And(str),
                },
                Optional("linux"): {
                    Optional("install"): And(str),
                    Optional("uninstall"): And(str),
                    Optional("check"): And(str),
                },
            },
        )
    )
    tool_schema = Schema(
        {
            Optional("depends_on"): Or(str, list[str]),
            "scripts": tool_scripts_schema
        }
    )

    def __init__(self, name: str, dependencies: list[str], scripts: dict[str, str or dict[str, str]]):
        """
        Initializes a Tool with the given name, dependencies, and scripts.

        :param name: The name of the tool.
        :param dependencies: A list of dependencies required by the tool.
        :param scripts: A dictionary mapping script names to their respective commands or scripts.

        :raises TypeError: If the 'install' and 'uninstall' scripts are not defined for the module.
        """
        if self.get_script("install", scripts, name=name) is None:
            raise TypeError(f"No 'install' script defined for module \"{name}\". Failed to create Module.")
        if self.get_script("uninstall", scripts, name=name) is None:
            raise TypeError(f"No 'uninstall' script defined for module \"{name}\". Failed to create Module.")

        self.name = name
        self.dependencies = dependencies
        self.scripts = scripts

    def get_script(self, script: str, scripts_dict: dict[str, str] or None = None,
                   name: str or None = None) -> str or None:
        """
        Retrieve the script based on the provided script name.

        :param script: The name of the script to retrieve.
        :param scripts_dict: A dictionary containing the available scripts. If not provided, use the default scripts.
        :param name: The name of the tool. If not provided, use the default tool name.
        :return: The script content as a string, or None if the script does not exist.
        :raises ValueError: If the provided script name does not exist in the scripts_dict.
        """
        if name is None:
            name = self.name
        if scripts_dict is None:
            scripts_dict = self.scripts

        _os = platform.system().lower()
        windows = _os in ["windows", "win32"]
        macos = _os in ["darwin"]

        _script = None

        # Default to top-level definition of the script (not platform-dependent)
        if script in scripts_dict:
            _script = scripts_dict[script]

        # Any platform-dependent scripts will override the top-level definition
        if windows and "windows" in scripts_dict.keys():
            if script in scripts_dict["windows"]:
                _script = scripts_dict["windows"][script]
        elif macos and "mac" in scripts_dict.keys():
            if script in scripts_dict["mac"]:
                _script = scripts_dict["mac"][script]
        elif (not windows and not macos) and "linux" in scripts_dict.keys():
            if script in scripts_dict["linux"]:
                _script = scripts_dict["linux"][script]
        else:
            if _script is None:
                raise ValueError(f"Tool \"{name}\" does not have script '{script}' "
                                 f"in {list(scripts_dict.keys())}")

        return _script

    def run(self, script: str) -> tuple[str, int]:
        """
        Runs a script with environment variable substitutions.

        :param script: The name of the script to be executed, located in the Tool's scripts.
        :return: A tuple containing the stdout output and the return code of the script execution.
        """
        _script = self.get_script(script)

        return run_script_with_env_substitution(_script)

    def check(self):
        """
        Run the Tool's 'check' script.

        :return: True if the response code is 0, False otherwise.
        """
        response, code = self.run("check")

        return code == 0

    def initialize(self):
        """
        Run the Tool's 'install' script.

        :return: True if the response code is 0, False otherwise.
        """
        msg, code = self.run("install")
        print(msg)

        return code == 0

    def destroy(self):
        """
        Run the Tool's 'uninstall' script.

        :return: True if the response code is 0, False otherwise.
        """
        msg, code = self.run("uninstall")
        print(msg)

        return code == 0
