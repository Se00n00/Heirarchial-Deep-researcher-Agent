from .state import Output
from src.tools.registry import tools
from src.agent import agents

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from jinja2 import Template
import os


load_dotenv()
API_KEY = os.environ['GROQ_API_KEY']
BASE_URL = os.environ['GROQ_BASE_URL']

class Agent:
  def __init__(self, model:str, agent:str, system_instructions_path:str, tools, managed_agents):
    self.model = ChatOpenAI(
        model = model,
        api_key = API_KEY,
        base_url = BASE_URL,
        streaming = True,
    ).with_structured_output(Output)

    self.agent = agent
    self.contents = None
    self.system_instructions_template_path = system_instructions_path
    self.tools = tools or {}
    self.managed_agents = managed_agents or {}
    self.feedbacks = None
    self.execution_iteration = 0
    

  def render_yaml_template(self, file_path, var):
    with open(file_path, "r") as f:
      file_content = f.read()
    template = Template(file_content)
    rendered = template.render(**var)
    return rendered
  
  def add_managed_agents(self, agent_list):
    self.managed_agents = agent_list
  
  def add_managed_agents(self, tool_list):
    self.tools.update(tool_list)
  

  def forward(self, message:HumanMessage = None):

    prompt_variables = {
      "tools": self.tools['definitions'],
      "managed_agents": self.managed_agents['definitions'],
      "name": self.agent,
      "task": message.content,
      "feedbacks": self.feedbacks or []
    }

    # Update Context With Feedback ------------ >
    if self.contents == None:
      system_content = self.render_yaml_template(self.system_instructions_template, prompt_variables)
      self.contents = [
        SystemMessage(content=system_content)
      ]

    # Call model with current contents
    res = self.model.invoke(self.contents)


    if res.name != "final_answer":
      
      if res.name in [tool['name'] for tool in self.tools.values()]:
        result = tools[res.name](**res.arguments)


      elif res.name in [agent['name'] for agent in self.managed_agents.values()]:
        result = agents[res.name](**res.arguments)

      else:
        result = "tool / agent not found"

      self.feedbacks.append({
        "iteration": self.execution_iteration,
        "name": res.name,
        "final_answer": result
      })

      self.execution_iteration += 1
      return self.forward()

    return res.arguments