"""
Git Tools using Agno framework

A toolkit for Git operations with base directory support, similar to FileTools.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Any, List, Optional, Dict

from agno.tools import Toolkit
from agno.utils.log import log_debug, log_error, log_info


class GitTools(Toolkit):
    def __init__(
        self,
        base_dir: Optional[Path] = None,
        clone_repos: bool = True,
        git_operations: bool = True,
        list_repos: bool = True,
        repo_status: bool = True,
        **kwargs,
    ):
        self.base_dir: Path = base_dir or Path.cwd()

        tools: List[Any] = []
        if clone_repos:
            tools.append(self.clone_repository)
        if git_operations:
            tools.append(self.git_add_commit_push)
        if list_repos:
            tools.append(self.list_repositories)
        if repo_status:
            tools.append(self.get_repository_status)

        super().__init__(name="git_tools", tools=tools, **kwargs)

    def clone_repository(
        self, 
        repo_url: str, 
        branch: Optional[str] = None, 
        depth: Optional[int] = None
    ) -> str:
        """Clone a Git repository to the base directory.

        :param repo_url: The URL of the repository to clone
        :param branch: Specific branch to clone (optional)
        :param depth: Depth for shallow clone (optional)
        :return: Success message or error message
        """
        try:
            # Validate repository URL
            if not repo_url or not repo_url.strip():
                return "Error: Repository URL is required"
            
            # Extract repository name from URL
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            clone_dir = self.base_dir / repo_name
            
            # Check if repository already exists
            if clone_dir.exists():
                return f"Error: Repository {repo_name} already exists at {clone_dir}"
            
            # Get GitHub token from environment
            github_token = os.getenv("GITHUB_ACCESS_TOKEN")
            
            # Build git clone command
            cmd = ["git", "clone"]
            
            if branch:
                cmd.extend(["-b", branch])
            
            if depth:
                cmd.extend(["--depth", str(depth)])
            
            # Use GitHub token for authentication if available
            if github_token and "github.com" in repo_url:
                if repo_url.startswith("https://github.com/"):
                    authenticated_url = repo_url.replace("https://github.com/", f"https://{github_token}@github.com/")
                else:
                    authenticated_url = repo_url
            else:
                authenticated_url = repo_url
            
            cmd.extend([authenticated_url, str(clone_dir)])
            
            # Execute git clone
            log_info(f"Cloning repository: {repo_url} to {clone_dir}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                return f"Successfully cloned {repo_name} to {clone_dir}"
            else:
                return f"Error: Git clone failed: {result.stderr}"
                
        except Exception as e:
            log_error(f"Git clone error: {e}")
            return f"Error: Git clone error: {str(e)}"

    def git_add_commit_push(
        self,
        repo_name: str,
        commit_message: str,
        files: str = ".",
        branch: Optional[str] = None,
        force_push: bool = False,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> str:
        """Add files, commit changes, and push to GitHub for a repository.

        :param repo_name: Name of the repository in the base directory
        :param commit_message: Commit message for the changes
        :param files: Files to add (default: "." for all changes)
        :param branch: Branch to push to (optional, uses current branch if not provided)
        :param force_push: Whether to force push (default: False)
        :param author_name: Author name for commit (optional)
        :param author_email: Author email for commit (optional)
        :return: Success message or error message
        """
        try:
            repo_path = self.base_dir / repo_name
            
            # Validate repository path
            if not repo_path.exists():
                return f"Error: Repository {repo_name} not found in {self.base_dir}"
            
            if not (repo_path / ".git").exists():
                return f"Error: Not a Git repository: {repo_path}"
            
            # Get current branch if not specified
            if not branch:
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_path)
                )
                if branch_result.returncode == 0:
                    branch = branch_result.stdout.strip()
                else:
                    return f"Error: Failed to get current branch: {branch_result.stderr}"
            
            # Step 1: Git Add
            log_info(f"Adding files in repository: {repo_path}")
            add_cmd = ["git", "add", files]
            add_result = subprocess.run(
                add_cmd,
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            if add_result.returncode != 0:
                return f"Error: Git add failed: {add_result.stderr}"
            
            # Step 2: Git Commit
            log_info(f"Committing changes in repository: {repo_path}")
            
            # Check if Git user is configured, if not set default values
            user_name_result = subprocess.run(
                ["git", "config", "--global", "user.name"],
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            user_email_result = subprocess.run(
                ["git", "config", "--global", "user.email"],
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            # If Git user is not configured, set default values
            if user_name_result.returncode != 0 or user_email_result.returncode != 0:
                log_info("Git user not configured, setting default values")
                git_user_name = os.getenv("GIT_USER_NAME", "admin-gulpanzer")
                git_user_email = os.getenv("GIT_USER_EMAIL", "admin@gulpanzer.xyz")
                
                subprocess.run(
                    ["git", "config", "--global", "user.name", git_user_name],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_path)
                )
                subprocess.run(
                    ["git", "config", "--global", "user.email", git_user_email],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_path)
                )
            
            commit_cmd = ["git", "commit", "-m", commit_message]
            
            # Set author if provided
            if author_name and author_email:
                commit_cmd.extend(["--author", f"{author_name} <{author_email}>"])
            
            commit_result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            if commit_result.returncode != 0:
                return f"Error: Git commit failed: {commit_result.stderr}"
            
            # Get commit hash
            commit_hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            commit_hash = commit_hash_result.stdout.strip() if commit_hash_result.returncode == 0 else "unknown"
            
            # Step 3: Git Push
            log_info(f"Pushing to repository: {repo_path}")
            push_cmd = ["git", "push"]
            
            if force_push:
                push_cmd.append("--force")
            
            push_cmd.extend(["origin", branch])
            
            push_result = subprocess.run(
                push_cmd,
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            if push_result.returncode != 0:
                return f"Error: Git push failed: {push_result.stderr}"
            
            return f"Successfully added, committed, and pushed changes to {repo_name} (commit: {commit_hash})"
            
        except Exception as e:
            log_error(f"Git operations error: {e}")
            return f"Error: Git operations error: {str(e)}"

    def list_repositories(self) -> str:
        """List all repositories in the base directory with their status.

        :return: JSON formatted list of repositories and their status, or error message
        """
        try:
            if not self.base_dir.exists():
                return json.dumps({
                    "base_directory": str(self.base_dir),
                    "repositories": [],
                    "message": "Base directory does not exist yet"
                }, indent=2)
            
            repositories = []
            
            # Iterate through base directory contents
            for item in self.base_dir.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    # This is a git repository
                    repo_info = {
                        "name": item.name,
                        "path": str(item),
                        "is_git_repo": True
                    }
                    
                    # Get repository status
                    try:
                        status_result = subprocess.run(
                            ["git", "status", "--porcelain"],
                            capture_output=True,
                            text=True,
                            cwd=str(item)
                        )
                        
                        if status_result.returncode == 0:
                            status_lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
                            repo_info["modified_files"] = len([line for line in status_lines if line.startswith('M')])
                            repo_info["untracked_files"] = len([line for line in status_lines if line.startswith('??')])
                            repo_info["staged_files"] = len([line for line in status_lines if line.startswith('A') or line.startswith('M')])
                            repo_info["is_clean"] = len(status_lines) == 0
                            repo_info["total_changes"] = len(status_lines)
                        else:
                            repo_info["status_error"] = status_result.stderr
                            
                    except Exception as e:
                        repo_info["status_error"] = str(e)
                    
                    # Get current branch
                    try:
                        branch_result = subprocess.run(
                            ["git", "branch", "--show-current"],
                            capture_output=True,
                            text=True,
                            cwd=str(item)
                        )
                        
                        if branch_result.returncode == 0:
                            repo_info["current_branch"] = branch_result.stdout.strip()
                        else:
                            repo_info["current_branch"] = "unknown"
                            
                    except Exception as e:
                        repo_info["current_branch"] = "unknown"
                    
                    # Get remote URL
                    try:
                        remote_result = subprocess.run(
                            ["git", "config", "--get", "remote.origin.url"],
                            capture_output=True,
                            text=True,
                            cwd=str(item)
                        )
                        
                        if remote_result.returncode == 0:
                            repo_info["remote_url"] = remote_result.stdout.strip()
                        else:
                            repo_info["remote_url"] = "unknown"
                            
                    except Exception as e:
                        repo_info["remote_url"] = "unknown"
                    
                    repositories.append(repo_info)
                elif item.is_dir():
                    # This is a directory but not a git repository
                    repositories.append({
                        "name": item.name,
                        "path": str(item),
                        "is_git_repo": False
                    })
            
            result = {
                "base_directory": str(self.base_dir),
                "repositories": repositories,
                "total_repositories": len([r for r in repositories if r.get("is_git_repo", False)]),
                "total_items": len(repositories),
                "message": f"Found {len(repositories)} items in {self.base_dir}"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log_error(f"List repositories error: {e}")
            return f"Error: List repositories error: {str(e)}"

    def get_repository_status(self, repo_name: str) -> str:
        """Get the status of a repository in the base directory.

        :param repo_name: Name of the repository in the base directory
        :return: JSON formatted repository status, or error message
        """
        try:
            repo_path = self.base_dir / repo_name
            
            # Validate repository path
            if not repo_path.exists():
                return f"Error: Repository {repo_name} not found in {self.base_dir}"
            
            if not (repo_path / ".git").exists():
                return f"Error: Not a Git repository: {repo_path}"
            
            # Get git status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            if status_result.returncode != 0:
                return f"Error: Git status failed: {status_result.stderr}"
            
            # Parse status output
            status_lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
            
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Get remote URL
            remote_result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                cwd=str(repo_path)
            )
            
            remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else "unknown"
            
            result = {
                "repository_name": repo_name,
                "repository_path": str(repo_path),
                "current_branch": current_branch,
                "remote_url": remote_url,
                "modified_files": len([line for line in status_lines if line.startswith('M')]),
                "untracked_files": len([line for line in status_lines if line.startswith('??')]),
                "staged_files": len([line for line in status_lines if line.startswith('A') or line.startswith('M')]),
                "status_summary": status_result.stdout.strip() or "Working directory clean",
                "total_changes": len(status_lines)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log_error(f"Git status error: {e}")
            return f"Error: Git status error: {str(e)}" 