from .state import Action
from .utils import render_yaml_template

from groq import Groq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv

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
# [Inside Core Agent Class][3] Observation manager for each agent + change Prompt's Instructions
# [][4] Action Manager for planning_agent


class Agent:
  def __init__(self, model:str, agent:str, context_manager, system_instructions_path:str, user_instructions_path:str, tools, managed_agents):
    self.inference_client = Groq(
      api_key=os.environ["GROQ_API_KEY"]
    )
    self.model= model
    self.agent = agent
    self.context_manager = context_manager
    self.context = None
    self.observations = []
    self.system_instructions_template_path = system_instructions_path
    self.user_template_path = user_instructions_path
    self.managed_agents = managed_agents or {}
    self.feedbacks = {}
    self.execution_iteration = 0
    self.tools ={}
    
  def add_managed_agents(self, agent_list):
    self.managed_agents = agent_list
  
  def add_tools(self, tools):
    self.tools.update(tools)
  
  def update_observation(self, action_name, result):
    obs = {
      "iteration": self.execution_iteration,
      "source": action_name,
      "result": result,
    }
    self.observations.append(obs)

  def build_observations(self):
    minimized = self.context_manager.forward(
      task=self.context[-1]["content"],
      observations=self.observations
    )

    return [{
      "role": "user",
      "content": f"Relevant observations:\n\n{minimized}"
    }]

  def forward(self, task = None, tries: int | None = None):
    prompt_variables = {
      "tools": self.tools or {},
      "managed_agents": self.managed_agents,
      "name": self.agent,
      "task": task
    }

    # Update Context With Feedback ------------ >
    if self.context == None:
      system = render_yaml_template(self.system_instructions_template_path, prompt_variables)
      user = render_yaml_template(self.user_template_path, prompt_variables)

      self.context = [
        {"role": "system","content":system},
        {"role": "user", "content": f"\You are assisting with a subtask for a larger problem. {task} \n"}
      ]

    try:
      response = self.inference_client.chat.completions.create(
        model= self.model,
        messages=self.context + self.build_observations(),
        stream=False
      )

      
      raw = response.choices[0].message.content
      print("RESPONE: ", raw)
      res = Action.model_validate(json.loads(raw))
      
    except Exception as e:

      res = Action(
        name = "error",
        arguments = {"error": str(e)}
      )

      print("Context Content: \n\n\n", self.context + self.build_observations(), "\n\n\n")



    if res.name not in ["final_answer","final_answer_tool"]:
      try:
        if res.name in [tool['name'] for tool in self.tools.values()]:
          result = self.tools[res.name]['function'](**res.arguments)
          print(f"[TOOL :\n{result}")


        elif res.name in self.managed_agents:
          result = self.managed_agents[res.name]['function'](**res.arguments)
          print(f"[MANGED AGENT :\n{result}")

        else:
          raise Exception("tool or agent not found")
        
      except Exception as e:
        return self.forward()


      self.update_observation(
        action_name= f"{res.name}- given to act: {str(res.arguments)}",
        result= str(result)
      )
      self.execution_iteration += 1
      return self.forward()
    
  
    if self.agent != "planning_agent":
      self.observations = [] # Empty Observations

    return res