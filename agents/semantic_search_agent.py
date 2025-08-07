"""
Comprehensive Code Analyzer Agent using Agno framework

This agent combines semantic search through vector embeddings stored in Pinecone
with direct file analysis capabilities for comprehensive code understanding.
Each repository is indexed in a separate namespace within the codebase-index.

Usage:
    # Create agent for analyzing code across all repositories
    agent = get_code_analyzer_agent()
    
    # Create agent for analyzing specific repository namespace
    agent = get_code_analyzer_agent(repo_namespace="my-repo")
    
    # Create agent with custom parameters
    agent = get_code_analyzer_agent(
        repo_namespace="my-repo",
        model_id="gpt-4o",
        user_id="user123"
    )
"""

from textwrap import dedent
from typing import Optional

from agno import debug
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.file import FileTools
from agno.tools import Toolkit
from services.pinecone_retriever import create_pinecone_knowledge_base


def get_code_analyzer_agent(
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
    repo_namespace: Optional[str] = None,
) -> Agent:
    """
    Create a comprehensive code analyzer agent that combines semantic search and file analysis.
    
    Args:
        model_id: OpenAI model to use
        user_id: User ID for the agent
        session_id: Session ID for the agent
        debug_mode: Whether to enable debug mode
        repo_namespace: Optional repository namespace to focus on
        
    Returns:
        Configured Agent instance for comprehensive code analysis
    """
    
    # Create tools list - comprehensive code analyzer with file tools
    from pathlib import Path
    
    # Configure FileTools with base_dir to restrict to dev folder
    dev_folder = Path(__file__).parent.parent / "dev"
    
    tools: list = [
        FileTools(
            base_dir=dev_folder,  # Restrict all operations to dev folder
            save_files=True,      # Allow file writing/creation
            read_files=True,      # Allow file reading
            list_files=True,      # Allow file listing
            search_files=True     # Allow file searching
        ),
    ]
    
    # Create knowledge base with custom Pinecone retriever
    knowledge_base = create_pinecone_knowledge_base(
        repo_namespace=repo_namespace,
        top_k=10
    )
    
    # Determine the context for the description
    if repo_namespace:
        context_description = f"focused on repository '{repo_namespace}'"
    else:
        context_description = "across all indexed repositories"
    
    # Create agent description
    description = dedent(f"""
    You are a Comprehensive Code Analyzer Agent that combines semantic search and file analysis capabilities.
    
    Your capabilities:
    - Perform semantic search through vector embeddings of code {context_description}
    - Analyze and read files directly from the filesystem within the dev directory
    - Find relevant code snippets, functions, and classes using both semantic similarity and direct file access
    - Filter results by file type and repository
    - Provide detailed code analysis with file paths and content
    - Search for specific patterns, functions, or code structures
    
    Available tools:
    - read_file: Read and analyze specific files (restricted to dev directory)
    - list_files: List files in directories (restricted to dev directory)
    - search_files: Search for files matching patterns (restricted to dev directory)
    
    Knowledge capabilities:
    - Semantic search through indexed code repositories using Pinecone
    - Automatic retrieval of relevant code snippets and functions
    - Context-aware code analysis with similarity scoring
    
    When analyzing code:
    - Use semantic search for finding relevant code across indexed repositories
    - Use file tools for direct analysis of specific files or directories within dev/
    - Combine both approaches for comprehensive code understanding
    - Provide context about what you're looking for
    - Ask for specific functions, classes, or code patterns
    - All file operations are automatically restricted to the dev directory for security
    
    Always provide clear, structured responses with the analysis results and explain how they relate to the query.
    """)
    
    # Create agent instructions for comprehensive code analysis
    instructions = dedent(f"""
    You are a Comprehensive Code Analyzer Agent. Your primary goal is to help users understand and analyze code using both semantic search and direct file access.
    
    SECURITY CONFIGURATION:
    - FileTools is configured with base_dir set to the 'dev' directory
    - ALL file operations are automatically restricted to the 'dev' directory
    - You cannot access files outside this directory due to the base_dir configuration
    - No manual path validation needed - the tool handles this automatically
    
    TOOL USAGE GUIDELINES:
    1. Use semantic search (knowledge base) for finding relevant code across indexed repositories
    2. Use read_file for analyzing specific files when you know the path (relative to dev/)
    3. Use list_files SPARINGLY and only for specific directories when needed
    4. Use search_files to find files matching patterns within dev/
    
    IMPORTANT - PREVENT INFINITE LOOPS:
    - NEVER call list_files on the root dev directory (/app/dev) - this causes infinite loops
    - Only use list_files on specific subdirectories like 'gen-1', 'gen-1/backend', etc.
    - If you need to explore the structure, start with specific known directories
    - Use search_files with patterns like '*.py' or 'auth*' instead of listing entire directories
    
    PATH HANDLING (Simplified with base_dir):
    - FileTools base_dir is set to the dev folder
    - Use relative paths from the dev directory root
    - Example: If user asks to read 'gen-1/backend/main.py', use 'gen-1/backend/main.py' (relative to dev/)
    - Example: If user asks to list files in 'gen-1', use 'gen-1' (relative to dev/)
    - Example: If user asks to search for '*.py' in 'gen-1/backend', use 'gen-1/backend/*.py' (relative to dev/)
    - The base_dir configuration automatically handles the dev/ prefix
    
    ANALYSIS STRATEGY:
    - Start with semantic search (knowledge base) to find relevant code patterns
    - Use search_files with specific patterns to find relevant files
    - Use read_file for analyzing specific files when you know the path
    - Use list_files ONLY for specific subdirectories when needed
    - Combine both approaches for comprehensive understanding
    - Provide context about what you're analyzing
    
    RESPONSE FORMAT:
    - Start with a brief explanation of your analysis approach
    - Use the appropriate tools to gather information
    - Present results in a clear, structured format
    - Explain how the results relate to the user's query
    - Provide insights and recommendations when relevant
    
    PERFORMANCE NOTES:
    - Be direct and efficient in your tool usage
    - Focus on getting comprehensive analysis results
    - Use reasoning to connect different pieces of information
    """)
    
    # Create agent
    agent = Agent(
        name="Code Analyzer Agent",
        agent_id="code_analyzer_agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAIChat(id=model_id),
        tools=tools,
        retriever=knowledge_base,
        search_knowledge=True,
        description=description,
        instructions=instructions,
        reasoning=True,  # Enable reasoning for better problem-solving capabilities
        markdown=True  # Enable markdown formatting for better responses
    )
    
    return agent


def get_code_analyzer_agent_for_repo(
    repo_namespace: str,
    model_id: str = "gpt-4o-mini",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    """
    Convenience function to create a code analyzer agent focused on a specific repository.
    
    Args:
        repo_namespace: The repository namespace to focus on
        model_id: OpenAI model to use
        user_id: User ID for the agent
        session_id: Session ID for the agent
        debug_mode: Whether to enable debug mode
        
    Returns:
        Configured Agent instance focused on the specified repository
    """
    return get_code_analyzer_agent(
        model_id=model_id,
        user_id=user_id,
        session_id=session_id,
        debug_mode=debug_mode,
        repo_namespace=repo_namespace
    ) 