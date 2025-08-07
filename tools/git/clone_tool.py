"""
Repository Clone Tool

A simple tool to clone repositories to the dev folder using git commands.
"""

import os
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from agno.tools import tool


@tool(
    name="clone_repository",
    description="Clone a Git repository to the dev folder",
    show_result=True,
    cache_results=False
)
def clone_repository(
    repo_url: str,
    branch: Optional[str] = None,
    depth: Optional[int] = None
) -> Dict[str, Any]:
    """
    Clone a Git repository to the dev folder.
    
    Args:
        repo_url: The URL of the repository to clone
        branch: Specific branch to clone (optional)
        depth: Depth for shallow clone (optional)
        
    Returns:
        Dict containing clone status and directory path
    """
    try:
        # Validate repository URL
        if not repo_url or not repo_url.strip():
            return {"success": False, "error": "Repository URL is required"}
        
        # Get dev folder path
        dev_folder = Path(__file__).parent.parent.parent / "dev"
        dev_folder.mkdir(exist_ok=True)
        
        # Extract repository name from URL
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        clone_dir = dev_folder / repo_name
        
        # Check if repository already exists in dev folder
        if clone_dir.exists():
            return {"success": False, "error": f"Repository {repo_name} already exists in dev folder at {clone_dir}"}
        
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
        logger.info(f"Cloning repository: {repo_url} to {clone_dir}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "repository_url": repo_url,
                "local_path": str(clone_dir),
                "repository_name": repo_name,
                "branch": branch or "default",
                "message": f"Successfully cloned {repo_name} to dev folder at {clone_dir}"
            }
        else:
            return {
                "success": False,
                "error": f"Git clone failed: {result.stderr}",
                "return_code": result.returncode
            }
            
    except Exception as e:
        logger.error(f"Git clone error: {e}")
        return {"success": False, "error": f"Git clone error: {str(e)}"} 