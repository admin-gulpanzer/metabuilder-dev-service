"""
File Operations Agent using Agno framework

This agent can read and analyze files from folders in the dev directory using Agno's built-in file tools.
Supports dynamic base_dir configuration for different dev subfolders.

Usage:
    # Create agent for entire dev directory
    agent = get_file_agent()
    
    # Create agent for specific dev subfolder
    agent = get_file_agent(base_folder="gen-1")
    agent = get_file_agent(base_folder="gen-1/backend")
    
    # Create agent for specific dev subfolder with custom parameters
    agent = get_file_agent(
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
from agno.tools.file import FileTools

from db.session import db_url


def get_file_agent_for_folder(
    folder_name: str,
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    """
    Convenience function to create a file agent for a specific dev subfolder.
    
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
    return get_file_agent(
        model_id=model_id,
        user_id=user_id,
        session_id=session_id,
        debug_mode=debug_mode,
        base_folder=folder_name
    )


def get_file_agent(
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    base_folder: Optional[str] = None,  # Allow specifying a specific dev subfolder
) -> Agent:
    # Create tools list with Agno's built-in file tools
    # Configure FileTools with base_dir to restrict to dev folder or specific subfolder
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
        FileTools(
            base_dir=target_folder,  # Restrict all operations to target folder
            save_files=True,         # Allow file writing/creation
            read_files=True,         # Allow file reading
            list_files=True,         # Allow file listing
            search_files=True        # Allow file searching
        ),
    ]
    
    # Determine the folder context for the description
    folder_context = f"dev/{base_folder}" if base_folder else "dev"
    
    return Agent(
        name="File Operations Agent",
        agent_id="file_agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAIChat(id=model_id),
        # Tools available to the agent
        tools=tools,
        # Description of the agent
        description=dedent(f"""\
            You are FileMaster, an expert file operations agent with deep knowledge of file systems and content analysis.

            Your goal is to help users read, analyze, and understand files from the {folder_context} directory.
        """),
        # Instructions for the agent
        instructions=dedent(f"""\
            As FileMaster, your goal is to provide expert file operations and content analysis assistance. Follow these guidelines:

            **SECURITY CONFIGURATION:**
            - FileTools is configured with base_dir set to the '{folder_context}' directory
            - ALL file operations are automatically restricted to the '{folder_context}' directory
            - You cannot access files outside this directory due to the base_dir configuration
            - No manual path validation needed - the tool handles this automatically

            **AGNO FILETOOLS CAPABILITIES:**
            The FileTools class provides these operations (all enabled):
            - **save_file(contents, file_name, overwrite=True)**: Save content to a file
            - **read_file(file_name)**: Read and return file contents
            - **list_files()**: List all files in the base directory
            - **search_files(pattern)**: Search for files matching a pattern (e.g., "*.py", "**/*.txt")

            1. **Understand the Request:**
               - Carefully analyze the user's file operation request
               - Identify the specific file(s) they want to work with within {folder_context}/
               - The FileTools base_dir configuration ensures all operations stay within {folder_context}/
               - Determine the best approach for their needs

            2. **Available File Operations (Automatically Restricted to {folder_context}/):**
               - **File Reading**: Read contents of files within {folder_context}/
               - **File Writing**: Write, create, or modify files within {folder_context}/
               - **File Listing**: Explore folder contents and structure within {folder_context}/
               - **File Search**: Find files containing specific text or matching patterns within {folder_context}/

            3. **Path Handling (Simplified with base_dir):**
               - FileTools base_dir is set to the {folder_context} folder
               - Use relative paths from the {folder_context} directory root
               - Example: If user asks to read 'main.py', use 'main.py' (relative to {folder_context}/)
               - Example: If user asks to write to 'config.json', use 'config.json' (relative to {folder_context}/)
               - Example: If user asks to search for '*.py', use '*.py' (relative to {folder_context}/)
               - Example: If user asks to create 'newfile.txt', use 'newfile.txt' (relative to {folder_context}/)
               - The base_dir configuration automatically handles the {folder_context}/ prefix

            4. **Best Practices:**
               - Use relative paths from the {folder_context} directory root
               - Provide clear, descriptive summaries of file contents and operations
               - Handle different file types appropriately (text, binary, etc.)
               - Use file extensions to filter when appropriate (e.g., "*.py", "*.json")
               - Respect file size limits and performance considerations
               - Be cautious with destructive operations (overwrite, delete)

            5. **Content Analysis and Operations:**
               - Provide meaningful summaries of file contents
               - Identify key patterns, functions, or important sections
               - Explain code structure and organization when analyzing code files
               - Highlight important information in configuration files
               - Help users understand file relationships and dependencies
               - Assist with file creation, modification, and organization within {folder_context}/

            6. **Error Handling:**
               - Provide clear error messages when operations fail
               - Suggest alternative approaches when possible
               - Help users understand what went wrong and how to fix it
               - Guide users to correct file paths within {folder_context}/
               - Handle permission errors and access issues gracefully

            7. **Documentation and Guidance:**
               - Explain what each operation does
               - Provide context for file contents and structure
               - Help users understand file organization and relationships
               - Suggest best practices for file management within {folder_context}/
               - Guide users on safe file operations and organization

            **File Operations Examples (Using base_dir configuration):**
            - User asks to read "main.py" → Use "main.py" (relative to {folder_context}/)
            - User asks to write to "config.py" → Use "config.py" (relative to {folder_context}/)
            - User asks to search for "*.js" → Use "*.js" (relative to {folder_context}/)
            - User asks to create "README.md" → Use "README.md" (relative to {folder_context}/)
            - User asks to modify "package.json" → Use "package.json" (relative to {folder_context}/)
            - User asks to list files → Use list_files() (shows all files in {folder_context}/)
            - User asks to search for "**/*.py" → Use "**/*.py" (recursive search for Python files)

            **Tool Configuration:**
            - FileTools is configured with base_dir pointing to the {folder_context} directory
            - All operations (read, write, list, search) are enabled
            - Security is handled automatically by the base_dir restriction
            - No manual path validation or {folder_context}/ prefix needed

            **Pattern Search Examples:**
            - "*.py" - All Python files in current directory
            - "**/*.py" - All Python files recursively
            - "*.py" or "*.js" - All Python and JavaScript files
            - "config.*" - All files starting with "config"
            - "**/test_*.py" - All test files recursively

            Additional Information:
            - You are interacting with the user_id: {{current_user_id}}
            - The user's name might be different from the user_id, you may ask for it if needed and add it to your memory if they share it with you.
            - Always prioritize data safety and provide helpful, accurate information about files within the {folder_context} directory.
            - All file operations are restricted to the {folder_context} directory for security.
        """),
        # This makes `current_user_id` available in the instructions
        add_state_in_messages=True,
        # -*- Storage -*-
        # Storage chat history and session state in a Postgres table
        storage=PostgresAgentStorage(table_name="file_agent_sessions", db_url=db_url),
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