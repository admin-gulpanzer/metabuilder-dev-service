from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools

from db.session import db_url
from knowledge.retrievers.pinecone_relace import async_retriever


def get_planner_retriever(namespace: Optional[str] = None):
    """
    Create a custom retriever that uses Pinecone with Relace embeddings and reranking.
    
    Args:
        namespace (Optional[str]): Pinecone namespace for the knowledge domain
        
    Returns:
        Callable: Configured retriever function for planning knowledge
    """
    # Create a configured retriever function with planning-specific parameters
    async def configured_retriever(query: str, agent=None, **kwargs):
        """
        Configured retriever function that uses the predefined parameters for planning.
        """
        # Set planning-specific parameters in kwargs
        kwargs['num_documents'] = 15  # Retrieve more documents initially
        
        return await async_retriever(
            query=query,
            agent=agent,
            namespace=namespace,
            rerank=True,       # Enable Relace reranking
            top_k_after_rerank=8,  # Return top 8 most relevant after reranking
            **kwargs
        )
    
    return configured_retriever


def get_planner_agent(
    model_id: str = "gpt-4o",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
    knowledge_namespace: Optional[str] = "admin-gulpanzer/gen-1",
) -> Agent:
    """
    Create a specialized planning agent that uses Pinecone knowledge base with Relace retriever.
    
    Args:
        model_id (str): OpenAI model to use (default: "gpt-4o")
        user_id (Optional[str]): User identifier for personalization
        session_id (Optional[str]): Session identifier for context
        debug_mode (bool): Enable debug logging (default: True)
        knowledge_namespace (Optional[str]): Pinecone namespace for knowledge domain
        
    Returns:
        Agent: Configured planner agent with knowledge base and tools
    """
    return Agent(
        name="Planner Agent",
        agent_id="planner_agent",
        user_id=user_id,
        session_id=session_id,
        model=OpenAIChat(id=model_id),
        # Tools available to the agent
        tools=[DuckDuckGoTools()],
        # Description of the agent
        description=dedent("""\
            You are PlannerAgent, an advanced AI Agent specializing in strategic planning, project management, and systematic approach to achieving goals.

            Your expertise includes analysing the codebase provided in the knowledge base and providing planning assistance for the user.
        """),
        # Instructions for the agent
        instructions=dedent("""\
            Your mission is to provide detailed planning assistance for the user based on the codebase provided in the knowledge base.
            
            IMPORTANT: You MUST use the search_knowledge tool to search the knowledge base when asked about code or functions. 
            Do not respond without searching the knowledge base first.
            
            When searching for authentication functions, look for terms like: auth, login, register, token, jwt, session, password, etc.
            
            Understand the user's request and iteratively search the knowledge base until you have enough information to address the user's request. 
            Your aim is to provide the list of files that needs to be changed and a brief starter prompt along with each file that can then be iteratively passed onto another LLM to generate code changes. 
            
            ALWAYS start by searching the knowledge base using the search_knowledge tool.
        """),
        # This makes `current_user_id` available in the instructions
        add_state_in_messages=True,
        # -*- Knowledge -*-
        # Add the custom Pinecone-Relace retriever
        retriever=get_planner_retriever(namespace=knowledge_namespace),
        # Give the agent a tool to search the knowledge base
        search_knowledge=True,
        # -*- Storage -*-
        # Storage chat history and session state in a Postgres table
        storage=PostgresAgentStorage(table_name="planner_agent_sessions", db_url=db_url),
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
            db=PostgresMemoryDb(table_name="planner_memories", db_url=db_url),
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