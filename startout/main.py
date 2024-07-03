import typer
import os
import startout.github_api as gh_r #temp name

#Pull Env Varibles (Not sure if this is the approach we are wanting)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)
TEMPLATE_OWNER = os.getenv("TEMPLATE_OWNER", None)
EXPRESS_TEMPLATE_NAME = os.getenv("EXPRESS_TEMPLATE_NAME", None)
NEW_EXPRESS_OWNER = os.getenv("NEW_EXPRESS_OWNER", None)  # TODO: Tightly couple to $GITHUB_TOKEN
NEW_EXPRESS_NAME = os.getenv("NEW_EXPRESS_NAME", None)

def initialize_express():
    print("Initializing Express...")
    # TODO: Assert that proper env varibles are in place
    gh_r.create_repo_from_temp(GITHUB_TOKEN, TEMPLATE_OWNER, EXPRESS_TEMPLATE_NAME, NEW_EXPRESS_OWNER, NEW_EXPRESS_NAME)
    # Update $NEW_PATH_ROOT


def main(path: str):
    print("Welcome to GoldenPaths!")

    # Determine what path to create
    #  AND where, store the created path's root in an ENV variable $NEW_PATH_ROOT
    if path == "react-express-postgresql":
        # Determine how to create that path
        # - discover frameworks that need initializing
        # - init them in necessary order
        print(f"Initializing {path}")
        initialize_express()
    else:
        print("Path not found...")


if __name__ == "__main__":
    typer.run(main)
