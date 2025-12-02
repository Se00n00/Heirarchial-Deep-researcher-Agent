from src.core.agent import Agent
from src.tools.registry import tools # TODO: Import all tools


from langchain_core.messages import HumanMessage

DEEP_RESEARCHER_AGENT_TEMPLATE = "src/core/prompts/planning_agent.yaml"
BROWSER_USE_AGENT_TEMPLATE = "src/core/prompts/browser_use_agent.yaml"
PLANNING_AGENT_TEMPLATE = "src/core/prompts/planning_agent.yaml"

basic_managed_agent = {}
# TODO : Define tools here

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
    "description": "",
    "function" : browser_use.forward # removing brackets to make it callable
}

deep_researcher_description = {
    "name": "deep_researcher_agent",
    "description": "",
    "function" : deep_researcher.forward # removing brackets to make it callable
}

planner_description = {
    "name": "planning_agent",
    "description": "",
    "function" : planner.forward  # removing brackets to make it callable
}
planner.add_managed_agents(
    {
        "browser_user": browser_use_description,
        "deep_researcher": deep_researcher_description
    }
)
deep_researcher.add_managed_agents(
    {
        "browser_user": browser_use_description
    }
)
browser_use.add_managed_agents(
    {
        "deep_researcher": deep_researcher_description
    }
)


if __name__ == "__main__":
    
    resume = True

    while(resume):
        input_message = input("Enter Any Task to do ")
        message = HumanMessage(content = input_message)
        print(f"Output : {planner.forward(message)}")

        resume_ = input("Continue_conersation: ------------------------------------------- [T / F]")
        if resume_ == 'F':
            resume = False
