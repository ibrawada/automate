import json
import sys
from typing import Any, Dict, List
import requests
import argparse
import subprocess
from pathlib import Path
from mate import output

COMMAND_NAME = "gitea" 
HOST = "host"
TOKEN = "token"

def _get_gitea_info(path: Path) -> dict | None:
    """
    Extracts Git info (branch, url, owner, repo) from a local repository.

    Args:
        path: The path to the local git repository.

    Returns:
        A dictionary with 'branch', 'url', 'owner', and 'repo',
        or None if it's not a git repository or info can't be found.
    """
    if not (path / ".git").is_dir():
        return None

    try:
        # Get current branch
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path, text=True, stderr=subprocess.DEVNULL
        ).strip()

        # Get remote origin URL
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=path, text=True, stderr=subprocess.DEVNULL
        ).strip()

        # Parse URL to get owner and repo
        path_part = url.split('@')[-1].replace(':', '/').replace('.git', '')
        parts = path_part.split('/')
        owner = parts[-2]
        repo = parts[-1]

        return {"branch": branch, "url": url, "owner": owner, "repo": repo}

    except (subprocess.CalledProcessError, IndexError):
        # This can happen if 'origin' remote doesn't exist or URL is malformed
        return None

def _construct_headers(token: str):
    # construct the header of the request
    headers = {
        'Authorization': f'Bearer {token}',
    }
    return headers



def _create_pull_request(cwd, gitea_url, gitea_PAT, title, target_branch, source_branch = None):
    # Gather git information on the currently processed folder
    gitea_info = _get_gitea_info(Path(cwd))

    if source_branch is None:
        source_branch = gitea_info["branch"]

    # construct the url of the request
    # https://docs.gitea.com/api/1.24/#tag/repository/operation/repoCreatePullRequest
    url = f'{gitea_url}/api/v1/repos/{gitea_info["owner"]}/{gitea_info["repo"]}/pulls'

    # construct the header of the request
    headers = _construct_headers(gitea_PAT)
    # construct the data of the request
    data = {
        'title': title,
        'head': source_branch,
        'base': target_branch
    }
    # call the api by providing the url, header, and data
    response = requests.post(url, headers=headers, json=data)
    # return the response of the api
    return response


def _merge_pull_request(cwd, gitea_url, gitea_PAT, delete_branch = False,  merge_method = "merge"):
    # Gather git information on the currently processed folder
    git_info = _get_gitea_info(Path(cwd))
    from_branch = git_info["branch"]


    # Get all pull requests for the repo
    # https://docs.gitea.com/api/1.24/#tag/repository/operation/repoListPullRequests
    prs_url = f'{gitea_url}/api/v1/repos/{git_info["owner"]}/{git_info["repo"]}/pulls'
    data = {'state': "open" }
    headers = _construct_headers(gitea_PAT)
    prs_response = requests.get(prs_url, headers=headers, json=data)
    prs = prs_response.json()
    
    # Right now it works by searching for a pull-request that comes from the currently checkout branch 
    pr_index = -1
    for pr in prs:
        if pr["head"]["ref"] == from_branch:
            pr_index = pr["number"]
            output.info(f'[gitea:merge-pr] Pull Request from {from_branch} to {pr["base"]["ref"]} has index: {pr_index} ')
            break
        
    
    if pr_index != -1:
        # construct the url of the 
        url = f'{gitea_url}/api/v1/repos/{git_info["owner"]}/{git_info["repo"]}/pulls/{pr_index}/merge'
        # construct the header of the request
        headers = _construct_headers(gitea_PAT)
        # construct the data of the request
        data = {
            'Do': merge_method,
            'delete_branch_after_merge': delete_branch,
        }
        # call the api by providing the url, header, and data
        # https://docs.gitea.com/api/1.24/#tag/repository/operation/repoPullRequestIsMerged
        response = requests.post(url, headers=headers, json=data)
        # return the response of the api
        return response
    else:
        output.warning("[gitea:merge-pr] No pull request found")
        return None



def main(cwd, args, env: dict) -> int:
    """
    Executes the gitea operation based on parsed arguments.
    """
    if HOST not in env or TOKEN not in env:
        output.error(f"'{HOST}' and '{TOKEN}' must be defined in the [{COMMAND_NAME}] section of your config.")
        return 1
    
    if args.action == "create-pr":
        response = _create_pull_request(
           cwd, env[HOST], env[TOKEN], args.title, args.target_branch, args.source_branch
        )
        return 0
    elif args.action == "merge-pr":
        response = _merge_pull_request(
            cwd, env[HOST], env[TOKEN], 
            args.delete_branch, args.merge_method 
        )
        return 0
    else:
        output.error(f"Unknown gitea action '{args.action}'")
        return 1
    


def get_default_config() -> dict[str, dict[str, str]]:
    return {
        COMMAND_NAME: 
        {
            HOST : "",
            TOKEN: ""
        }
    }




def build_parser(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Builds the argument parser for the gitea command.
    """
    subparsers = p.add_subparsers(dest="action", required=True, help="Gitea action")

    # --- Subparser for 'create-pr' ---
    pr_parser = subparsers.add_parser("create-pr", help="Create a pull request")
    pr_parser.add_argument("--target-branch", required=True, help="Target branch for the PR")
    pr_parser.add_argument("--source-branch", required=False, help="Source branch for the PR\nIf none provided then the current branch is taken as source")
    pr_parser.add_argument("--title", required=True,default="Just another PR", help="Title of the pull request")

    # --- Subparser for 'merge-pr' ---
    merge_parser = subparsers.add_parser("merge-pr", help="Merge a pull request")
    merge_parser.add_argument("--merge-method", default="merge",
                              choices=['merge', 'rebase', 'rebase-merge', 'squash', 'manually-merged'],
                              help="Merge method")
    merge_parser.add_argument("--delete-branch", action="store_true", help="Delete source branch after merge")

    return p



if __name__ == "__main__":
    parser = build_parser(
        argparse.ArgumentParser(prog=f"Nothing to say")
    )
    parsed_args = parser.parse_args(args=sys.argv[1:])