import shutil
import subprocess
import sys

from schema import Schema, And, Or, Optional, Use

from startout.init_option import InitOption
from startout.util import replace_env, run_script_with_env_substitution, get_script


def check_for_key(name: str, key: str, scripts: dict):
    all_platform_keys = [platforms for platforms in scripts.keys() if platforms in ["windows", "mac", "linux"]]

    # The key must be in the top level (not platform-specific) unless it is specified in EACH platform-specific set

    # If the key is not at the top level...
    if key not in scripts.keys():
        # ...and the three supported platforms are not also all specified...
        if len(all_platform_keys) != 3:
            # ...then it is impossible for the script to have been fully defined.
            raise TypeError(f"No '{key}' script defined for module \"{name}\". Failed to create Module.")
        else:
            # If all platforms have a set of scripts, make sure that this script is in each of them
            missing_platforms = []
            for _platform in all_platform_keys:
                if key not in scripts[_platform].keys():
                    missing_platforms.append(_platform)
            if len(missing_platforms) > 0:
                raise TypeError(
                    f"Script 'init' not fully defined for module \"{name}\" (missing {missing_platforms}). Failed to create Module.")


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
    module_scripts_schema = Schema(
        Or(
            {
                Optional(str): And(str),
                Optional("windows"): {
                    Optional(str): And(str)
                },
                Optional("mac"): {
                    Optional(str): And(str)
                },
                Optional("linux"): {
                    Optional(str): And(str)
                },
            },
        )
    )
    module_schema = Schema(
        {
            "dest": And(str, Use(replace_env)),
            "source": Schema(
                {
                    Or("git", "script", only_one=True): str
                }
            ),
            "scripts": module_scripts_schema,
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
        if get_script("init", scripts, name) is None:
            raise TypeError(f"No 'init' script defined for module \"{name}\". Failed to create Module.")
        if get_script("destroy", scripts, name) is None:
            raise TypeError(f"No 'destroy' script defined for module \"{name}\". Failed to create Module.")

        self.name = name
        self.dest = dest
        self.source = source
        self.scripts = scripts
        self.dependencies = dependencies
        self.init_options = init_options

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def run(self, script: str, print_output: bool = False) -> tuple[str, int]:
        """
        Runs a script with environment variable substitutions.

        :param script: The name of the script to be executed, located in the Module's scripts.
        :param print_output: Whether to print the response at the .... level
        :return: A tuple containing the stdout output and the return code of the script execution.
        """
        if script not in self.scripts:
            raise ValueError(f"Module \"{self.name}\" does not have script '{script}' in {list(self.scripts.keys())}")

        response, code = run_script_with_env_substitution(get_script(script, self.scripts, self.name))

        if print_output and type(response) is str and len(response.strip()) > 0:
            print(f".... [{self.name}.{script}]: {response.strip()}")

        return response, code

    def initialize(self):
        """
        Run the Module's 'init' script.

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
        Run the Module's 'destroy' script.

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
            # "--progress",
            self.source,
            self.dest
        ]
        result = subprocess.run(cmd, text=True,
                                capture_output=True)  # TODO hoist the feedback to the terminal, especially if it can be displayed by the CLI which enwraps it

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
        msg, code = run_script_with_env_substitution(self.source)

        if code != 0:
            print(f".. FAILURE [{self.name}]: {msg}", file=sys.stderr)
            return False
        else:
            print(f".... PROGRESS [{self.name}]: Ran script for module {self.name}")
            if type(msg) is str and len(msg.strip()) > 0:
                print(f".... [{self.name}.source.script]: {msg.strip()}")
            print(f".... PROGRESS [{self.name}]: Running init script")
            msg, code = self.run("init", print_output=True)

            if code != 0:
                print(f".. FAILURE [{self.name}]: {msg}", file=sys.stderr)
                return False
            else:
                print(f".. SUCCESS [{self.name}]: Initialized module {self.name}")
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
