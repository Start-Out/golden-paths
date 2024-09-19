import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme
from typing_extensions import Annotated

import startout.github_api as gh_api
from startout import util
from startout.env_manager import EnvironmentVariableManager
from startout.init_option import InitOption
from startout.starterfile import parse_starterfile, Starter
from startout.util import replace_env

custom_theme = Theme(
    {
        "input_prompt": "bold cyan",
        "announcement": "bold yellow",
        "success": "bold green",
        "warning": "bold orange1",
        "error": "bold red",
        "bold": "bold",
    }
)

console = Console(theme=custom_theme)
log_path = os.path.join(Path(__file__).parent, "logs", "startout.log")


def prompt_init_option(option: InitOption):
    # If the default type is boolean, then use yes/no parsing
    use_bool = isinstance(option.default, bool)

    if use_bool:
        default_reminder = f" \[default: {util.bool_to_yn(option.default)}]"
    else:
        default_reminder = f" \[default: {option.default}]"

    if use_bool:
        type_reminder = f"(y/n)"
    elif type(option.default) is int:
        type_reminder = f"(enter an integer)"
    elif type(option.default) is float:
        type_reminder = f"(enter a floating point number)"
    else:
        type_reminder = ""

    endl = "\n"
    potential_response = console.input(
        f"[input_prompt]{option.prompt}[/]"
        f"{' ' if len(type_reminder) == 0 else endl}"
        f"[italic cyan]{type_reminder}{default_reminder}: [/]"
    )

    _T = type(option.default)
    response = None
    while response is None:
        if len(potential_response) > 0:
            try:
                if use_bool:
                    response = util.string_to_bool(potential_response)
                else:
                    response = _T(potential_response)
            except ValueError:
                console.print(f"[error]Try again.[/]")
                potential_response = console.input("> ")
        else:
            response = option.default

    return response


# Initialize the typer CLI
startout_paths_app = typer.Typer(name="startout-paths")
startout_starterfile_app = typer.Typer(name="startout-starter")


# fmt: off
@startout_paths_app.command(
    name="init",
    help="Initialize a new Path instance from a template repository and perform all automatic set up steps defined in"
         "its Starterfile"
)
def initialize_path_instance(
        template: Annotated[str, typer.Argument(help="Path Template to use. This may be a fully-formed GitHub repo "
                                                     "(e.g. User/Repo) or part of name which will be completed "
                                                     "interactively")],
        new_repo_name: Annotated[str, typer.Argument(help="Name of new repo created from Path")],
        new_repo_owner: Annotated[Optional[str], typer.Argument(help="User or Organization that will own the new repo "
                                                                     "(leave blank to assign interactively)")] = "",
        public: Annotated[bool, typer.Option("--public/--private", help="Set visibility of the new repo")] = True,
):
    # fmt: on

    #########################
    # Parse the template repo
    #########################

    # Case: User has defined a fully-formed GitHub repo
    if re.match(r"^[^/]*/[^/]*$", template):
        template_owner, template_name = template.split("/", 1)
    # Case: User has defined a non-path, will use interactive mode to form template owner and name
    elif "/" not in template:

        # Interactive mode defaults to using StartOut's Path templates
        result = console.input(
            f"[input_prompt]Please provide the owner of the '{template}' "
            f"Path (case insensitive) \\[default: Start-Out]: [/]",
        )
        if len(result) == 0 or result.lower() == "start-out":

            # StartOut Path templates begin with a prefix 'path-', default behavior is to use this prefix.
            template_owner = "Start-Out"
            template_name = f"path-{template}"
        else:
            template_owner = result
            template_name = template

        console.print(f"INFO: Using template {template_owner}/{template_name}", style='announcement')

    else:
        console.print(
            f"[error]Invalid Path template '{template}', please specify one of the following:[/]\n"
            f"- A fully-formed GitHub repository name (e.g. Owner/Repository)\n"
            f"- A non-path to be defined interactively (e.g. express-react-postgresql)\n"
            f"  * [bold]NOTE[/]: Non-paths will trigger an interactive mode which provides helpful defaults"
        )
        sys.exit(1)

    #######################################
    # Check if defined repository is a Path
    #######################################

    is_path = gh_api.check_repo_custom_property(template_owner, template_name, {
        "Golden-Paths": "Path",
    })

    if not is_path:
        console.print("Warning: Specified template can't be confirmed as a path, some features may be unavailable.",
                      style='warning')

    #################################
    # Parse the owner of the new repo
    #################################

    # If the new owner was not specified when this function was called, the user wants to define it interactively.
    if len(new_repo_owner) == 0:
        new_repo_owner = new_repo_owner_interactive()

    initialized_repo_path = initialize_repo(
        template_owner, template_name, new_repo_owner, new_repo_name, public
    )

    if not initialized_repo_path:
        console.file = sys.stderr  # set console output to stderr
        console.print("Failed to initialize new Path, exiting now.", style='error')
        console.file = sys.stdout  # set console output back to stdout
        sys.exit(1)

    else:
        if not is_path:
            console.print("Not a path: Skipping Starterfile step.", style='warning')
        else:
            # Initialize frameworks using Starterfile
            os.chdir(initialized_repo_path)

            # Start capturing environment variables throughout the process of opening the Path
            env_manager = EnvironmentVariableManager()
            with open("Starterfile.yaml", "r") as starter_file:
                starter = parse_starterfile(starter_file)

            do_starter_init(starter, env_manager)


