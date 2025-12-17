from .state import Action
from .utils import render_yaml_template, extract_completion_metadata
from .context_manager import Context_Manager

from groq import Groq
import groq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
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
    messages = []

    for obs in self.observations:
      messages.append({
        "role": "user",
        "content": (
          f"Observation [{obs['iteration']}]\n"
          f"Source: {obs['source']}\n"
          f"Type: {obs['type']}\n"
          f"Result:\n{obs['result']}"
        )
      })

    return messages

  def call_llm(self, tries = 0):
    try:
      response = self.inference_client.chat.completions.create(
        model= self.model,
        messages=self.context + self.build_observations(),
        stream=False
      )
      raw = response.choices[0].message.content
      action = Action.model_validate(json.loads(raw))
      
      # --------------------
      # LOG 1: Model Output
      # --------------------
      yield {"type":"ASSISTANT","content":{"metadata": extract_completion_metadata(response) ,"response":{"name":action.name,"arguments": str(action.arguments)}}}
     
      return action
    
    except (json.JSONDecodeError, groq.BadRequestError) as e:
      if tries >= self.MAX_RETRIES:
        return Action(
          name="final_answer",
          arguments={
            "error": type(e).__name__,
            "message": str(e),
          },
        )

      if isinstance(e, json.JSONDecodeError):
        # assuming Validation Error had occured due to context pollution
        # Just remove the last observation and gives agent another chance to fix the error
        
        # Though this error may arise from bad prompt or bad set model
        if self.observations == []:
          return Action(
            name="final_answer",
            arguments={
              "type": type(e).__name__,
              "error": str(e),
            },
          )
        
        if tries > 1:
          if self.observations:
            self.observations.pop()
        
        else:
          self.observations[-1]["result"] = self.context_manager.summarize_tool_output(
            task=self.context[1]["content"],
            tool_output=self.observations[-1]["result"],
            tool_used = self.observations[-1]["source"]
          )


      if isinstance(e, groq.BadRequestError):
        # Optional: trim or reset context here
        # self.context = self.context[-N:]
        
        index_list = self.context_manager.minimize_context(
          task=self.context[1]["content"],
          observations=self.observations
        )

        self.observations = [obj for idx, obj in enumerate(self.observations) if idx in index_list]

      call = yield from self.call_llm(tries=tries + 1)
      return call
    
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
      call = yield from self.call_llm(tries=tries + 1)
      return call

    except Exception as e:
      return Action(
        name = "final_answer",
        arguments = {"Exception": str(e)}
      )

  def _run_generator(self, gen):
    result = None
    try:
      while True:
        event = next(gen)
        yield event
    except StopIteration as e:
      result = e.value
    return result


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

    # try:
    #   res = self.call_llm(tries=0)
    # except Exception as e:

    #   res = Action(
    #     name = "final_answer",
    #     arguments = {"error": str(e)}
    #   )
    res = yield from self._run_generator(self.call_llm())

    if res.name not in ["final_answer","final_answer_tool"]:
      try:
        if res.name in [tool['name'] for tool in self.tools.values()]:
          result = self.tools[res.name]['function'](**res.arguments)

          # Reject tool's ouput if it is not fit for result as it may pollute the context
          if self.context_manager.verify_tool_output(
            task=self.context[1]["content"], tool_output=result, tries=0) == False:
            return self.forward()
          
          
          # ------------------------
          # LOG 2: Valid Tool Output
          # ------------------------
          yield {"type":"TRACE","content": {"output":str(result), "name":res.name}}
          result_type = "tool"
          

        elif res.name in self.managed_agents:
          result = yield from self.managed_agents[res.name]['function'](**res.arguments)
          
          # --------------------
          # LOG 3: Agent Output
          # --------------------
          yield {"type":"TRACE","content": {"output":str(result), "name":res.name}}

          result_type = "agent"

        else:
          raise Exception("tool or agent not found")
        
      except Exception as e:
        res = yield from self.forward()
        return res


      self.update_observation(
        action_name = f"[{res.name}]",
        type = result_type,
        result = str(result)
      )
      self.execution_iteration += 1
      res = yield from self.forward()
      return res
    
  
    if self.agent != "planning_agent":
      self.observations = [] # Empty Observations
    
    # ---------------------
    # LOG 4: Final Output
    # ----------------------
    if res.name in ["final_answer","final_answer_tool"] and self.agent == "planning_agent":
      yield {"type": "FINAL_ANSWER", "content": res.arguments}

    return res