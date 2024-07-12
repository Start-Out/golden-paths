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


def replace_env(string: str) -> str:
    pattern = re.compile(r'\$\{(.+?)}')
    matches = pattern.findall(string)

    for match in matches:
        env_value = os.getenv(match)
        if env_value is None:
            raise ValueError(f'Environment variable {match} not set.')
        string = string.replace(f'${{{match}}}', env_value)

    return string


class Tool:
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
        if self.get_script("install", scripts, name=name) is None:
            raise TypeError(f"No 'install' script defined for module \"{name}\". Failed to create Module.")
        if self.get_script("uninstall", scripts, name=name) is None:
            raise TypeError(f"No 'uninstall' script defined for module \"{name}\". Failed to create Module.")

        self.name = name
        self.dependencies = dependencies
        self.scripts = scripts

    def get_script(self, script: str, scripts_list, name: str or None = None) -> str or None:
        if name is None:
            name = self.name

        _os = platform.system().lower()
        windows = _os in ["windows", "win32"]
        macos = _os in ["darwin"]

        _script = None

        # Default to top-level definition of the script (not platform-dependent)
        if script in scripts_list:
            _script = scripts_list[script]

        # Any platform-dependent scripts will override the top-level definition
        if windows and "windows" in scripts_list.keys():
            if script in scripts_list["windows"]:
                _script = scripts_list["windows"][script]
        elif macos and "mac" in scripts_list.keys():
            if script in scripts_list["mac"]:
                _script = scripts_list["mac"][script]
        elif (not windows and not macos) and "linux" in scripts_list.keys():
            if script in scripts_list["linux"]:
                _script = scripts_list["linux"][script]
        else:
            if _script is None:
                raise ValueError(f"Tool \"{name}\" does not have script '{script}' "
                                 f"in {list(scripts_list.keys())}")


        return _script

    def run(self, script: str) -> tuple[str, int]:

        _script = self.get_script(script, self.scripts)

        # Inject environment variables
        substituted_script = replace_env(_script)
        try:
            _script = shlex.split(substituted_script)

            if shutil.which(_script[0]) is None:
                raise OSError(f"'{_script[0]}' is not installed. Trying script in shell.")

            result = subprocess.run(_script, shell=True, check=True, text=True, capture_output=True)
        except OSError:
            result = subprocess.run(substituted_script, shell=True, check=True, text=True, capture_output=True)

        return result.stdout, result.returncode

    def check(self):
        response, code = self.run("check")

        return code == 0

    def initialize(self):
        msg, code = self.run("install")
        print(msg)

        return code == 0

    def destroy(self):
        msg, code = self.run("uninstall")
        print(msg)

        return code == 0


class Module:
    module_schema = Schema(
        {
            "name": And(str, Use(replace_env)),
            "dest": And(str, Use(replace_env)),
            "source": Schema(
                {
                    Or("git", "curl", "script", "docker", only_one=True): str
                }
            ),
            "scripts": And(dict, len)
        }
    )

    def __init__(self, name: str, dest: str, source: str, scripts: dict[str, str]):
        if "init" not in scripts.keys():
            raise TypeError(f"No 'init' script defined for module \"{name}\". Failed to create Module.")
        if "destroy" not in scripts.keys():
            raise TypeError(f"No 'destroy' script defined for module \"{name}\". Failed to create Module.")

        self.name = name
        self.dest = dest
        self.source = source
        self.scripts = scripts

    def run(self, script: str) -> tuple[str, int]:
        if script not in self.scripts:
            raise ValueError(f"Module \"{self.name}\" does not have script '{script}' in {list(self.scripts.keys())}")

        # Inject environment variables
        substituted_script = replace_env(self.scripts[script])
        try:
            _script = shlex.split(substituted_script)

            if shutil.which(_script[0]) is None:
                raise OSError(f"'{_script[0]}' is not installed. Trying script in shell.")

            result = subprocess.run(_script, shell=True, check=True, text=True, capture_output=True)
        except OSError:
            result = subprocess.run(substituted_script, shell=True, check=True, text=True, capture_output=True)

        return result.stdout, result.returncode

    def initialize(self):
        msg, code = self.run("init")
        print(msg)

        return code == 0

    def destroy(self):
        msg, code = self.run("destroy")
        print(msg)

        return code == 0


class GitModule(Module):
    def initialize(self):
        if shutil.which("git") is None:
            raise OSError(f"Git is not installed. Please install Git and try again.")

        cmd = [
            "git",
            "clone",
            "--progress",
            self.source,
            self.dest
        ]
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)

        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            return False
        else:
            return True


