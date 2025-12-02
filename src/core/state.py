from pydantic import BaseModel, Field

class Output(BaseModel):
  name: str
  arguments: dict