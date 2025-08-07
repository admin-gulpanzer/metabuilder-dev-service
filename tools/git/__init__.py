"""
Git management tools for Git operations

DEPRECATED: These individual tools are deprecated in favor of the new GitTools class.
Use tools.git_tools.GitTools instead for better base directory support and consistency.
"""

from .clone_tool import clone_repository
from .git_add_commit_push import git_add_commit_push
from .git_status import git_status
from .list_dev_repositories import list_dev_repositories

__all__ = [
    "clone_repository",
    "git_add_commit_push",
    "git_status",
    "list_dev_repositories",
]

# Simple deprecation warning
import warnings
warnings.warn(
    "The individual git tools are deprecated. Use tools.git_tools.GitTools instead.",
    DeprecationWarning,
    stacklevel=1
) 