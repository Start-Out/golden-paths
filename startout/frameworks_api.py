import os
import subprocess


def init_framework(init_script: str, multiline_init_script: list[str] = None):
    # Make sure you're in the right dir
    _path = os.environ.get("NEW_PATH_ROOT")  # TODO Validate path
    os.chdir(_path)

    if multiline_init_script is None:
        _output = subprocess.check_output(init_script)
    else:
        # Handle multiline scripts differently
        pass

    # Make sure _output succeeded, raise any necessary exceptions BUT make sure they're handled
