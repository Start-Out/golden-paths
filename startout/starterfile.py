import itertools
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import TextIO

import requests
import yaml
from dotenv import load_dotenv
from schema import Schema, And, Or, Optional, Use


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

    # Check if command can be found with shutil, run as a string otherwise
    _script = shlex.split(substituted_script)

    try:
        if shutil.which(_script[0]) is None:
            if verbose:
                print(f"'{_script[0]}' is not installed. Trying script in shell.", file=sys.stderr)
            result = subprocess.run(substituted_script, shell=True, check=True, text=True, capture_output=True)
        else:
            result = subprocess.run(_script, shell=True, check=True, text=True, capture_output=True)
    except OSError as e:
        return f"{e}", 1
    except subprocess.CalledProcessError as e:
        return f"{e.stdout}\n{e.stderr}", e.returncode

    return result.stdout, result.returncode


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


class InitOption:
    """
    Initializes an instance of the `InitOption` class. This class is used as an API for setting options before a Module
    is initialized (e.g. name of the project, passwords, etc.).

    This API is meant to be used by tools which interface with the Starterfile parser, e.g. the Startout CLI.

    :param options_set: A dictionary containing the options for initialization.
                        The dictionary should have the following keys:
                        - "default" (required): The default value for the option.
                        - "type" (optional): The type of the option value.
                        - "env_name" (required): The name of the environment variable associated with the option.
                        - "prompt" (required): The prompt to display when prompting for the option value.
    """

    def __init__(self, options_set):
        """
        Initializes the method.

        :param options_set: A dictionary containing the options for the method.
                    - "default" (required): The default value for the option.
                    - "type" (optional): The type of the option value.
                    - "env_name" (required): The name of the environment variable associated with the option.
                    - "prompt" (required): The prompt to display when prompting for the option value.
        """
        default = options_set["default"]

        if "type" in options_set.keys():
            _t = type_tool(options_set["type"])
            default = _t(default)

        self.name = replace_env(options_set["env_name"])
        self.default = replace_env(default) if type(default) is str else default
        self.prompt = replace_env(options_set["prompt"])
        self.value = None


class Module:
    """
    Class representing a module.

    Module.source defines how the module is collected, defined as:

    - git
      : A URI is passed to `git clone`

    - script
      : A script is executed by `bash` (or `git-bash` on Windows)

    Attributes:
        name (str): The name of the module.
        dest (str): The destination of the module (usually used as the name of the directory into which the module is installed).
        source (dict): The source of the module, given as any ONE of [git, curl, script, docker].
        scripts (dict): Scripts associated with the module.
        dependencies (str or list[str]): Dependencies of the module. (Optional)
        init_options (list[dict]): Initialization options for the module. (Optional)

    """
    module_schema = Schema(
        {
            "dest": And(str, Use(replace_env)),
            "source": Schema(
                {
                    Or("git", "script", only_one=True): str
                }
            ),
            "scripts": And(dict, len),
            Optional("depends_on"): Or(str, list[str]),
            Optional("init_options"): list[Schema(
                {
                    "env_name": And(str, len),
                    "type": And(str, len),
                    "default": And(str, len),
                    "prompt": And(str, len),
                }
            )]
        }
    )

    def __init__(self, name: str, dest: str, source: str, scripts: dict[str, str], dependencies=None,
                 init_options=None):
        """
        Initialize a new Module instance.

        :param name: The name of the module.
        :param dest: The destination path of the module.
        :param source: The source path of the module.
        :param scripts: A dictionary mapping script names to script paths.
        :param dependencies: (optional) A list of module names that this module depends on. Defaults to None.
        :param init_options: (optional) Additional options for module initialization. Defaults to None.
        """
        if "init" not in scripts.keys():
            raise TypeError(f"No 'init' script defined for module \"{name}\". Failed to create Module.")
        if "destroy" not in scripts.keys():
            raise TypeError(f"No 'destroy' script defined for module \"{name}\". Failed to create Module.")

        self.name = name
        self.dest = dest
        self.source = source
        self.scripts = scripts
        self.dependencies = dependencies
        self.init_options = init_options

    def run(self, script: str, print_output: bool = False) -> tuple[str, int]:
        """
        Runs a script with environment variable substitutions.

        :param script: The name of the script to be executed, located in the Module's scripts.
        :param print_output: Whether to print the response at the .... level
        :return: A tuple containing the stdout output and the return code of the script execution.
        """
        if script not in self.scripts:
            raise ValueError(f"Module \"{self.name}\" does not have script '{script}' in {list(self.scripts.keys())}")

        response, code = run_script_with_env_substitution(self.scripts[script])

        if print_output and len(response.strip()) > 0:
            print(f".... [{self.name}.{script}]: {response.strip()}")

        return response, code

    def initialize(self):
        """
        Run the Tool's 'init' script.

        :return: True if the response code is 0, False otherwise.
        """
        msg, code = self.run("init", print_output=True)

        if code != 0:
            print(f".. FAILURE [{self.name}]: {msg}", file=sys.stderr)
            return False
        else:
            print(f".. SUCCESS [{self.name}]: Initialized module {self.name}")
            return True

    def destroy(self):
        """
        Run the Tool's 'destroy' script.

        :return: True if the response code is 0, False otherwise.
        """
        msg, code = self.run("destroy", print_output=True)

        if code != 0:
            print(f".. FAILURE [{self.name}]: {msg}", file=sys.stderr)
            return False
        else:
            print(f".. SUCCESS [{self.name}]: Destroyed module {self.name}")
            return True


