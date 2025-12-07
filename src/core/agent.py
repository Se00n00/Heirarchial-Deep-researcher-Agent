from .state import Output

from groq import Groq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
from jinja2 import Template
import os
import json

load_dotenv()
API_KEY = os.environ['GROQ_API_KEY']
BASE_URL = os.environ['GROQ_BASE_URL']

# --------------------------------------------
# ----------------- TODO ---------------------
# [DONE][1] Fail Safe: Inference Engines: Openai API, ChatOpenAI , normal request: Returns > json schema + thougts
# [][2] Fix / Break prompts and Fix Context Updation
# [][3] Action Manager for planning_agent


class Agent:
  def __init__(self, model:str, agent:str, system_instructions_path:str, user_instructions_path:str, tools, managed_agents):
    self.inference_client = Groq(
      api_key=os.environ["GROQ_API_KEY"],
    )
    self.agent = agent
    self.contents = None
    self.context = None
    self.system_instructions_template_path = system_instructions_path
    self.tools = tools or {}
    self.managed_agents = managed_agents or {}
    self.feedbacks = {}
    self.execution_iteration = 0
    self.user_prompt = ""
    

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
  

  def forward(self, message = None, task_from_manager = None):

    # self.feedbacks.append({
    #   "iteration": self.execution_iteration,
    #   "name": "GIVEN TASK : ",
    #   "final_answer": message or task_from_manager
    # })

    if self.execution_iteration == 0:

      self.feedbacks.update({
        self.execution_iteration :
        {
          "iteration": self.execution_iteration,
          "name": "Given Task",
          "final_answer": message or task_from_manager
        }
      })
      self.execution_iteration += 1


    prompt_variables = {
      "tools": self.tools or {},
      "managed_agents": self.managed_agents,
      "name": self.agent,
      "task": message or task_from_manager,
      "feedbacks": self.feedbacks
    }

    # Update Context With Feedback ------------ >
    if self.contents == None:
      system_content = self.render_yaml_template(self.system_instructions_template_path, prompt_variables)
      self.context = [
        {"role": "system","content":system_content},
        {"role": "user", "content":message or task_from_manager}
      ]

    # Call model with current contents
    try:
      response = self.inference_client.chat.completions.create(
        input=self.context,
        model="openai/gpt-oss-20b",
      )

      # LOG 1: Agent's Call
      # yield {"type":"ASSISTANT","content":{"Resoning":response.choices[0].message.reasoning,"res":res}}

      raw = response.choices[0].message.content
      if isinstance(raw, str):
        raw = json.loads(raw)

      res = Output.model_validate(raw)

      # res = self.model.invoke(
      #   [SystemMessage(system_content),HumanMessage(content=f"Task: {message or task_from_manager}")]
      # )
    except Exception as e:
      # LOG 2: Exception
      # yield {"type":"ERROR","content":e}

      res = Output(
        name = "final_answer",
        arguments = {"error":e}
      )

    print("EXECUTION :\n\n",res)


    if res.name not in ["final_answer", "SYSTEM"]:
      
      if res.name in [tool['name'] for tool in self.tools.values()]:
        result = self.tools[res.name]['function'](**res.arguments)


      elif res.name in self.managed_agents:
        result = self.managed_agents[res.name]['function'](**res.arguments)

      else:
        result = "tool / agent not found"

      # self.feedbacks.update({
      #   self.execution_iteration :
      #   {
      #     "iteration": self.execution_iteration,
      #     "name": res.name,
      #     "final_answer": result
      #   }
      # })

      self.context.append({
        "role":"assistant",
        "content": f"\nIteration [{self.execution_iteration}] : Observation from {res.name} : {result} \n"
      })

      self.execution_iteration += 1
      return self.forward()

    return res.arguments