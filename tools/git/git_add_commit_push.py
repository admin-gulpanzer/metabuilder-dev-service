"""
Git Add Commit Push Tool

A tool for git add, commit, and push operations on repositories in the dev folder.
"""

import os
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from agno.tools import tool


@tool(
    name="git_add_commit_push",
    description="Add files, commit changes, and push to GitHub for a repository in the dev folder",
    show_result=True,
    cache_results=False
)
def git_add_commit_push(
    repo_name: str,
    commit_message: str,
    files: str = ".",
    branch: Optional[str] = None,
    force_push: bool = False,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add files, commit changes, and push to GitHub for a repository in the dev folder.
    
    Args:
        repo_name: Name of the repository in the dev folder
        commit_message: Commit message for the changes
        files: Files to add (default: "." for all changes)
        branch: Branch to push to (optional, uses current branch if not provided)
        force_push: Whether to force push (default: False)
        author_name: Author name for commit (optional)
        author_email: Author email for commit (optional)
        
    Returns:
        Dict containing operation status and details
    """
    try:
        # Get dev folder path
        dev_folder = Path(__file__).parent.parent.parent / "dev"
        repo_path = dev_folder / repo_name
        
        # Validate repository path
        if not repo_path.exists():
            return {"success": False, "error": f"Repository {repo_name} not found in dev folder"}
        
        if not (repo_path / ".git").exists():
            return {"success": False, "error": f"Not a Git repository: {repo_path}"}
        
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
                return {"success": False, "error": f"Failed to get current branch: {branch_result.stderr}"}
        
        # Step 1: Git Add
        logger.info(f"Adding files in repository: {repo_path}")
        add_cmd = ["git", "add", files]
        add_result = subprocess.run(
            add_cmd,
            capture_output=True,
            text=True,
            cwd=str(repo_path)
        )
        
        if add_result.returncode != 0:
            return {
                "success": False,
                "error": f"Git add failed: {add_result.stderr}",
                "step": "add"
            }
        
        # Step 2: Git Commit
        logger.info(f"Committing changes in repository: {repo_path}")
        
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
            logger.info("Git user not configured, setting default values")
            import os
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
            return {
                "success": False,
                "error": f"Git commit failed: {commit_result.stderr}",
                "step": "commit"
            }
        
        # Get commit hash
        commit_hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_path)
        )
        
        commit_hash = commit_hash_result.stdout.strip() if commit_hash_result.returncode == 0 else "unknown"
        
        # Step 3: Git Push
        logger.info(f"Pushing to repository: {repo_path}")
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
            return {
                "success": False,
                "error": f"Git push failed: {push_result.stderr}",
                "step": "push",
                "commit_hash": commit_hash
            }
        
        return {
            "success": True,
            "repository_name": repo_name,
            "repository_path": str(repo_path),
            "branch": branch,
            "commit_message": commit_message,
            "commit_hash": commit_hash,
            "files_added": files,
            "force_push": force_push,
            "message": f"Successfully added, committed, and pushed changes to {repo_name}"
        }
        
    except Exception as e:
        logger.error(f"Git operations error: {e}")
        return {"success": False, "error": f"Git operations error: {str(e)}"} 