class GitModule(Module):
    """
    Module for interacting with Git.

    :class:`GitModule` is a subclass of :class:`Module` and provides functionality
    for initializing a Git repository.

    Example:
        >>> git_module = GitModule()
        >>> git_module.source = "https://github.com/username/repo.git"
        >>> git_module.dest = "/path/to/destination"
        >>> git_module.initialize()

    Note:
        This module requires Git to be installed on the system.

    Attributes:
        source (str): The source URL of the Git repository.
        dest (str): The destination directory to clone the repository into.

    Raises:
        OSError: If Git is not installed on the system.

    """
    def initialize(self):
        """
        Initializes the object by cloning `self.source` (a repository) to `self.dest` (a directory).

        :return: bool - True if the cloning succeeds, False otherwise.
        :raises OSError: If Git is not installed.
        """
        if shutil.which("git") is None:
            raise OSError(f"Git is not installed. Please install Git and try again.")

        cmd = [
            "git",
            "clone",
            "--progress",
            self.source,
            self.dest
        ]
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)  # TODO hoist the feedback to the terminal, especially if it can be displayed by the CLI which enwraps it

        if result.returncode != 0:
            print(f".. FAILURE [{self.name}]: {result.stdout.strip()}", file=sys.stderr)
            return False
        else:
            print(f".... PROGRESS [{self.name}]: Cloned module {self.name}, running init script")
            msg, code = self.run("init", print_output=True)

            if code != 0:
                print(f".. FAILURE [{self.name}]: {msg}", file=sys.stderr)
                return False
            else:
                print(f".. SUCCESS [{self.name}]: Initialized module {self.name}")
                return True


class ScriptModule(Module):
    def initialize(self):
        _os = platform.system().lower()
        windows = _os in ["windows", "win32"]

        if windows and shutil.which("git-bash") is None:
            raise OSError(f"Windows detected and Git Bash is not installed. Please install Git Bash and try again.")

        _script = f"{'git-bash' if windows else 'bash'} -c \"{self.source}\""

        response, code = run_script_with_env_substitution(_script, verbose=True)

        if code != 0:
            print(f".. FAILURE [{self.name}]: {response}", file=sys.stderr)
            return False
        else:
            msg = response.strip()
            if len(msg) > 0:
                print(f".... [{self.name}.source.script]: {response.strip()}")
            print(f".. SUCCESS [{self.name}]: Ran script for module {self.name}")
            return True


def create_module(module: dict, name: str):
    """
    Create a module object based on the given parameters. The value of module.source determines the type of module.

    :param module: A dictionary representing the module information.
    :param name: The name of the module.
    :return: An instance of a module object.
    """
    mode = next(iter(module["source"]))
    source = module["source"][mode]
    dest = module["dest"]

    options = None
    if "init_options" in module.keys():
        options = []
        for options_set in module["init_options"]:
            options.append(InitOption(options_set))
    dependencies = None
    if "depends_on" in module.keys():
        _deps = module["depends_on"]
        if type(_deps) is str:
            dependencies = [_deps]
        else:
            dependencies = _deps

    # Instantiate the correct type of Module
    _T = Module
    if mode == "git":
        _T = GitModule
    elif mode == "script":
        _T = ScriptModule

    return _T(
        name=name,
        dest=dest,
        source=source,
        scripts=module["scripts"],
        init_options=options,
        dependencies=dependencies
    )


