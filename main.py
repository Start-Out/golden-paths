import typer
import os
import githubRepoCreation as gh #temp name

#Pull Env Varibles (Not sure if this is the approach we are wanting)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
TEMPLATE_OWNER = os.getenv("TEMPLATE_OWNER")
EXPRESS_TEMPLATE_NAME = os.getenv("EXPRESS_TEMPLATE_NAME")
NEW_EXPRESS_OWNER = os.getenv("NEW_EXPRESS_OWNER")
NEW_EXPRESS_NAME = os.getenv("NEW_EXPRESS_NAME")



def initialize_express():
    print("Initializing Express...")
    #TODO: Assert that proper env varibles are in place
    gh.create_repo_from_temp(GITHUB_TOKEN, TEMPLATE_OWNER, EXPRESS_TEMPLATE_NAME, NEW_EXPRESS_OWNER, NEW_EXPRESS_NAME)


def main(path: str):
    print("Welcome to GoldenPaths!")

    #Determine what path to create
    if path == "react-express-postgresql":
        print(f"Initializing {path}")
        initialize_express()
    else:
        print("Path not found...")


if __name__ == "__main__":
    typer.run(main)