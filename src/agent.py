import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.agent import Agent
# from src.tools.registry import tools

tools = {}


from langchain_core.messages import HumanMessage

DEEP_RESEARCHER_AGENT_TEMPLATE = "/run/media/seono/P/Heirarchial-Deep-researcher-Agent/src/core/prompts/planning_agent.yaml"
BROWSER_USE_AGENT_TEMPLATE = "/run/media/seono/P/Heirarchial-Deep-researcher-Agent/src/core/prompts/browser_use_agent.yaml"
PLANNING_AGENT_TEMPLATE = "/run/media/seono/P/Heirarchial-Deep-researcher-Agent/src/core/prompts/planning_agent.yaml"

basic_managed_agent = {}

planner = Agent(
    model = "openai/gpt-oss-20b",
    agent = "planning_agent",
    system_instructions_path = PLANNING_AGENT_TEMPLATE,
    tools = tools,
    managed_agents = basic_managed_agent
)

browser_use = Agent(
    model = "openai/gpt-oss-20b",
    agent = "browser_use_agent",
    system_instructions_path = BROWSER_USE_AGENT_TEMPLATE,
    tools = tools,
    managed_agents = basic_managed_agent
)

deep_researcher = Agent(
    model = "openai/gpt-oss-20b",
    agent = "deep_researcher_agent",
    system_instructions_path = DEEP_RESEARCHER_AGENT_TEMPLATE,
    tools = tools,
    managed_agents = basic_managed_agent
)

browser_use_description = {
    "name": "browser_use_agent",
    "description": "Automates web interactions for searching, extracting, and collecting real-time data to support research and information needs.",
    "function" : browser_use.forward
}

deep_researcher_description = {
    "name": "deep_researcher_agent",
    "description": "Gathers and synthesizes high-quality information on topics, automatically producing research reports or knowledge summaries.",
    "function" : deep_researcher.forward
}

planner_description = {
    "name": "planning_agent",
    "description": "Orchestrates overall task workflows by decomposing them into sub-tasks and coordinating lower-level agents for efficient completion.",
    "function" : planner.forward
}
planner.add_managed_agents(
    {
        "browser_use_agent": browser_use_description,
        "deep_researcher_agent": deep_researcher_description
    }
)
deep_researcher.add_managed_agents(
    {
        "browser_use_agent": browser_use_description
    }
)
browser_use.add_managed_agents(
    {
        "deep_researcher_agent": deep_researcher_description
    }
)


if __name__ == "__main__":
    
    resume = True

    while(resume):
        input_message = input("Enter Any Task to do: \t")
        message = HumanMessage(content = input_message)
        print(f"Output : {planner.forward(message)}")

        resume_ = input("Continue_conersation: ------------------------------------------- [T / F]: \t")
        if resume_ == 'F':
            resume = False
