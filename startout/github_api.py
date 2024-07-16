import os.path
import shlex
import subprocess
import sys
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn

custom_theme = Theme({
    "input_prompt": "bold cyan",
    "announcement": "bold yellow",
    "success": "bold green",
    "error": "bold red",
    "bold": "bold",
})

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

    # Example use of shlex (shell lexer) which will help us parse Starterfile
    cmd_string = f"gh repo create {owner}/{repo_name} --template={template} --clone"
    cmd = shlex.split(cmd_string)

    if public:
        cmd.append("--public")
    else:
        cmd.append("--private")

    result = ''

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Fetching and cloning {template}", total=None)

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if result.returncode == 0:
            progress.update(task, description=f"Success: {template} has been cloned.", completed=True)
            console.print(f"{result.stdout.decode()}", style='success')
            return os.path.join(os.getcwd(), repo_name)
        else:
            progress.update(task, description=f"Failure: {template} has not been cloned.")
            console.file = sys.stderr #set console output to stderr
            console.print(f"ERROR: {result.stdout.decode()}", style='error')
            return False