def do_starter_init(starter: Starter, env_manager: EnvironmentVariableManager):
    init_options = starter.get_init_options()

    responses = {}
    for module_name, options in init_options:
        for option in options:
            response = prompt_init_option(option)
            responses[(module_name, option.name)] = response

    starter.set_init_options(responses)
    starter.up(console, log_path)

    ###############
    # Dump env vars
    if starter.env_dump_file is not None and starter.env_dump_mode is not None:
        # After opening the Path, gather the env vars generated during the process
        console.print(
            f"[info]Collecting environment variables for dump file: {starter.env_dump_file}[/]"
        )
        env_manager.capture_final_env()
        nonsensitive, sensitive = env_manager.get_captured_vars()

        # Ask for approval of each individual entry in sensitive
        approved_sensitive = {}
        for sens_key, sens_val in sensitive.items():
            include_var = console.input(
                f"[input_prompt]Do you want to include the potentially sensitive variable '{sens_key}={sens_val}'? (y/N) [/]")
            if include_var.lower() == 'y':
                approved_sensitive[sens_key] = sens_val

        dump_vars = {**nonsensitive, **approved_sensitive}

        with open(starter.env_dump_file, starter.env_dump_mode) as dump_file:
            if starter.env_dump_mode == 'a':
                dump_file.write("\n")

            for key, val in dump_vars.items():
                dump_file.write(f"{key}={val}\n")

    ########################
    # Do env var replacement
    if starter.env_replacement_targets is not None:
        for target in starter.env_replacement_targets:
            with open(target, 'r') as target_file:
                lines = target_file.readlines()

            with open(target, 'w') as target_file:
                for line in lines:
                    target_file.write(replace_env(line))


