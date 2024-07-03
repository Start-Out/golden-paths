import typer

def main(path: str):
    print("Welcome to GoldenPaths!")

    #Determine what path to create
    if path == "react-express-postgresql":
        print(f"Initializing {path}")
    else:
        print("Path not found...")


if __name__ == "__main__":
    typer.run(main)