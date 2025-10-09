from pydantic import BaseModel

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


# arguments type:
# final answer