class Starter:
    """
    Starter class

    The Starter class is used to install modules and tools required for a project. It allows for easy management of
    module and tool dependencies.

    Attributes:
        starterfile_schema (Schema): Schema definition for the starter file.

    Methods:
        __init__(modules, tools, module_dependencies, tool_dependencies)
            Initializes a new instance of the Starter class.

            Parameters:
                modules (list[Module]): List of modules to be installed.
                tools (list[Tool]): List of tools to be installed.
                module_dependencies (list[list[str]]): List of module dependencies in layers.
                tool_dependencies (list[list[str]]): List of tool dependencies in layers.

        up(teardown_on_failure=True)
            Installs the modules and tools.

            Parameters:
                teardown_on_failure (bool, optional): Specifies whether to rollback successfully installed tools or
                 modules if any others fail.
                Defaults to True.

            Returns:
                bool: True if installation is successful, False otherwise.

        install_tools(teardown_on_failure=True)
            Installs the tools. Called by up().

            Parameters:
                teardown_on_failure (bool, optional): Specifies whether to rollback installations on failure.
                Defaults to True.

            Returns:
                bool: True if installation is successful, False otherwise.

        install_modules(teardown_on_failure=True)
            Installs the modules. Called by up().

            Parameters:
                teardown_on_failure (bool, optional): Specifies whether to rollback installations on failure.
                Defaults to True.

            Returns:
                bool: True if installation is successful, False otherwise.

        get_init_options()
            Placeholder method for getting the initialization options.

        set_init_options(options)
            Placeholder method for setting the initialization options.
    """
    starterfile_schema = Schema(
        {
            "tools": And(dict, len),
            "modules": And(dict, len),
            Optional('env_file'): And(Or(Use(list), None))
        }
    )

    def __init__(self, modules: list[Module], tools: list[Tool], module_dependencies: list[list[str]],
                 tool_dependencies: list[list[str]]):
        """
        Initializes the class instance with given modules, tools, module dependencies, and tool dependencies.

        :param modules: A list of Module objects representing the parsed modules.
        :param tools: A list of Tool objects representing the parsed tools.
        :param module_dependencies: A list of lists of strings representing the dependencies between modules.
            Each inner list depends on one or more of the modules in the previous inner list (the first list has no
            dependencies).
        :param tool_dependencies: A list of lists of strings representing the dependencies between tools.
            Each inner list depends on one or more of the modules in the previous inner list (the first list has no
            dependencies).
        """
        self.modules = modules
        self.tools = tools
        self.module_dependencies = module_dependencies
        self.tool_dependencies = tool_dependencies

    def up(self, teardown_on_failure=True, fail_early=True):
        """
        :param teardown_on_failure: A boolean flag to determine whether to perform teardown operations if any failure occurs during the method execution. Default value is `True`.
        :param fail_early: A boolean flag to determine whether to abort the process as soon as a tool or module fails to initialize. Default value is `False`.
        :return: A boolean value indicating whether the tools and modules installation was successful. Returns `True` if both tools and modules were installed successfully, otherwise returns `False`.
        """
        tools_installed = self.install_tools(teardown_on_failure, fail_early)
        modules_installed = self.install_modules(teardown_on_failure, fail_early)

        if not tools_installed:
            print("ERROR: Failed to install tools!", file=sys.stderr)
        if not modules_installed:
            print("ERROR: Failed to install modules!", file=sys.stderr)

        return tools_installed and modules_installed

    def install_tools(self, teardown_on_failure=True, fail_early=True):
        """
        Install tools layer by layer so that their dependencies are all met before being installed.

        :param teardown_on_failure: If True, rollback other tools if any tool installation fails.
        :type teardown_on_failure: bool
        :param fail_early: If True, function will return false as soon as a tool fails to initialize.
        :type fail_early: bool
        :return: True if all tools are installed successfully, False otherwise.
        :rtype: bool
        """

        # Early exit if there are no tools to install.
        if len(self.tools) == 0:
            print("Nothing to do.")
            return False

        print("Installing tools...")

        failed_tools = []
        successful_tools = []
        for layer in self.tool_dependencies:
            # Install tools layer by layer so that their dependencies are all met before being installed
            early_exit = False

            for tool in (tool for tool in self.tools if tool.name in layer):
                # Use the tool's check function to prevent attempts to install an existing tool
                if tool.check():
                    print(f".. Tool '{tool.name}' is already installed, skipping.")
                    continue

                # Initialize this tool, adding it to the list of failures if it cannot be initialized
                if not tool.initialize():
                    failed_tools.append(tool.name)
                    if fail_early:
                        early_exit = True
                else:
                    successful_tools.append(tool.name)

            if early_exit:
                break

        # Upon any failed tools, report which tools failed...
        if len(failed_tools) > 0:
            print("Failed tools:", failed_tools, file=sys.stderr)

            # ... and teardown if specified
            if teardown_on_failure:
                print("Rolling back successfully installed tools:", successful_tools, file=sys.stderr)

                destroyed_tools = []
                for tool in [tool for tool in self.tools if tool.name in successful_tools]:
                    if not tool.destroy():
                        # TODO handle failure to destroy better
                        print(f"FATAL: Failed to destroy tool \"{tool.name}\"", file=sys.stderr)
                        print(f".. Only destroyed these tools: {destroyed_tools}", file=sys.stderr)
                        sys.exit(1)
                    else:
                        destroyed_tools.append(tool.name)

            # If any tools failed
            return False

        # If all tools were successfully installed or were already installed
        return True

    def install_modules(self, teardown_on_failure=True, fail_early=True):
        """
        Install modules layer by layer so that their dependencies are all met before being installed.

        :param teardown_on_failure: If True, rollback other tools if any module installation fails.
        :type teardown_on_failure: bool
        :param fail_early: If True, function will return false as soon as a tool fails to initialize.
        :type fail_early: bool
        :return: True if all modules are installed successfully, False otherwise.
        :rtype: bool
        """

        # Early exit if there are no modules to install.
        if len(self.modules) == 0:
            print("Nothing to do.")
            return False

        print("Installing modules...")

        failed_modules = []
        successful_modules = []
        for layer in self.module_dependencies:
            # Install modules layer by layer so that their dependencies are all met before being installed
            early_exit = False

            for module in (module for module in self.modules if module.name in layer):
                # Initialize this module, adding it to the list of failures if it cannot be initialized
                if not module.initialize():
                    failed_modules.append(module.name)
                    if fail_early:
                        early_exit = True
                else:
                    successful_modules.append(module.name)

            if early_exit:
                break

        # Report any failed modules
        if len(failed_modules) > 0:
            print("Failed modules:", failed_modules, file=sys.stderr)

            # Destroy modules which were successfully installed if specified
            if teardown_on_failure:
                print("Rolling back successfully installed modules:",
                      successful_modules,
                      file=sys.stderr)

                destroyed_modules = []
                for module in [module for module in self.modules if module.name in successful_modules]:
                    if not module.destroy():
                        # TODO handle failure to destroy better
                        print(f"FATAL: Failed to destroy module \"{module.name}\"", file=sys.stderr)
                        print(f".. Only destroyed these modules: {destroyed_modules}", file=sys.stderr)
                        sys.exit(1)
                    else:
                        destroyed_modules.append(module.name)

            # If any modules failed to initialize
            return False

        # If all modules were successfully initialized
        return True

    def get_init_options(self):
        """
        Returns a list of tuples containing the name and init_options of modules
        that have a non-null value for init_options in the self.modules list.

        :return: A list of tuples where each tuple contains the name and init_options
                 of modules satisfying the condition.
        """
        return [(module.name, module.init_options) for module in self.modules if module.init_options is not None]

    def set_init_options(self, options):
        """
        Sets the init options of the Starter to be used before calling .up()

        :param options: A dictionary of module and option names along with their corresponding values.
                        Example: {("react", "MODULE_REACT_USE_TYPESCRIPT"): True,
                                  ("react", "MODULE_REACT_APP_NAME"): "example-react-app"}
        :return: None
        """
        for module_name, option_name in options:
            # Get the value from the options set
            value = options[(module_name, option_name)]

            # Update the environment
            os.environ[option_name] = str(value)

            # Update the internal variable of the option itself
            module = [module for module in self.modules if module.name == module_name][0]
            option = [option for option in module.init_options if option.name == option_name][0]
            option.value = value

        pass


