from .state import Action

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
# [Inside Core Agent Class][3] Observation manager for each agent + change Prompt's Instructions
# [][4] Action Manager for planning_agent


class Agent:
  def __init__(self, model:str, agent:str, system_instructions_path:str, user_instructions_path:str, tools, managed_agents):
    self.inference_client = Groq(
      api_key=os.environ["GROQ_API_KEY"]
    )
    self.model= model
    self.agent = agent
    self.context = None
    self.observations = []
    self.system_instructions_template_path = system_instructions_path
    self.user_template_path = user_instructions_path
    self.managed_agents = managed_agents or {}
    self.feedbacks = {}
    self.execution_iteration = 0
    self.tools = {
      "delete_observations": {
        "name": "delete_observations",
        "description": """
          An internal agent tool that removes all stored observations 
          associated with a specific execution iteration.
          This is typically used to roll back invalid, hallucinated,
          or superseded tool results."
        """,
        "parameters": {
          "type": "object",
          "properties": {
              "iteration": {
                "type": "integer",
                "description": """
                  The execution iteration number whose observations
                  should be deleted from the agent's internal state.
                """
              }
          },
          "required": ["iteration"]
        },
        "output_type": "None",
        "function": self.delete_observations
      }
    }

    

  def render_yaml_template(self, file_path, var):
    with open(file_path, "r") as f:
      file_content = f.read()
    template = Template(file_content)
    rendered = template.render(**var)
    return rendered
  
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


  def delete_observations(self, iteration):
    self.observations = [
      obs for obs in self.observations
      if obs["iteration"] != iteration
    ]

  
  def build_observations(self):
    if self.observations:
      obs_text = "\n".join(
        f"Iteration [{o['iteration']}] | {o['source']} → {o['result']}"
        for o in self.observations
      )

      return [{
        "role": "assistant",
        "content": f"Observations so far:\n{obs_text}"
      }]

    return []

  
  def extract_completion_metadata(self, completion_obj):
    usage = completion_obj.usage

    return {
      "id": completion_obj.id,
      "model": completion_obj.model,
      "created": completion_obj.created,
      "object": completion_obj.object,
      "service_tier": completion_obj.service_tier,
      "system_fingerprint": completion_obj.system_fingerprint,
      "completion_tokens": usage.completion_tokens,
      "prompt_tokens": usage.prompt_tokens,
      "total_tokens": usage.total_tokens,
      "reasoning_tokens": usage.completion_tokens_details.reasoning_tokens,
      "prompt_tokens_details": usage.prompt_tokens_details if usage.prompt_tokens_details == None else usage.prompt_tokens_details.cached_tokens,
      "completion_time": usage.completion_time,
      "prompt_time": usage.prompt_time,
      "queue_time": usage.queue_time,
      "total_time": usage.total_time,
      "resoning": completion_obj.choices[0].message.reasoning,
      "x_groq": completion_obj.x_groq.id,
    }


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
        {"role": "system","content":system},
        {"role": "user", "content":user}
      ]

    try:
      response = self.inference_client.chat.completions.create(
        model= self.model,
        messages=self.context + self.build_observations()
      )

      
      raw = response.choices[0].message.content
      print(f"[{self.execution_iteration}][{self.agent}]| RESPONSE: \n {raw}")
      res = Action.model_validate(json.loads(raw))

      # LOG 1: Agent's Call > More MetaData
      # yield {"type":"ASSISTANT","content":{"metadata": self.extract_completion_metadata(response) ,"response":{"name":res.name,"arguments": {"answer":str(res)}}}}
      
    except Exception as e:
      # LOG 2: Exception
      # yield {"type":"ERROR","content":str(e)}

      res = Action(
        name = "error",
        arguments = {"error": str(e)}
      )


    if res.name not in ["final_answer","final_answer_tool"]:

      if res.name in [tool['name'] for tool in self.tools.values()]:
        result = str(self.tools[res.name]['function'](**res.arguments))


      elif res.name in self.managed_agents:
        result = str(self.managed_agents[res.name]['function'](**res.arguments))

      else:
        result = "tool or agent not found"

      print(f"[{self.execution_iteration}][{self.agent}]| TOOL/MANGED AGENT :\n{result}")

      self.update_observation(
        action_name= f"{res.name}- given to act: {str(res.arguments)}",
        result= result
      )
      self.execution_iteration += 1

      # self.observations.append({
      #   "role":"assistant",
      #   "content": f"\nIteration [{self.execution_iteration}] : Observation from {action.name} : {result} \n"
      # })
      
      return self.forward()
    
    # if res.name in ["final_answer","final_answer_tool"] and self.agent == "planning_agent":
    #   yield {"type": "FINAL_ANSWER", "content": res.arguments.get("answer")}

    if self.agent != "planning_agent":
      self.observations = [] # Empty Observations

    return res