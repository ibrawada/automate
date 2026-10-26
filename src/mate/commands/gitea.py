import json
import sys
from typing import Any, Dict, List
import requests
import argparse
import subprocess
from pathlib import Path

from mate import globals
from mate import output
from mate.executors import ExecutionResult, ExecutorType

COMMAND_NAME = "gitea" 
HOST = "host"
TOKEN = "token"


def get_default_config() -> dict[str, Any]:
    return {
        COMMAND_NAME: 
        {
            HOST : "",
            TOKEN: ""
        }
    }



def get_git_info(path: Path) -> dict | None:
    """
    Extracts Git info (branch, url, owner, repo) from a local repository.

    Args:
        path: The path to the local git repository.

    Returns:
        A dictionary with 'branch', 'url', 'owner', and 'repo',
        or None if it's not a git repository or info can't be found.
    """
    if not (path / ".git").is_dir():
        # globals.exit_mate(globals.ERROR_CODE, "get_git_info: Path is not a valid git repo")
        return {}

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


def construct_headers(token: str):
    # construct the header of the request
    headers = {
        'Authorization': f'Bearer {token}',
    }
    return headers



def result(cwd, returncode: int, stdout: str = "", stderr: str = "") -> ExecutionResult:
    return ExecutionResult(command_name=COMMAND_NAME, command_args=[], cwd=Path(cwd), executor=ExecutorType.EMBEDDED,
                           returncode=returncode, stdout=stdout, stderr=stderr)



def create_pull_request(cwd: Path, gitea_url, gitea_PAT, title, target_branch, source_branch = None) -> ExecutionResult:
    # Gather git information on the currently processed folder
    dir_git_info = get_git_info(cwd)

    if dir_git_info == {}:
        return result(cwd, globals.ERROR_CODE, "", f"Provided path: {cwd} is not a valid git repo")

    if source_branch is None:
        source_branch = dir_git_info["branch"]

    # construct the url of the request
    # https://docs.gitea.com/api/1.24/#tag/repository/operation/repoCreatePullRequest
    url = f'{gitea_url}/api/v1/repos/{dir_git_info["owner"]}/{dir_git_info["repo"]}/pulls'

    # construct the header of the request
    headers = construct_headers(gitea_PAT)
    
    # construct the data of the request
    data = {
        'title': title,
        'head': source_branch,
        'base': target_branch
    }
    # call the api by providing the url, header, and data
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 201:
        return result(cwd, globals.ERROR_CODE,
                      stderr=f"[gitea:create-pr] No Pull-Request could be created from: {source_branch} to: {target_branch}\nReason: {response.reason}")

    return result(cwd, globals.SUCCESS_CODE)


def merge_pull_request(cwd: Path, gitea_url, gitea_PAT, from_branch: str | None,  delete_branch = False,  merge_method = "merge") -> ExecutionResult:
    # Gather git information on the currently processed folder
    dir_git_info = get_git_info(cwd)

    if dir_git_info == {}:
        return result(cwd, globals.ERROR_CODE, "", f"Provided path: {cwd} is not a valid git repo")
        
    if from_branch is None:
        from_branch = dir_git_info["branch"]


    # Get all pull requests for the repo
    # https://docs.gitea.com/api/1.24/#tag/repository/operation/repoListPullRequests
    prs_url = f'{gitea_url}/api/v1/repos/{dir_git_info["owner"]}/{dir_git_info["repo"]}/pulls'
    data = {'state': "open" }
    headers = construct_headers(gitea_PAT)
    prs_response = requests.get(prs_url, headers=headers, json=data)
    prs = prs_response.json()
    
    # Right now it works by searching for a pull-request that comes from the currently checkout branch 
    pr_index = -1
    for pr in prs:
        if pr["head"]["ref"] == from_branch:
            pr_index = pr["number"]
            #output.info(f'[gitea:merge-pr] Pull Request from {from_branch} to {pr["base"]["ref"]} has index: {pr_index} ')
            break
        
    
    if pr_index != -1:
        # construct the url of the 
        url = f'{gitea_url}/api/v1/repos/{dir_git_info["owner"]}/{dir_git_info["repo"]}/pulls/{pr_index}/merge'

        # construct the header of the request
        headers = construct_headers(gitea_PAT)

        # construct the data of the request
        data = {
            'Do': merge_method,
            'delete_branch_after_merge': delete_branch,
        }

        # call the api by providing the url, header, and data
        # https://docs.gitea.com/api/1.24/#tag/repository/operation/repoPullRequestIsMerged
        response = requests.post(url, headers=headers, json=data)

        # return the response of the api
        if response.status_code >= 300:
            return result(cwd, globals.ERROR_CODE,
                          stderr=f"[gitea:merge-pr] Pull-Request from: {from_branch} with index:{pr_index} cannot be merged. Reason: {response.reason}")
        # Else: success 
        return result(cwd, globals.SUCCESS_CODE)
    else:
        return result(cwd, globals.WARNING_CODE,
                      stderr=f"[gitea:merge-pr] No pull request found for provided from-branch: {from_branch}")



def main(cwd: Path, args, env: dict) -> ExecutionResult:
    """
    Executes the gitea operation based on parsed arguments.
    """
    # env is already the [gitea] section of the config
    host = env.get(HOST, "")
    token = env.get(TOKEN, "")

    # Both must be present and non-empty (the default config defines them as "")
    if not host or not token:
        return result(cwd, globals.ERROR_CODE,
                      stderr=f"'{HOST}' and '{TOKEN}' must be defined in the [{COMMAND_NAME}] section of your config.")

    if args.action == "create-pr":
        pr_status = create_pull_request(
           cwd, host, token, args.title, args.target_branch, args.source_branch
        )
        return pr_status
    elif args.action == "merge-pr":
        merge_status = merge_pull_request(
            cwd, host, token, args.from_branch,
            args.delete_branch, args.merge_method 
        )
        return merge_status
    else:
        # Todo: When encountering an error_code mate shall probabyl quit/abort execution.
        return result(cwd, globals.ERROR_CODE, stderr=f"Unknown gitea action '{args.action}'")
    



def build_parser(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Builds the argument parser for the gitea command.
    """
    subparsers = p.add_subparsers(dest="action", required=True, help="Gitea action")

    # --- Subparser for 'create-pr' ---
    pr_parser = subparsers.add_parser("create-pr", help="Create a pull request")
    pr_parser.add_argument("--target-branch", required=True, help="Target branch for the PR")
    pr_parser.add_argument("--source-branch", required=False, help="Source branch for the PR\nIf none provided then the current branch is taken as source")
    pr_parser.add_argument("--title", required=False,default="Just another PR", help="Title of the pull request")

    # --- Subparser for 'merge-pr' ---
    merge_parser = subparsers.add_parser("merge-pr", help="Merge a pull request")
    merge_parser.add_argument("--merge-method", default="merge",
                              choices=['merge', 'rebase', 'rebase-merge', 'squash', 'manually-merged'],
                              help="Merge method. Default=merge")
    merge_parser.add_argument("--from-branch", required=False, help="Source branch for the PR")
    merge_parser.add_argument("--delete-branch", action="store_true", help="Delete source branch after merge")

    return p



if __name__ == "__main__":
    parser = build_parser(
        argparse.ArgumentParser(prog=f"Nothing to say")
    )
    parsed_args = parser.parse_args(args=sys.argv[1:])