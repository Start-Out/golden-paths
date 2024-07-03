import requests

def create_repo_from_temp(token:str, template_owner:str, template_repo:str, new_owner:str, new_repo:str):
    """
        Create a Github repo from a provided template.

        Endpoint Docs: https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-a-repository-using-a-template

        Parameters:
        :param token: A Github auth token.
        :param template_owner: The owner of the template repo.
        :param template_repo: The name of the template repo.
        :param new_owner: The owner of the new repo.
        :param new_repo: The name of the new repo.

        Returns:

        Raises:

        """
    print("Creating repository...")

    # Create URL
    url = f"https://api.github.com/repos/{template_owner}/{template_repo}/generate"

    # Create payload
    payload = {
        "owner": new_owner,
        "name": new_repo,
        "description": "This repository was made from Python!",
        "private": False,
    }


    # Create headers
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }

    # Make api call
    response = requests.post(url, headers=headers, json=payload)

    #TODO: Adjust return for proper handling of errors

    # verify result of api call
    if response.status_code == 201:
        print("Repository created successfully!")
        # print(response.json())
    else:
        print(f"Failed to create repository: {response.status_code}")
        print(response.json())
