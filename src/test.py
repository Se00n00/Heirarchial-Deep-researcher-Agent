from langgraph.graph import StateGraph, END
from typing import TypedDict
from pydantic import BaseModel

# ============================================================
# Action Model
# ============================================================
class Action(BaseModel):
    """
    Examples:
        tool call:
            {"name": "final_answer", "arguments": {"answer": "insert your final answer here"}}
        agent call:
            {"name": "browser_use_agent", "arguments": {"task": "given task"}}
    """
    name: str
    arguments: dict


# ============================================================
# Shared Graph State
# ============================================================
class AgentState(TypedDict):
    task: str
    action: dict
    final_answer: str


# ============================================================
# 1️⃣ Planning Agent
# ============================================================
def planning_agent(state: AgentState):
    print(f"\n[Planning Agent] Received task: {state['task']}")

    # Determine next action based on content
    if "research" in state["task"].lower():
        next_action = Action(name="deep_researcher_agent", arguments={"task": state["task"]})
    elif "browse" in state["task"].lower():
        next_action = Action(name="browser_use_agent", arguments={"task": state["task"]})
    else:
        next_action = Action(name="tools", arguments={"task": state["task"]})

    # Update state
    state["action"] = next_action.dict()
    print(f"[Planning Agent] Selected next: {next_action.name}")

    # return the node name directly (LangGraph routes automatically)
    return next_action.name


# ============================================================
# 2️⃣ Deep Researcher Agent
# ============================================================
def deep_researcher_agent(state: AgentState):
    print(f"\n[Deep Researcher Agent] Handling task: {state['action']['arguments']['task']}")
    state["final_answer"] = "Deep research completed."
    return "planning_agent"


# ============================================================
# 3️⃣ Browser Use Agent
# ============================================================
def browser_use_agent(state: AgentState):
    print(f"\n[Browser Use Agent] Browsing: {state['action']['arguments']['task']}")
    state["final_answer"] = "Browser agent extracted live content."
    return "planning_agent"


# ============================================================
# 4️⃣ Tools Node
# ============================================================
def tools(state: AgentState):
    print(f"\n[Tools] Running tool for: {state['action']['arguments']['task']}")
    state["final_answer"] = "Tool executed successfully."
    return "planning_agent"


# ============================================================
# 5️⃣ End Node
# ============================================================
def end(state: AgentState):
    print(f"\n✅ Final Answer to User: {state['final_answer']}")
    return state


# ============================================================
# 6️⃣ Build Graph
# ============================================================
graph = StateGraph(AgentState)

graph.add_node("planning_agent", planning_agent)
graph.add_node("deep_researcher_agent", deep_researcher_agent)
graph.add_node("browser_use_agent", browser_use_agent)
graph.add_node("tools", tools)
graph.add_node(END, end)

# All possible transitions
graph.add_edge("planning_agent", "deep_researcher_agent")
graph.add_edge("planning_agent", "browser_use_agent")
graph.add_edge("planning_agent", "tools")
graph.add_edge("planning_agent", END)

# Feedback loops
graph.add_edge("deep_researcher_agent", "planning_agent")
graph.add_edge("browser_use_agent", "planning_agent")
graph.add_edge("tools", "planning_agent")

graph.set_entry_point("planning_agent")
app = graph.compile()


# ============================================================
# 7️⃣ Example Run
# ============================================================
print("\n--- Example 1: Research Task ---")
app.invoke({"task": "Perform deep research on climate change", "action": {}, "final_answer": ""})

print("\n--- Example 2: Browse Task ---")
app.invoke({"task": "Browse the web for recent AI news", "action": {}, "final_answer": ""})

print("\n--- Example 3: Tool Task ---")
app.invoke({"task": "Use calculator tool", "action": {}, "final_answer": ""})

# agent.invoke({"name":""})