def create_dependency_layers(items: list[Module or Tool]) -> list[list[str]]:
    """
    Generate dependency layers based on the given items such that each inner list's dependencies are all contained
    within the preceding inner list (the first inner list has no dependencies).

    :param items: a list of `Module` or `Tool` objects representing the items
    :type items: list[Module or Tool]
    :return: a list of lists, each containing item names grouped by their dependencies
    :rtype: list[list[str]]
    """
    # Handle dependencies
    dependency_layers = [[item.name for item in items if item.dependencies is None]]

    # Check for any unfulfilled dependencies,
    #  collect all items that are in any item's depends_on fields
    all_items_depended_upon = set(
        itertools.chain.from_iterable([item.dependencies for item in items if item.dependencies is not None]))

    # Check if any items that are depended upon are not present (e.g. 'a' requires 'z' but only 'a' and 'b' are defined)
    unmet_dependencies = all_items_depended_upon - set([item.name for item in items])

    if len(unmet_dependencies) > 0:
        print(f"ERROR: Dependency not met {unmet_dependencies}", file=sys.stderr)
        exit(1)

    # Modules with no dependencies are added to the first layer

    # Put remaining modules (those with dependencies) in a set
    dependent_items = False
    if len(dependency_layers) > 0:
        dependent_items = set([item for item in items if item.name not in dependency_layers[0]])

    # Add items to layers until none are left
    while dependent_items:
        scheduled_items = list(itertools.chain.from_iterable(dependency_layers))

        added_items = []
        for dependent_item in dependent_items:
            if all(needed in scheduled_items for needed in dependent_item.dependencies):
                added_items.append(dependent_item)

        if len(added_items) == 0:
            print(f"ERROR: Could not meet dependencies for {[item.name for item in dependent_items]}, "
                  f"may be a circular dependency.", file=sys.stderr)
            exit(1)

        for added_item in added_items:
            dependent_items.remove(added_item)

        dependency_layers.append([item.name for item in added_items])

    return dependency_layers


