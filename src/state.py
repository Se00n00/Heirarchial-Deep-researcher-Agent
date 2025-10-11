from pydantic import BaseModel
from typing import TypedDict

class Action(BaseModel):
    """
    examples:
        tool call:
        {
            "name": "final_answer",
            "arguments": {"answer": "insert your final answer here"}
        }
        
        agent call:
        {
            "name":"browser_use_agent"
            "arguments": {"task": "given task"}
        }
    """
    name:str
    arguments:dict

class action(TypedDict):
    name:str
    arguments:dict

class State(TypedDict):
    message:str
    action:action