class CurlModule(Module):
    def initialize(self):
        _os = platform.system().lower()
        windows = _os in ["windows", "win32"]

        if windows and shutil.which("git-bash") is None:
            raise OSError(f"Windows detected and Git Bash is not installed. Please install Git Bash and try again.")

        with tempfile.TemporaryDirectory() as tmpdir:
            with requests.get(self.source) as request:
                _filename = os.path.join(tmpdir, "script.sh")
                if request.status_code == 200:
                    with open(_filename, "w") as module_script_file:
                        module_script_file.write(request.text)

                    os.chmod(_filename, 0o775)
                    shell = "git-bash" if windows else "bash"

                    try:
                        result = subprocess.run([shell, _filename], check=True, stdout=subprocess.PIPE, text=True)
                    except subprocess.CalledProcessError as error:
                        print(f"Error while running the script. Error: {error.output}")
                        print(result.stdout)
                else:
                    return False

            if result.returncode != 0:
                print(result.stdout, file=sys.stderr)
                return False
            else:
                return True


def create_module(module: dict, name: str):
    mode = next(iter(module["source"]))
    source = module["source"][mode]
    dest = module["dest"]

    if mode == "git":
        return GitModule(name, dest, source, module["scripts"])
    elif mode == "curl":
        return CurlModule(name, dest, source, module["scripts"])
    else:
        return Module(name, dest, source, module["scripts"])


class Starter:
    starterfile_schema = Schema(
        {
            "tools": And(dict, len),
            "modules": And(dict, len),
            Optional('env_file'): And(Or(Use(list), None))
        }
    )

    def __init__(self, modules: list[Module], tools: list[Tool]):
        self.modules = modules
        self.tools = tools

    def up(self, teardown_on_failure=True):
        self.install_tools(teardown_on_failure)
        self.install_modules(teardown_on_failure)

    def install_tools(self, teardown_on_failure=True):
        if len(self.tools) == 0:
            print("Nothing to do.")
            return False

        print("Installing tools...")

        failed_tools = []
        for tool in self.tools:
            if tool.check():
                print(f".. Tool '{tool.name}' is already installed, skipping.")
                continue

            result = tool.initialize()

            if result is False:
                failed_tools.append(tool.name)

        if len(failed_tools) > 0:
            print("Failed tools:", failed_tools, file=sys.stderr)

            if teardown_on_failure:
                succeeded_tools = [tool for tool in self.tools if tool.name not in failed_tools]
                print("Rolling back other tools:", [tool.name for tool in succeeded_tools], file=sys.stderr)

                for tool in succeeded_tools:
                    destroyed = tool.destroy()
                    if not destroyed:
                        # TODO handle failure to destroy better
                        print(f"FATAL: Failed to destroy tool \"{tool.name}\"", file=sys.stderr)

            return False

        return True

    def install_modules(self, teardown_on_failure=True):
        if len(self.modules) == 0:
            print("Nothing to do.")
            return False

        print("Installing modules...")

        failed_modules = []
        for module in self.modules:
            result = module.initialize()

            if result is False:
                failed_modules.append(module.name)

        if len(failed_modules) > 0:
            print("Failed modules:", failed_modules, file=sys.stderr)

            if teardown_on_failure:
                succeeded_modules = [module for module in self.modules if module.name not in failed_modules]
                print("Rolling back other modules:", [module.name for module in succeeded_modules], file=sys.stderr)

                for module in succeeded_modules:
                    destroyed = module.destroy()
                    if not destroyed:
                        # TODO handle failure to destroy better
                        print(f"FATAL: Failed to destroy module \"{module.name}\"", file=sys.stderr)

            return False

        return True

    def get_init_options(self):
        pass

    def set_init_options(self, options):
        pass


def parse_starterfile(starterfile_stream: TextIO) -> Starter:
    loaded = yaml.safe_load(starterfile_stream)
    Starter.starterfile_schema.validate(loaded)

    for env_file in loaded["env_file"]:
        _path = os.path.join(os.path.dirname(starterfile_stream.name), env_file)
        load_dotenv(str(_path))

    tools = []

    for tool_name in loaded["tools"]:
        _tool = loaded["tools"][tool_name]
        tool = Tool.tool_schema.validate(_tool)

        dependencies = tool["depends_on"] if "depends_on" in _tool else []

        if type(dependencies) is str:
            dependencies = [dependencies]

        tools.append(Tool(tool_name, dependencies, tool["scripts"]))

    print("SUCCESS! Parsed tools:", [tool.name for tool in tools])

    modules = []

    for module_name in loaded["modules"]:
        _module = loaded["modules"][module_name]
        module = Module.module_schema.validate(_module)

        name = module["name"]

        modules.append(create_module(module, name))

    print("SUCCESS! Parsed modules:", [module.name for module in modules])

    return Starter(modules, tools)


if __name__ == "__main__":
    with open("../Starterfile.yaml", "r") as f:
        s = parse_starterfile(f)

    # for opt in s.get_init_options():
    #     response = cli_prompt(opt)
    #     os.environ(opt.env_name) = response

    s.up()
