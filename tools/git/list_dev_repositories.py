"""
List Dev Repositories Tool

A tool for listing all repositories in the dev folder with their status.
"""

import subprocess
from typing import Dict, Any
from pathlib import Path
from loguru import logger

from agno.tools import tool


@tool(
    name="list_dev_repositories",
    description="List all repositories in the dev folder with their status",
    show_result=True,
    cache_results=False
)
def list_dev_repositories() -> Dict[str, Any]:
    """
    List all repositories in the dev folder with their status.
    
    Returns:
        Dict containing list of repositories and their status
    """
    try:
        # Get dev folder path
        dev_folder = Path(__file__).parent.parent.parent / "dev"
        
        if not dev_folder.exists():
            return {
                "success": True,
                "dev_folder": str(dev_folder),
                "repositories": [],
                "message": "Dev folder does not exist yet"
            }
        
        repositories = []
        
        # Iterate through dev folder contents
        for item in dev_folder.iterdir():
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
        
        return {
            "success": True,
            "dev_folder": str(dev_folder),
            "repositories": repositories,
            "total_repositories": len([r for r in repositories if r.get("is_git_repo", False)]),
            "total_items": len(repositories),
            "message": f"Found {len(repositories)} items in dev folder"
        }
        
    except Exception as e:
        logger.error(f"List dev repositories error: {e}")
        return {"success": False, "error": f"List dev repositories error: {str(e)}"} 