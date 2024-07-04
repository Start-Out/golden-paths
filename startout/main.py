import os
import sys

import typer

import startout.github_api as gh_r  # temp name

# Initialize the typer CLI
startout_paths_app = typer.Typer(name="startout-paths")

# Pull Env Variables (Not sure if this is the approach we are wanting)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)
TEMPLATE_OWNER = os.getenv("TEMPLATE_OWNER", None)
PATH_TEMPLATE_NAME = os.getenv("PATH_TEMPLATE_NAME", None)
NEW_PATH_OWNER = os.getenv(
    "NEW_PATH_OWNER", None
)  # TODO: Tightly couple to $GITHUB_TOKEN
NEW_PATH_NAME = os.getenv("NEW_PATH_NAME", None)


def initialize_path():
    initialized_path = initialize_repo()

    if not initialized_path:
        print("Failed to initialize new Path, exiting now.", file=sys.stderr)
    else:
        pass
        # initialize_postgresql()
        # initialize_express()
        # initialize_react()


def initialize_repo():
    print("Fetching and cloning Path template...")

    # If any environment variables are missing, prompt the user for them interactively
    _new_path_owner = NEW_PATH_OWNER
    _new_path_name = NEW_PATH_NAME
    _template_owner = TEMPLATE_OWNER
    _template_name = PATH_TEMPLATE_NAME

    # TODO Use some localization scheme for all feedback
    if _new_path_owner is None:
        _new_path_owner = input(
            "Who should be the owner of the new repository?\n"
            "(Must be a user/org authorized with `gh `auth`): "
        )
    if _new_path_name is None:
        _new_path_name = input(
            "What should the name of the new repository be?\n"
            "(Make sure the name isn't already taken): "
        )
    if _template_owner is None:
        _template_owner = input("\nWho is the owner of the Path template?: ")

    if _template_name is None:
        _template_name = input("\nWhat is the name of the Path template?: ")

    result = gh_r.create_repo_from_temp(
        _new_path_owner, _new_path_name, f"{_template_owner}/{_template_name}"
    )
    # Update $NEW_PATH_ROOT

    if not result:
        print("Failed to clone Path template.", file=sys.stderr)
    else:
        print(f"Cloned new Path to {result}")
        os.environ["NEW_PATH_ROOT"] = result

    return result


def main(path: str):
    print("Welcome to GoldenPaths!")

    # Determine what path to create
    #  AND where, store the created path's root in an ENV variable $NEW_PATH_ROOT
    if path == "react-express-postgresql":
        # Determine how to create that path
        # - discover frameworks that need initializing
        # - init them in necessary order
        print(f"Initializing {path}")
        initialize_path()
    else:
        print("Path not found...")


if __name__ == "__main__":
    typer.run(main)