def parse_starterfile(starterfile_stream: TextIO) -> Starter:
    """
    Parse a Starterfile.yaml

    Checks the Starterfile, Modules, Tools, and their constituent dependencies against their respective schemas and
    creates a `Starter` complete with dependency ordering for tools and modules.

    :param starterfile_stream: The stream representing the starter file.
    :type starterfile_stream: TextIO
    :return: The parsed Starter object.
    :rtype: Starter
    """
    loaded = yaml.safe_load(starterfile_stream)
    Starter.starterfile_schema.validate(loaded)

    for env_file in loaded["env_file"]:
        _path = os.path.join(os.path.dirname(starterfile_stream.name), env_file)
        load_dotenv(str(_path))

    tools = []

    for tool_name in loaded["tools"]:
        _tool = loaded["tools"][tool_name]
        tool = Tool.tool_schema.validate(_tool)

        dependencies = tool["depends_on"] if "depends_on" in _tool else None

        if type(dependencies) is str:
            dependencies = [dependencies]

        tools.append(Tool(tool_name, dependencies, tool["scripts"]))

    tool_dependencies = create_dependency_layers(tools)

    print("SUCCESS! Parsed tools:", [tool.name for tool in tools])

    modules = []

    for module_name in loaded["modules"]:
        _module = loaded["modules"][module_name]
        module = Module.module_schema.validate(_module)

        modules.append(create_module(module, module_name))

    module_dependencies = create_dependency_layers(modules)

    print("SUCCESS! Parsed modules:", [module.name for module in modules])

    return Starter(
        modules=modules,
        tools=tools,
        module_dependencies=module_dependencies,
        tool_dependencies=tool_dependencies
    )


if __name__ == "__main__":
    with open("../Starterfile.yaml", "r") as f:
        s = parse_starterfile(f)

    # for opt in s.get_init_options():
    #     response = cli_prompt(opt)
    #     os.environ(opt.env_name) = response

    stuff = s.get_init_options()

    example = {
        ("react", "MODULE_REACT_USE_TYPESCRIPT"): True,
        ("react", "MODULE_REACT_APP_NAME"): "example-react-app"
    }

    s.set_init_options(example)
    s.up()
