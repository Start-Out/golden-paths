import shlex
import subprocess
import sys
from typing import TextIO
import yaml

from schema import Schema, And, Or


class Module:
    module_schema = Schema(
        {
            "name": And(str, len),
            "source": Schema(
                {
                    Or("git", "curl", "script", "docker-image", "dockerfile", only_one=True): str
                }
            ),
            "scripts": And(dict, len)
        }
    )

    def __init__(self, name: str, source: str, scripts: dict[str, str]):
        if "init" not in scripts.keys():
            raise TypeError(f"No 'init' script defined for module \"{name}\". Failed to create Module.")

        self.name = name
        self.source = source
        self.scripts = scripts

    def run(self, script: str) -> tuple[str, int]:
        if script not in self.scripts:
            raise ValueError(f"Module \"{self.name}\" does not have script '{script}' in {list(self.scripts.keys())}")

        _script = shlex.split(self.scripts[script])

        result = subprocess.run(_script, shell=True, check=True, text=True, capture_output=True)

        return result.stdout, result.returncode

    def initialize(self):
        msg, code = self.run("init")
        print(msg)

        return code == 0

    def destroy(self):
        print(f"Oops! {self.name} doesn't know how to destroy itself!")


class GitModule(Module):
    def initialize(self):
        print(f"Going to clone a git repository: {self.source}")
        return True


class CurlModule(Module):
    def initialize(self):
        # print(f"Going to download and run this script: {self.source}")
        # return True
        print(f"Going to pretend like {self.name} failed to initialize!")
        return False


class Starter:
    starterfile_schema = Schema(
        {
            "tools": And(dict, len),
            "modules": And(dict, len)
        }
    )

    def __init__(self, modules: list[Module]):
        self.modules = modules

    def up(self, teardown_on_failure=True):
        if len(self.modules) == 0:
            print("Nothing to do.")
            return False

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
                    module.destroy()

            return False

        return True


def parse_starterfile(starterfile_stream: TextIO) -> Starter:
    loaded = yaml.safe_load(starterfile_stream)
    Starter.starterfile_schema.validate(loaded)

    modules = []

    for module_name in loaded["modules"]:
        _module = loaded["modules"][module_name]
        module = Module.module_schema.validate(_module)

        name = module["name"]
        mode = next(iter(module["source"]))
        source = module["source"][mode]

        if mode == "git":
            module = GitModule(name, source, module["scripts"])
        elif mode == "curl":
            module = CurlModule(name, source, module["scripts"])
        else:
            module = Module(name, source, module["scripts"])

        modules.append(module)

    return Starter(modules)


if __name__ == "__main__":
    # test = Module("test", "", {"init": "echo hello world"})
    # test.run("init")
    # test.run("test")
    #
    # experiment = Module("experiment", "", {"test": "echo goodbye world", "init": "sleep 1"})
    # experiment.run("init")
    # experiment.run("ex")

    s = None
    with open("../Starterfile.yaml", "r") as f:
        s = parse_starterfile(f)

    s.up()
