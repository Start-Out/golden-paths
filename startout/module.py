import os
import platform
import shutil
import subprocess
import sys
import tempfile

from schema import Schema, And, Or, Optional, Use

from startout.init_option import InitOption
from startout.util import replace_env, run_script_with_env_substitution


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
        result = subprocess.run(cmd, shell=True, check=True, text=True,
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
            if len(msg.strip()) > 0:
                print(f".... [{self.name}.source.script]: {msg.strip()}")
            print(f".... PROGRESS [{self.name}]: Running init script")
            msg, code = self.run("init", print_output=True)

            if code != 0:
                print(f".. FAILURE [{self.name}]: {msg}", file=sys.stderr)
                return False
            else:
                print(f".. SUCCESS [{self.name}]: Initialized module {self.name}")
                return True

    def initialize_bash(self):
        """
        DEPRECATED

        Attempts to work on Windows

        :return:
        """
        _os = platform.system().lower()
        windows = _os in ["windows", "win32"]

        if windows and shutil.which("git-bash") is None:
            raise OSError(f"Windows detected and Git Bash is not installed. Please install Git Bash and try again.")

        with tempfile.TemporaryDirectory() as tmpdir:
            _tmp_filename = os.path.join(tmpdir, "script.sh")
            with open(_tmp_filename, "w") as f:
                f.write(self.source)

            _script = [
                "git-bash" if windows else "bash",
                _tmp_filename
            ]

            result = subprocess.run(_script, check=False, text=True, capture_output=True)
            print(f"Return code: {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            code = result.returncode
            response = result.stdout

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
