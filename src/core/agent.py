from .state import Output

from groq import Groq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
from jinja2 import Template
import os
import json
from pathlib import Path

load_dotenv()
API_KEY = os.environ['GROQ_API_KEY']
BASE_URL = os.environ['GROQ_BASE_URL']

# --------------------------------------------
# ----------------- TODO ---------------------
# [DONE][1] Fail Safe: Inference Engines: Openai API, ChatOpenAI , normal request: Returns > json schema + thougts
# [DONE][2] Fix / Break prompts and Fix Context Updation
# [][3] Action Manager for planning_agent


class Agent:
  def __init__(self, model:str, agent:str, system_instructions_path:str, user_instructions_path:str, tools, managed_agents):
    self.inference_client = Groq(
      api_key=os.environ["GROQ_API_KEY"]
    )
    self.model= model
    self.agent = agent
    self.context = None
    self.system_instructions_template_path = system_instructions_path
    self.user_template_path = user_instructions_path
    self.tools = tools or {}
    self.managed_agents = managed_agents or {}
    self.feedbacks = {}
    self.execution_iteration = 0
    

  def render_yaml_template(self, file_path, var):
    with open(file_path, "r") as f:
      file_content = f.read()
    template = Template(file_content)
    rendered = template.render(**var)
    return rendered
  
  def add_managed_agents(self, agent_list):
    self.managed_agents = agent_list
  
  def add_tools(self, tool_list):
    self.tools.update(tool_list)
  

  def forward(self, task = None):

    prompt_variables = {
      "tools": self.tools or {},
      "managed_agents": self.managed_agents,
      "name": self.agent,
      "task": task
    }

    # Update Context With Feedback ------------ >
    if self.context == None:
      system = self.render_yaml_template(self.system_instructions_template_path, prompt_variables)
      user = self.render_yaml_template(self.user_template_path, prompt_variables)
      
      self.context = [
        {"role": "system", "content":"""Always return an answer no matter what, output format: {'name': name of tool/agent  ,'arguments': arguments to give to tool/ agent}  , use JSON format """},
        {"role": "system","content":system},
        {"role": "user", "content":user}
      ]

    try:
      response = self.inference_client.chat.completions.create(
        model= self.model,
        messages=self.context
      )

      # LOG 1: Agent's Call > More MetaData
      # yield {"type":"ASSISTANT","content":{"Resoning":response.choices[0].message.reasoning,"res":res}}

      raw = response.choices[0].message.content
      res = Output.model_validate(json.loads(raw))

    except Exception as e:
      # LOG 2: Exception
      # yield {"type":"ERROR","content":e}

      res = Output(
        name = "final_answer",
        arguments = {"error":e}
      )

    print("EXECUTION :\n\n",res)


    if res.name not in ["final_answer","final_answer_tool"]:
      
      if res.name in [tool['name'] for tool in self.tools.values()]:
        result = self.tools[res.name]['function'](**res.arguments)


      elif res.name in self.managed_agents:
        result = self.managed_agents[res.name]['function'](**res.arguments)

      else:
        result = "tool / agent not found"

      self.context.append({
        "role":"assistant",
        "content": f"\nIteration [{self.execution_iteration}] : Observation from {res.name} : {result} \n"
      })

      self.execution_iteration += 1
      return self.forward()

    return res