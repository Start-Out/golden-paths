import json
import os.path
import shlex
import subprocess
import sys
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn

custom_theme = Theme(
    {
        "input_prompt": "bold cyan",
        "announcement": "bold yellow",
        "success": "bold green",
        "error": "bold red",
        "bold": "bold",
    }
)

console = Console(theme=custom_theme)


def create_repo_from_temp(
    owner: str, repo_name: str, template: str, public: bool = False
):
    """
    Create a GitHub repo from a provided template.

    :param owner: The owner of the new repo to be created, must be a GitHub user/org for which the currently
    authenticated (`gh auth status`) has permission to create a repo.
    :param repo_name: The name of the new repo to be created.
    :param template: The owner and name of the template repo e.g. "StartOut/template-repo"
    :param public: The visibility for the repo to be created (defaults to private)
    """

    cmd_string = f"gh repo create {owner}/{repo_name} --template={template} --clone"
    cmd = shlex.split(cmd_string)

    if public:
        cmd.append("--public")
    else:
        cmd.append("--private")

    result = ""

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}")
    ) as progress:
        task = progress.add_task(f"Fetching and cloning {template}", total=None)

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if result.returncode == 0:
            progress.update(
                task,
                description=f"Success: {template} has been cloned.",
                completed=True,
            )
            progress.refresh()
            progress.stop()
            console.print(f"{result.stdout.decode()}", style="success")
            return os.path.join(os.getcwd(), repo_name)
        else:
            progress.update(
                task,
                description=f"Failure: {template} has not been cloned.",
                completed=True,
            )
            progress.refresh()
            progress.stop()
            console.file = sys.stderr  # Set console output to stderr
            console.print(f"ERROR: {result.stdout.decode()}", style="error")
            return False


def check_repo_custom_property(
    template_owner: str, template_name: str, custom_properties: dict
) -> bool:
    cmd_string = f"gh api /repos/{template_owner}/{template_name}/properties/values"
    cmd = shlex.split(cmd_string)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}")
    ) as progress:
        task = progress.add_task(f"Checking properties of {template_name}", total=None)

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if result.returncode == 0:
            # Try to get a dict from result
            response_str = result.stdout.decode()

            repo_properties = {}
            try:
                for _property in json.loads(response_str):
                    repo_properties[_property["property_name"]] = _property["value"]

            except ValueError:
                progress.update(
                    task,
                    description=f"Failure: Failed to check properties of {template_name} "
                    f"(response {response_str}).",
                    completed=True,
                )
                progress.refresh()
                progress.stop()
                return False

            progress.update(
                task,
                description=f"Success: Received custom properties of {template_name}.",
                completed=True,
            )
            progress.refresh()

            if custom_properties != repo_properties:
                progress.update(task, description=f"Expected: {custom_properties}")
                progress.update(task, description=f"Received: {repo_properties}")
                progress.update(
                    task,
                    description=f"Failure: Mismatch in properties of {template_name}.",
                    completed=True,
                )
                progress.refresh()
                progress.stop()
                return False

            progress.stop()
            console.print(
                f"Validated all custom properties for {template_name}", style="success"
            )
            return True
        else:
            progress.update(
                task,
                description=f"Failure: Could not check properties of {template_name}.",
                completed=True,
            )
            progress.refresh()
            progress.stop()
            console.file = sys.stderr  # Set console output to stderr
            console.print(f"ERROR: {result.stdout.decode()}", style="error")
            return False
