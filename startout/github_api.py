import os.path
import shlex
import subprocess
import sys


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

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if result.returncode == 0:
        print(result.stdout.decode())
        return os.path.join(os.getcwd(), repo_name)
    else:
        print(result.stderr.decode(), file=sys.stderr)
        return False
