import sys
import os
import asyncio

# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, project_root)

from pathlib import Path # Get the project root dynamically

project_root = Path(__file__).resolve().parent.parent  # Goes up to HEIRARCHICAL-DEEP-RESEARCHER-AGENT/
sys.path.insert(0, str(project_root)) # Add project root to sys.path FIRST

# Define template paths relative to project root
DEEP_RESEARCHER_AGENT_TEMPLATE = project_root / "src/core/prompts/deep_researcher_agent.md"
BROWSER_USE_AGENT_TEMPLATE = project_root / "src/core/prompts/browser_use_agent.md"
PLANNING_AGENT_TEMPLATE = project_root / "src/core/prompts/planning_agent.md"
USER_INSTRUCTION_TEMPLATE = project_root / "src/core/prompts/user_prompt.yaml"



from src.core.agent import Agent
from src.tool_builder import tool_builder

def create_agent(model = "llama-3.1-8b-instant"):
    basic_managed_agent = {}
    tools = tool_builder()

    planner = Agent(
        model = model,
        agent = "planning_agent",
        system_instructions_path = PLANNING_AGENT_TEMPLATE,
        user_instructions_path = USER_INSTRUCTION_TEMPLATE,
        tools = {},
        managed_agents = basic_managed_agent
    )
    planner.add_tools(
        tools = {k: tools[k] for k in ["final_answer"]},
    )

    browser_use = Agent(
        model = model,
        agent = "browser_use_agent",
        system_instructions_path = BROWSER_USE_AGENT_TEMPLATE,
        user_instructions_path = USER_INSTRUCTION_TEMPLATE,
        tools = {},
        managed_agents = basic_managed_agent
    )

    browser_use.add_tools(
        tools = {k: tools[k] for k in [
            "final_answer",
            "web_search",
            "download_file",
            "visit_page",
            "page_up",
            "page_down",
            "find_on_page_ctrl_f",
            "find_next",
            "find_archived_url"
            ]},
    )

    deep_researcher = Agent(
        model = model,
        agent = "deep_researcher_agent",
        system_instructions_path = DEEP_RESEARCHER_AGENT_TEMPLATE,
        user_instructions_path = USER_INSTRUCTION_TEMPLATE,
        tools = {},
        managed_agents = basic_managed_agent
    )

    deep_researcher.add_tools(
        tools = {k: tools[k] for k in ["final_answer","find_archived_url"]},
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
    # deep_researcher.add_managed_agents(
    #     {
    #         "browser_use_agent": browser_use_description
    #     }
    # )
    # browser_use.add_managed_agents(
    #     {
    #         "deep_researcher_agent": deep_researcher_description
    #     }
    # )

    return planner

def main():
    resume = True
    while resume:
        message = input("Enter Any Task to do: \t")
        
        if message.strip().lower() in ["exit", "quit", "stop"]:
            print("Goodbye!")
            break
        
        try:
            agent = create_agent()
            res = agent.forward(message)
            print(f"Output: {res}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Optional: ask to continue
        cont = input("Continue? (y/n): ")
        if cont.lower() != 'y':
            resume = False

if __name__ == "__main__":
    asyncio.run(main())