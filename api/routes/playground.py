from agno.playground import Playground

from agents.agno_assist import get_agno_assist
from agents.file_agent import get_file_agent
from agents.finance_agent import get_finance_agent
from agents.web_agent import get_web_agent
from agents.git_agent import get_git_agent
from agents.development_planner_agent import get_development_planner_agent
from agents.semantic_search_agent import get_code_analyzer_agent
from agents.planner_agent import get_planner_agent

######################################################
## Routes for the Playground Interface
######################################################

# Get Agents to serve in the playground
web_agent = get_web_agent(debug_mode=True)
agno_assist = get_agno_assist(debug_mode=True)
file_agent = get_file_agent(debug_mode=True)
finance_agent = get_finance_agent(debug_mode=True)
git_agent = get_git_agent(debug_mode=True)
development_planner_agent = get_development_planner_agent(debug_mode=True)
code_analyzer_agent = get_code_analyzer_agent(debug_mode=True)
planner_agent = get_planner_agent(debug_mode=True)

# Create a playground instance
playground = Playground(agents=[web_agent, agno_assist, file_agent, finance_agent, git_agent, development_planner_agent, code_analyzer_agent, planner_agent])

# Get the router for the playground
playground_router = playground.get_async_router()
