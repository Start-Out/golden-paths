import shlex
import subprocess
from typing import TextIO
import yaml

from schema import Schema, And


class Starter:
    def __init__(self):
        self.modules = None


class Module:
    module_schema = Schema(
        [
            {
                "name": And(str, len),
                "source": And(str, len)
            }
        ]
    )

    def __init__(self, name: str, source: str, scripts: dict[str, str]):
        if "init" not in scripts.keys():
            raise TypeError(f"No 'init' script defined for module \"{name}\". Failed to create Module.")

        self.name = name
        self.source = source
        self.scripts = scripts

    def run(self, script: str) -> subprocess.CompletedProcess[bytes]:
        if script not in self.scripts:
            raise ValueError(f"Module \"{self.name}\" does not have script '{script}' in {list(self.scripts.keys())}")

        _script = shlex.split(self.scripts[script])

        result = subprocess.run(_script, shell=True)

        return result


def parse_starterfile(starterfile_stream: TextIO) -> Starter:
    loaded = yaml.safe_load(starterfile_stream)
    Module.module_schema.validate(starterfile_stream)
    return Starter()


if __name__ == "__main__":
    # test = Module("test", "", {"init": "echo hello world"})
    # test.run("init")
    # test.run("test")
    #
    # experiment = Module("experiment", "", {"test": "echo goodbye world", "init": "sleep 1"})
    # experiment.run("init")
    # experiment.run("ex")

    with open("../Starterfile.yaml", "r") as f:
        parse_starterfile(f)

