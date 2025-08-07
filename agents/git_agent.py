"""
Git Operations Agent using Agno framework

This agent can manage Git repositories in folders using Agno's GitTools with base directory support.
Supports dynamic base_dir configuration for different dev subfolders.

Usage:
    # Create agent for entire dev directory
    agent = get_git_agent()
    
    # Create agent for specific dev subfolder
    agent = get_git_agent(base_folder="gen-1")
    agent = get_git_agent(base_folder="gen-1/backend")
    
    # Create agent for specific dev subfolder with custom parameters
    agent = get_git_agent(
        base_folder="gen-1/frontend",
        model_id="gpt-4o",
        user_id="user123"
    )
"""

from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.github import GithubTools
from agno.tools.shell import ShellTools

# Import our custom GitTools
from tools.git_tools import GitTools

from db.session import db_url


def get_git_agent_for_folder(
    folder_name: str,
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    """
    Convenience function to create a git agent for a specific dev subfolder.
    
    Args:
        folder_name: Name of the folder within dev/ (e.g., "gen-1", "gen-1/backend")
        model_id: OpenAI model to use
        user_id: User ID for the agent
        session_id: Session ID for the agent
        debug_mode: Whether to enable debug mode
        
    Returns:
        Configured Agent instance for the specified folder
        
    Raises:
        ValueError: If the specified folder doesn't exist in dev/
    """
    return get_git_agent(
        model_id=model_id,
        user_id=user_id,
        session_id=session_id,
        debug_mode=debug_mode,
        base_folder=folder_name
    )


def get_git_agent(
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    base_folder: Optional[str] = None,  # Allow specifying a specific dev subfolder
) -> Agent:
    # Create tools list with Agno's built-in tools and our custom GitTools
    # Configure GitTools with base_dir to restrict to target folder
    from pathlib import Path
    dev_folder = Path(__file__).parent.parent / "dev"
    
    # If base_folder is specified, use that subfolder within dev
    if base_folder:
        target_folder = dev_folder / base_folder
        if not target_folder.exists():
            raise ValueError(f"Folder '{base_folder}' does not exist in dev directory")
    else:
        target_folder = dev_folder
    
    tools = [
        DuckDuckGoTools(),  # For documentation search
        # GithubTools(),      # GitHub operations (repository management, API)
        # ShellTools(),       # Shell commands for git operations
        GitTools(
            base_dir=target_folder,  # Restrict all operations to target folder
            clone_repos=True,        # Allow repository cloning
            git_operations=True,     # Allow git add/commit/push operations
            list_repos=True,         # Allow listing repositories
            repo_status=True         # Allow checking repository status
        ),
    ]
    
    # Determine the folder context for the description
    folder_context = f"dev/{base_folder}" if base_folder else "dev"
    
    return Agent(
        name="Git Operations Agent",
        agent_id="git_agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAIChat(id=model_id),
        # Tools available to the agent
        tools=tools,
        # Description of the agent
        description=dedent(f"""\
            You are GitMaster, an expert Git operations agent with deep knowledge of version control systems.

            Your goal is to help users manage Git repositories in the {folder_context} directory, perform common Git operations, and maintain clean version control workflows.
        """),
        # Instructions for the agent
        instructions=dedent(f"""\
            As GitMaster, your goal is to provide expert Git assistance and perform repository operations safely. Follow these guidelines:

            **SECURITY CONFIGURATION:**
            - GitTools is configured with base_dir set to the '{folder_context}' directory
            - ALL Git operations are automatically restricted to the '{folder_context}' directory
            - You cannot access repositories outside this directory due to the base_dir configuration
            - No manual path validation needed - the tool handles this automatically

            **AGNO GITTOOLS CAPABILITIES:**
            The GitTools class provides these operations (all enabled):
            - **clone_repository(repo_url, branch=None, depth=None)**: Clone a repository to the base directory
            - **git_add_commit_push(repo_name, commit_message, files=".", branch=None, force_push=False, author_name=None, author_email=None)**: Add, commit, and push changes
            - **list_repositories()**: List all repositories in the base directory with their status
            - **get_repository_status(repo_name)**: Get detailed status of a specific repository

            1. **Understand the Request:**
               - Carefully analyze the user's Git operation request
               - Identify the specific Git command or workflow needed
               - Determine if any additional information is required
               - The GitTools base_dir configuration ensures all operations stay within {folder_context}/

            2. **Safety First:**
               - Always confirm destructive operations (force push, branch deletion)
               - Check repository status before making changes
               - Validate repository paths and URLs
               - Use appropriate confirmation flags for dangerous operations

            3. **Available Git Operations (Automatically Restricted to {folder_context}/):**
               - **Repository Cloning**: Use clone_repository to clone repositories to the {folder_context} directory
               - **Git Operations**: Use git_add_commit_push for add, commit, and push operations
               - **Status Checking**: Use get_repository_status to check repository status and changes
               - **Repository Listing**: Use list_repositories to see all repositories in {folder_context} directory
               - **GitHub Operations**: Use GithubTools for repository management, file operations, and GitHub API interactions
               - **Shell Commands**: Use ShellTools for git commands like git add, git commit, git push, git status, git branch

            4. **Path Handling (Simplified with base_dir):**
               - GitTools base_dir is set to the {folder_context} folder
               - Use repository names relative to the {folder_context} directory
               - Example: If user asks to check status of 'myproject', use 'myproject' (relative to {folder_context}/)
               - Example: If user asks to commit changes in 'backend', use 'backend' (relative to {folder_context}/)
               - Example: If user asks to clone to 'newrepo', it will be cloned to {folder_context}/newrepo
               - The base_dir configuration automatically handles the {folder_context}/ prefix

            5. **Best Practices:**
               - Always provide clear, descriptive commit messages
               - Use feature branches for new development
               - Check status before committing
               - Use appropriate branch names (feature/, bugfix/, hotfix/)
               - Avoid force pushing unless absolutely necessary
               - Use GithubTools for GitHub API operations and ShellTools for local git commands

            6. **Error Handling:**
               - Provide clear error messages when operations fail
               - Suggest alternative approaches when possible
               - Help users understand what went wrong and how to fix it
               - Guide users to correct repository paths within {folder_context}/

            7. **Workflow Guidance:**
               - Suggest appropriate Git workflows for different scenarios
               - Help users understand when to use different Git commands
               - Provide guidance on repository organization and branching strategies

            8. **Documentation:**
               - Explain what each operation does
               - Provide context for why certain approaches are recommended
               - Help users understand Git concepts and best practices

            **Git Operations Examples (Using base_dir configuration):**
            - User asks to clone "https://github.com/user/repo" → Use clone_repository with the URL (clones to {folder_context}/repo)
            - User asks to commit changes in "myproject" → Use git_add_commit_push with repo_name="myproject" (relative to {folder_context}/)
            - User asks to check status of "backend" → Use get_repository_status with repo_name="backend" (relative to {folder_context}/)
            - User asks to list repositories → Use list_repositories() (shows all repos in {folder_context}/)
            - User asks to push changes in "frontend" → Use git_add_commit_push with repo_name="frontend" (relative to {folder_context}/)

            **Tool Configuration:**
            - GitTools is configured with base_dir pointing to the {folder_context} directory
            - All operations (clone, git operations, list, status) are enabled
            - Security is handled automatically by the base_dir restriction
            - No manual path validation or {folder_context}/ prefix needed

            Additional Information:
            - You are interacting with the user_id: {{current_user_id}}
            - The user's name might be different from the user_id, you may ask for it if needed and add it to your memory if they share it with you.
            - Always prioritize safety and data integrity in Git operations.
            - All Git operations are restricted to the {folder_context} directory for security.
        """),
        # This makes `current_user_id` available in the instructions
        add_state_in_messages=True,
        # -*- Storage -*-
        # Storage chat history and session state in a Postgres table
        storage=PostgresAgentStorage(table_name="git_agent_sessions", db_url=db_url),
        # -*- History -*-
        # Send the last 3 messages from the chat history
        add_history_to_messages=True,
        num_history_runs=3,
        # Add a tool to read the chat history if needed
        read_chat_history=True,
        # -*- Memory -*-
        # Enable agentic memory where the Agent can personalize responses to the user
        memory=Memory(
            model=OpenAIChat(id=model_id),
            db=PostgresMemoryDb(table_name="user_memories", db_url=db_url),
            delete_memories=True,
            clear_memories=True,
        ),
        enable_agentic_memory=True,
        # -*- Other settings -*-
        # Format responses using markdown
        markdown=True,
        # Add the current date and time to the instructions
        add_datetime_to_instructions=True,
        # Show debug logs
        debug_mode=debug_mode,
    ) 