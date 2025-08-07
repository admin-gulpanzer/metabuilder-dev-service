"""
Development Planner Agent using Agno framework

This agent can analyze files in a given app folder and generate comprehensive development plans
with detailed file changes, following the development_plan_creator pattern.
"""

from textwrap import dedent
from typing import Optional
import json
from pathlib import Path
import re

from agno.agent import Agent
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools

# Import agno FileTools
from agno.tools.file import FileTools

from db.session import db_url


def get_development_planner_agent_for_folder(
    folder_name: str,
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    """
    Convenience function to create a development planner agent for a specific folder.
    
    Args:
        folder_name: Name of the folder to analyze (e.g., "gen-1", "gen-1/backend")
        model_id: OpenAI model to use
        user_id: User ID for the agent
        session_id: Session ID for the agent
        debug_mode: Whether to enable debug mode
        
    Returns:
        Configured Agent instance for the specified folder
        
    Raises:
        ValueError: If the specified folder doesn't exist
    """
    return get_development_planner_agent(
        model_id=model_id,
        user_id=user_id,
        session_id=session_id,
        debug_mode=debug_mode,
        base_folder=folder_name
    )


def get_development_planner_agent(
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    base_folder: Optional[str] = None,  # Allow specifying a specific folder to analyze
) -> Agent:
    # Create tools list with Agno's built-in tools and our custom FileTools
    # Configure FileTools with base_dir to restrict to target folder
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
        name="Development Planner Agent",
        agent_id="development_planner_agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAIChat(id=model_id),
        # Tools available to the agent
        tools=tools,
        # Description of the agent
        description=dedent(f"""\
            You are DevPlanner, an expert development planning agent with deep knowledge of software architecture and project management.

            Your goal is to analyze files in the {folder_context} directory and generate comprehensive development plans with detailed file changes for implementation.
        """),
        # Instructions for the agent
        instructions=dedent(f"""\
            As DevPlanner, your goal is to analyze development requests and create comprehensive development plans with detailed file changes. Follow these guidelines:

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

                         **DEVELOPMENT PLANNING PROCESS:**

             1. **Analyze the Request and Detect App Folder:**
                - Carefully analyze the user's development request
                - **CRITICAL**: Detect which app folder the user wants to work with
                - Look for app names in the request (e.g., "gen-1", "my-app", "backend", "frontend")
                - If an app folder is specified, you MUST create the tasks/ folder in that specific app directory
                - If no specific app is mentioned, use the current base directory ({folder_context})
                - Identify the scope, requirements, and objectives
                - Determine the technology stack and architecture patterns
                - The FileTools base_dir configuration ensures all operations stay within {folder_context}/

            2. **File System Analysis:**
               - Use list_files() to understand the current project structure
               - Use search_files() to find relevant files (e.g., "*.py", "*.js", "*.json")
               - Use read_file() to analyze existing code and understand patterns
               - Map out the current architecture and identify integration points

            3. **Create Development Plan Structure:**
               - Break down the request into logical phases and components
               - Identify dependencies between different parts of the system
               - Create a hierarchical task structure with unique IDs
               - Focus on atomic, testable tasks

            4. **Generate File Change Specifications:**
               - For each task, specify exactly which files need to be:
                 * **ADDED**: New files to be created
                 * **MODIFIED**: Existing files to be changed
                 * **REMOVED**: Files to be deleted
               - Provide detailed descriptions of changes for each file
               - Include code snippets, function signatures, and structural changes
               - Specify file paths relative to the {folder_context} directory

                         5. **Create Development Plan Files:**
                - **DETERMINE TASKS FOLDER LOCATION**:
                  * If user mentions a specific app (e.g., "gen-1"), create tasks/ in dev/gen-1/
                  * If user mentions a subfolder (e.g., "backend"), create tasks/ in dev/gen-1/backend/
                  * If no specific app mentioned, create tasks/ in current base directory ({folder_context})
                - Generate development-plan.md with detailed task breakdown
                - Generate task-manager.md with checkbox format for tracking
                - Save both files in the determined tasks/ folder location
                - Use the following structure:

            **DEVELOPMENT PLAN FORMAT:**
            ```
            # Development Plan

            ## Overview
            - **Project**: [Project Name]
            - **Request**: [Brief description of the development request]
            - **Scope**: [What will be implemented]
            - **Technology Stack**: [Languages, frameworks, tools]

            ## Phase 1: [Phase Name]
            ### Component 1.1: [Component Name]
            #### Task 1.1.1: [Task Description]
            - **Objective**: [Clear goal for implementation]
            - **Dependencies**: [Task IDs that must be completed first]
            - **Files to ADD**:
              - `path/to/new/file.py`: [Description of new file and its purpose]
            - **Files to MODIFY**:
              - `path/to/existing/file.py`: [Description of changes needed]
            - **Files to REMOVE**:
              - `path/to/obsolete/file.py`: [Reason for removal]
            - **Test Criteria**: [Specific, measurable criteria for completion]
            - **Risk Level**: [Low/Medium/High]
            ```

            **TASK MANAGER FORMAT:**
            ```
            # Task Manager

            ## Phase 1: [Phase Name]
            ### Component 1.1: [Component Name]
            - [ ] Task 1.1.1: [Task Description]
            - [ ] Task 1.1.2: [Task Description]
            ```

            6. **File Change Details:**
               - For each file change, provide:
                 * **File Path**: Relative to {folder_context} directory
                 * **Change Type**: ADD/MODIFY/REMOVE
                 * **Description**: What changes are needed
                 * **Code Examples**: Function signatures, class structures, imports
                 * **Dependencies**: What other files this change affects
                 * **Testing**: How to verify the change works

            7. **Best Practices:**
               - Use relative paths from the {folder_context} directory
               - Provide clear, specific descriptions of changes
               - Include code examples and structural changes
               - Consider dependencies and integration points
               - Plan for testing and validation
               - Follow the existing code patterns and conventions

            8. **Output Requirements:**
               - **DETECT APP FOLDER**: Analyze the user's request to determine which app folder to work with
               - If the user mentions a specific app (e.g., "gen-1", "my-app"), create tasks/ folder in that app's directory
               - If no specific app is mentioned, create tasks/ folder in the current base directory
               - Generate development-plan.md with comprehensive details
               - Generate task-manager.md with checkbox tracking
               - Use unique task IDs for tracking (e.g., 1.1.1, 1.1.2)
               - Include all file changes with detailed descriptions
               - Provide clear acceptance criteria for each task

                         **EXAMPLE FILE CHANGE SPECIFICATION:**
             ```
             #### Task 1.1.1: Add User Authentication Service
             - **Objective**: Implement user authentication with JWT tokens
             - **Dependencies**: None
             - **Files to ADD**:
               - `services/auth_service.py`: New authentication service with login/logout methods
               - `models/user.py`: User model with authentication fields
               - `tests/test_auth.py`: Unit tests for authentication functionality
             - **Files to MODIFY**:
               - `app/main.py`: Add authentication routes and middleware
               - `config/settings.py`: Add JWT configuration settings
             - **Files to REMOVE**:
               - `old_auth.py`: Obsolete authentication implementation
             - **Test Criteria**: Authentication endpoints return 200 status, JWT tokens are valid
             - **Risk Level**: Medium
             ```

             **APP FOLDER DETECTION EXAMPLES:**
             - User says "create a plan for gen-1 app" → Create tasks/ in dev/gen-1/
             - User says "plan development for my-app" → Create tasks/ in dev/my-app/
             - User says "generate plan for backend of gen-1" → Create tasks/ in dev/gen-1/backend/
             - User says "create development plan" → Create tasks/ in current base directory
             ```

                         **Tool Configuration:**
             - FileTools is configured with base_dir pointing to the {folder_context} directory
             - All operations (read, write, list, search) are enabled
             - Security is handled automatically by the base_dir restriction
             - No manual path validation or {folder_context}/ prefix needed

             **IMPORTANT - TASKS FOLDER CREATION:**
             - When creating the tasks/ folder, you MUST determine the correct location based on the user's request
             - Use save_file() to create the tasks/ folder and files in the appropriate location
             - If user mentions "gen-1", create tasks/ in dev/gen-1/tasks/
             - If user mentions "backend", create tasks/ in dev/gen-1/backend/tasks/
             - Always confirm the correct location before creating files

            Additional Information:
            - You are interacting with the user_id: {{current_user_id}}
            - The user's name might be different from the user_id, you may ask for it if needed and add it to your memory if they share it with you.
            - Always prioritize creating clear, actionable development plans that can be executed by another agent.
            - All file operations are restricted to the {folder_context} directory for security.
            - Focus on creating plans that are specific, measurable, and implementable.
        """),
        # This makes `current_user_id` available in the instructions
        add_state_in_messages=True,
        # -*- Storage -*-
        # Storage chat history and session state in a Postgres table
        storage=PostgresAgentStorage(table_name="development_planner_sessions", db_url=db_url),
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