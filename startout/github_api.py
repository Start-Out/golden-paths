import requests
import os
import subprocess
import platform


def create_repo_from_temp(owner, repo_name, template):
    """
    Create a GitHub repo from a provided template.

    :param owner: The owner of the new repo.
    :param repo_name: The name of the new repo.
    :param template: The name of the template repo.
    """
    cmd = ['gh', 'repo', 'create', f'{owner}/{repo_name}', '--public?', '--clone', f'--template={template}']

    if platform.system() == 'Windows':
        cmd = ['cmd', '/c'] + cmd

        print("cmd: ", cmd)

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout)
        print(result.stderr)

    else:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout)
        print(result.stderr)
