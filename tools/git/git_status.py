"""
Git Status Tool

A tool for getting the status of repositories in the dev folder.
"""

import subprocess
from typing import Dict, Any
from pathlib import Path
from loguru import logger

from agno.tools import tool


@tool(
    name="git_status",
    description="Get the status of a repository in the dev folder",
    show_result=True,
    cache_results=False
)
def git_status(repo_name: str) -> Dict[str, Any]:
    """
    Get the status of a repository in the dev folder.
    
    Args:
        repo_name: Name of the repository in the dev folder
        
    Returns:
        Dict containing repository status
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
        
        # Get git status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(repo_path)
        )
        
        if status_result.returncode != 0:
            return {
                "success": False,
                "error": f"Git status failed: {status_result.stderr}"
            }
        
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
        
        return {
            "success": True,
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
        
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return {"success": False, "error": f"Git status error: {str(e)}"} 