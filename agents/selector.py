from enum import Enum
from typing import List, Optional

from agents.agno_assist import get_agno_assist
from agents.file_agent import get_file_agent
from agents.finance_agent import get_finance_agent
from agents.git_agent import get_git_agent
from agents.web_agent import get_web_agent
from agents.development_planner_agent import get_development_planner_agent
from agents.semantic_search_agent import get_code_analyzer_agent
from agents.planner_agent import get_planner_agent


class AgentType(Enum):
    WEB_AGENT = "web_agent"
    AGNO_ASSIST = "agno_assist"
    FILE_AGENT = "file_agent"
    FINANCE_AGENT = "finance_agent"
    GIT_AGENT = "git_agent"
    DEVELOPMENT_PLANNER_AGENT = "development_planner_agent"
    CODE_ANALYZER_AGENT = "code_analyzer_agent"
    PLANNER_AGENT = "planner_agent"


def get_available_agents() -> List[str]:
    """Returns a list of all available agent IDs."""
    return [agent.value for agent in AgentType]


def get_agent(
    model_id: str = "gpt-4.1",
    agent_id: Optional[AgentType] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
):
    if agent_id == AgentType.WEB_AGENT:
        return get_web_agent(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)
    elif agent_id == AgentType.AGNO_ASSIST:
        return get_agno_assist(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)
    elif agent_id == AgentType.FILE_AGENT:
        return get_file_agent(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)
    elif agent_id == AgentType.FINANCE_AGENT:
        return get_finance_agent(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)
    elif agent_id == AgentType.GIT_AGENT:
        return get_git_agent(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)
    elif agent_id == AgentType.DEVELOPMENT_PLANNER_AGENT:
        return get_development_planner_agent(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)
    elif agent_id == AgentType.CODE_ANALYZER_AGENT:
        return get_code_analyzer_agent(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)
    elif agent_id == AgentType.PLANNER_AGENT:
        return get_planner_agent(model_id=model_id, user_id=user_id, session_id=session_id, debug_mode=debug_mode)

    raise ValueError(f"Agent: {agent_id} not found")
