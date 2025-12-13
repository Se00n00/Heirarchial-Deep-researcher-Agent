from pydantic import BaseModel, Field

class Action(BaseModel):
  name: str
  arguments: dict

class Agent_Output(BaseModel):
  actions: list[Action]