from .state import Action
from .utils import render_yaml_template
from .context_manager import Context_Manager

from groq import Groq
import groq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv

import os
import time
import json
from pathlib import Path
from pydantic import ValidationError

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
  def __init__(self, model:str, agent:str, system_instructions_path:str, user_instructions_path:str, tools, managed_agents):
    self.inference_client = Groq(
      api_key=os.environ["GROQ_API_KEY"]
    )
    self.model= model
    self.agent = agent
    self.context_manager = Context_Manager(model=model)
    self.context = None
    self.observations = []
    self.system_instructions_template_path = system_instructions_path
    self.user_template_path = user_instructions_path
    self.managed_agents = managed_agents or {}
    self.feedbacks = {}
    self.execution_iteration = 0
    self.tools ={}
    self.MAX_RETRIES = 3
    self.RATE_LIMIT_BACKOFF_SEC = 2
    
  def add_managed_agents(self, agent_list):
    self.managed_agents = agent_list
  
  def add_tools(self, tools):
    self.tools.update(tools)
  
  def update_observation(self, action_name, result, type = None):
    obs = {
      "iteration": self.execution_iteration,
      "source": action_name,
      "result": result,
      "type": type
    }
    self.observations.append(obs)

  def build_observations(self):
    if self.observations == []:
      return []
    
    content = "\n".join(f"[{o['iteration']}][{o['source']}] : {o['result']}" for o in self.observations)
    return [{
      "role": "user",
      "content": f"Relevant observations:\n\n{content}"
    }]
  
  def call_llm(self, tries = 0):
    try:
      response = self.inference_client.chat.completions.create(
        model= self.model,
        messages=self.context + self.build_observations(),
        stream=False
      )
      raw = response.choices[0].message.content
      return Action.model_validate(json.loads(raw))
    
    except (ValidationError, groq.BadRequestError) as e:
      if tries >= self.MAX_RETRIES:
        return Action(
          name="final_answer",
          arguments={
            "error": type(e).__name__[0],
            "message": str(e),
          },
        )

        
      
      # TODO : Manage Context
      if isinstance(e, ValidationError):
        # assuming Validation Error had occured due to context pollution
        pass

      if isinstance(e, groq.BadRequestError):
        # Optional: trim or reset context here
        # self.context = self.context[-N:]
        pass

      return self.call_llm(tries=tries + 1)
    
    except groq.RateLimitError as e:
      if tries >= self.MAX_RETRIES:
        return Action(
          name="final_answer",
          arguments={
            "error": "RateLimitError",
            "message": str(e),
          },
        )

      time.sleep(self.RATE_LIMIT_BACKOFF_SEC) # TODO: Manage incase of failure
      return self.call_llm(tries=tries + 1)

    except Exception as e:
      return Action(
        name = "final_answer",
        arguments = {"Exception": str(e)}
      )

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
        {"role": "user", "content": f"\nTask : {task} \n"}
      ]

    try:
      res = self.call_llm(tries=0)
    except Exception as e:

      res = Action(
        name = "error",
        arguments = {"error": str(e)}
      )

      print("[ERROR]:  \n",str(e))



    if res.name not in ["final_answer","final_answer_tool"]:
      try:
        if res.name in [tool['name'] for tool in self.tools.values()]:
          result = self.tools[res.name]['function'](**res.arguments)
          # result = self.context_manager.forward(
          #   task = self.context[-1]["content"],
          #   observations = tool_output,
          #   tool_used = res.name
          # )
          result_type = "tool"

          print(f"[TOOL] :\n{result}")


        elif res.name in self.managed_agents:
          result = self.managed_agents[res.name]['function'](**res.arguments)
          result_type = "agent"

          print(f"[MANGED AGENT :\n{result}")

        else:
          raise Exception("tool or agent not found")
        
      except Exception as e:
        return self.forward()


      self.update_observation(
        action_name = f"[{res.name}]",
        type = result_type,
        result = str(result)
      )
      self.execution_iteration += 1
      return self.forward()
    
  
    if self.agent != "planning_agent":
      self.observations = [] # Empty Observations

    return res