from src.state import State, AgentState
from src.agents.planning_agent.planning_agent import PlanningAgent
from src.agents.browser_use_agent.browser_agent import BrowserAgent
from src.agents.deep_researcher_agent.deep_researcher import DeepResearcherAgent

from langgraph.graph import StateGraph, START, END

# NODE: Planning Agent, DeepResearcher Agent, Browser Agent
Planner = PlanningAgent()
Researcher = DeepResearcherAgent()
Browser = BrowserAgent()

def final_answer(state:State):
    print(state["action"]["arguments"])

def planning_conditional_edge(state:State):
    match(state['action']['name']):
        case 'planning_agent':
            return 'planning_agent'
        case 'final_answer':
            return 'final_answer'
        case _:
            return 'final_answer'

agent = (
    StateGraph(State)
    .add_node("planning_agent",Planner)
    .add_node("researcher_agent",Researcher)
    .add_node("browser_use_agent", Browser)
    .add_edge(START, "planning_agent")
    .add_conditional_edges(
        "planning_agent",
        planning_conditional_edge,
        ["final_answer"]
        )
    .compile()
)

# Invoking the graph
user_query = "question !!!"
agent.invoke(
    {"action":
        {
            "name":"plannig_agent",
            "arguments":{"task":user_query}
        }
    }
)