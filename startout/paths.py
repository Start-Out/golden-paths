import os
import re
import subprocess
import sys
from typing import Optional

import typer
from typing_extensions import Annotated

import startout.github_api as gh_api

# Initialize the typer CLI
startout_paths_app = typer.Typer(name="startout-paths")


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
        new_repo_name:  Annotated[str, typer.Argument(help="Name of new repo created from Path")],
        new_repo_owner: Annotated[Optional[str], typer.Argument(help="User or Organization that will own the new repo "
                                                                     "(leave blank to assign interactively)")] = "",
        public:  Annotated[bool, typer.Option("--public/--private", help="Set visibility of the new repo")] = True,
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
        result = input(
            f"Please provide the owner of the '{template}' Path (case insensitive) [default: Start-Out]: "
        )
        if len(result) == 0 or result.lower() == "start-out":

            # StartOut Path templates begin with a prefix 'path.path-', default behavior is to use this prefix.
            template_owner = "Start-Out"
            template_name = f"path.path-{template}"
        else:
            template_owner = result
            template_name = template

        print(f"INFO: Using template {template_owner}/{template_name}")

    else:
        print(
            f"Invalid Path template '{template}', please specify one of the following:\n"
            f"- A fully-formed GitHub repository name (e.g. Owner/Repository)\n"
            f"- A non-path to be defined interactively (e.g. express-react-postgresql)\n"
            f"  * NOTE: Non-paths will trigger an interactive mode which provides helpful defaults"
        )
        sys.exit(1)

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
        print("Failed to initialize new Path, exiting now.", file=sys.stderr)
    else:
        pass
        # initialize frameworks using Starterfile


def new_repo_owner_interactive() -> str:
    # Collect valid options for the user using `gh auth status` and `gh org list`

    # Get the current username
    print("Checking `gh auth status`...")

    try:
        result = subprocess.run(['gh', 'auth', 'status'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError as e:
        print(f"Failed to run `gh auth status`, make sure `gh` is installed!\n\t{e}", file=sys.stderr)
        sys.exit(1)

    valid_owners = []

    # Exit if gh auth fails, necessary for the rest of the process
    if result.returncode != 0:
        if result.stderr is not None:
            print(result.stderr.decode(), file=sys.stderr)
        if result.stdout is not None:
            print(result.stdout.decode(), file=sys.stderr)
        print("Unable to authenticate with GitHub, please ensure you have completed `gh auth`", file=sys.stderr)
        sys.exit(1)

    # Parse username from gh auth status
    feedback = result.stdout.decode()
    username = re.findall(r"(?<=account )(.*)(?= \(keyring\))", feedback)

    if len(username) != 1:
        print("Problem parsing username from `gh auth status`, output was:", file=sys.stderr)
        print(feedback, file=sys.stderr)
        sys.exit(1)

    # If username is parsed, add to possible owners
    valid_owners.append(username[0])

    # Get authorized orgs via gh org list
    print("Checking `gh org list`...")
    result = subprocess.run(['gh', 'org', 'list'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Do not exit, but warn the user that this check failed
    if result.returncode != 0:
        print(result.stderr.decode(), file=sys.stderr)
        print("Unable to collect valid orgs, please check `gh auth status`", file=sys.stderr)
    else:
        # Parse orgs from command
        feedback = result.stdout.decode()
        lines = feedback.splitlines()

        valid_owners.extend(lines)

    # All potential new owners are collected, prompt user to choose one
    print("Please choose from the following list for the new repo owner:")

    i = 0
    for owner in valid_owners:
        print(f"[{i}] - {owner}")
        i += 1

    choice = None
    flag = False
    while choice is None:
        if flag:
            # Print the invalid feedback every time after the first ask
            print("Invalid choice", file=sys.stderr)
        flag = True

        choice = input("> ")

        try:
            choice = int(choice)
        except ValueError:
            choice = None

        try:
            if choice > 0:
                return valid_owners[choice]
            else:
                choice = None
        except (IndexError, TypeError):
            choice = None


def initialize_repo(
    template_owner: str, template_name: str, new_repo_owner: str, new_repo_name: str, public: bool = True
):
    print("Fetching and cloning Path template...")

    # If any environment variables are missing, prompt the user for them interactively

    # TODO Use some localization scheme for all feedback
    if new_repo_owner is None:
        new_repo_owner = input(
            "Who should be the owner of the new repository?\n"
            "(Must be a user/org authorized with `gh `auth`): "
        )
    if new_repo_name is None:
        new_repo_name = input(
            "What should the name of the new repository be?\n"
            "(Make sure the name isn't already taken): "
        )
    if template_owner is None:
        template_owner = input("\nWho is the owner of the Path template?: ")

    if template_name is None:
        template_name = input("\nWhat is the name of the Path template?: ")

    result = gh_api.create_repo_from_temp(
        new_repo_owner, new_repo_name, f"{template_owner}/{template_name}", public
    )

    if not result:
        print("Failed to clone Path template.", file=sys.stderr)
    else:
        # Update path to the project root if successful
        print(f"Cloned new Path to {result}")
        os.environ["NEW_PATH_ROOT"] = result

    return result


def startout_paths_command():
    typer.run(initialize_path_instance)


if __name__ == "__main__":
    startout_paths_app()