def new_repo_owner_interactive() -> str:
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:

        # Collect valid options for the user using `gh auth status` and `gh org list`

        # Get the current username
        task1 = progress.add_task(f"Checking `gh auth status`", total=None)

        try:
            result = subprocess.run(['gh', 'auth', 'status'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except FileNotFoundError as e:
            progress.update(task1, description="Failure: gh auth could not be validated", completed=True)
            console.file = sys.stderr  # set console output to stderr
            console.print(f"Failed to run `gh auth status`, make sure `gh` is installed!\n\t{e}", style='error')
            sys.exit(1)

        valid_owners = []

        # Exit if gh auth fails, necessary for the rest of the process
        if result.returncode != 0:
            progress.update(task1, description="Failure: gh auth could not be validated", completed=True)
            console.file = sys.stderr  # set console output to stderr
            if result.stderr is not None:
                console.print(result.stderr.decode(), style='error')
            if result.stdout is not None:
                console.print(result.stdout.decode())
            console.print("Unable to authenticate with GitHub, please ensure you have completed `gh auth login`",
                          style='bold')
            sys.exit(1)

        progress.update(task1, description="Success: gh auth status validated", completed=True)

        # Parse username from gh auth status
        feedback = result.stdout.decode()
        username = re.findall(r"(?<=account )(.*)(?= \(keyring\))", feedback)

        if len(username) != 1:
            console.file = sys.stderr  # set console output to stderr
            console.print("Problem parsing username from `gh auth status`, output was:", style='error')
            console.print(feedback, style='error')
            sys.exit(1)

        # If username is parsed, add to possible owners
        valid_owners.append(username[0])

        # Get authorized orgs via gh org list
        task2 = progress.add_task(f"Checking `gh org list`", total=None)

        result = subprocess.run(['gh', 'org', 'list'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Do not exit, but warn the user that this check failed
        if result.returncode != 0:
            console.file = sys.stderr  # set console output to stderr
            console.print(result.stderr.decode(), style='error')
            console.print("Unable to collect valid orgs, please check `gh auth status`", style='error')
            progress.update(task2, description="Failure: Failed to collect orgs", completed=True)
            console.file = sys.stdout  # set console output back to stdout

        else:
            # Parse orgs from command
            feedback = result.stdout.decode()
            lines = feedback.splitlines()

            valid_owners.extend([org for org in lines if len(org) > 0])
            progress.update(task2, description="Success: gh orgs collected", completed=True)

    # All potential new owners are collected, prompt user to choose one
    console.print("Please choose from the following list for the new repo owner:", style='input_prompt')

    i = 0
    for owner in valid_owners:
        console.print(f"[{i}] - [cyan]{owner}[/]")
        i += 1

    choice = None
    flag = False
    while choice is None:
        if flag:
            # Print the invalid feedback every time after the first ask
            console.file = sys.stderr  # set console output to stderr
            console.print("Invalid choice", style='error')
            console.file = sys.stdout  # set console output back to stdout

        flag = True

        choice = console.input("> ")

        try:
            choice = int(choice)
        except ValueError:
            choice = None

        try:
            if choice >= 0:
                return valid_owners[choice]
            else:
                choice = None
        except (IndexError, TypeError):
            choice = None


def initialize_repo(
        template_owner: str or None, template_name: str or None, new_repo_owner: str or None,
        new_repo_name: str or None, public: bool = True
):
    # If any environment variables are missing, prompt the user for them interactively

    # TODO Use some localization scheme for all feedback
    if new_repo_owner is None:
        new_repo_owner = console.input(
            "[input_prompt]Who should be the owner of the new repository?[/]\n"
            "[italic cyan](Must be a user/org authorized with `gh `auth`): [/]"
        )
    if new_repo_name is None:
        new_repo_name = console.input(
            "[input_prompt]What should the name of the new repository be?[/]\n"
            "[italic cyan](Make sure the name isn't already taken): [/]"
        )
    if template_owner is None:
        template_owner = console.input("\n[input_prompt]Who is the owner of the Path template?: [/]")

    if template_name is None:
        template_name = console.input("\n[input_prompt]What is the name of the Path template?: [/]")

    result = gh_api.create_repo_from_temp(
        new_repo_owner, new_repo_name, f"{template_owner}/{template_name}", public
    )

    if not result:
        console.file = sys.stderr  # set console output to stderr
        console.print("Failed to clone Path template.", style='error')
        console.file = sys.stdout  # set console output back to stdout

    else:
        # Update path to the project root if successful
        console.print(f"Cloned new Path to [italic]{result}[/]", style='success')
        os.environ["NEW_PATH_ROOT"] = result

    return result


def startout_paths_command():
    typer.run(initialize_path_instance)


@startout_starterfile_app.command(
    name="up",
    help="Perform all automatic set up steps defined in a Starterfile"
)
def starterfile_up_only(
        starterfile_path: Annotated[Optional[str], typer.Argument(help="Startfile to use")] = "Starterfile.yaml"):
    # Ensure the starterfile path is a valid file
    if not Path(starterfile_path).is_file():
        print(f"No such file '{starterfile_path}'", file=sys.stderr)
        exit(1)

    starterfile_parent_dir = Path(starterfile_path).parent

    # Obtain the current working directory, and then join this path with the 'starterfile_path'
    cwd = os.getcwd()
    full_starterfile_path = os.path.join(cwd, starterfile_path)

    os.chdir(starterfile_parent_dir)

    # Start capturing environment variables throughout the process of opening the Path
    env_manager = EnvironmentVariableManager()
    with open(full_starterfile_path, "r") as starter_file:
        starter = parse_starterfile(starter_file)

    do_starter_init(starter, env_manager)
    os.chdir(cwd)


def startout_starter_app():
    startout_starterfile_app()


if __name__ == "__main__":
    startout_starterfile_app()
