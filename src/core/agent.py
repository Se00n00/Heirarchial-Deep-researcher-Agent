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


  async def forward(self, task=None):
    prompt_variables = {
        "tools": self.tools or {},
        "managed_agents": self.managed_agents,
        "name": self.agent,
        "task": task
    }

    # Initial context
    if self.context is None:
        system = self.render_yaml_template(self.system_instructions_template_path, prompt_variables)
        user = self.render_yaml_template(self.user_template_path, prompt_variables)

        self.context = [
            {
                "role": "system",
                "content": "Always return an answer no matter what. "
                           "Output format: {'name': ..., 'arguments': ...} in JSON."
            },
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

    try:
        response = self.inference_client.chat.completions.create(
            model=self.model,
            messages=self.context
        )

        raw = response.choices[0].message.content
        res = Output.model_validate(json.loads(raw))

        # SEND LOG 1
        yield {
            "type": "ASSISTANT",
            "content": {
                "metadata": self.extract_completion_metadata(response),
                "response": {
                    "name": res.name,
                    "arguments": {"answer": str(res)}
                }
            }
        }

    except Exception as e:
        # SEND LOG 2
        yield {"type": "ERROR", "content": str(e)}

        res = Output(
            name="final_answer",
            arguments={"error": str(e)}
        )

    # Execution path
    if res.name not in ("final_answer", "final_answer_tool"):

        import inspect

        # TOOL CALL -------------------------
        if res.name in [tool["name"] for tool in self.tools.values()]:
            func = self.tools[res.name]["function"]
            call_result = func(**res.arguments)

            if inspect.isawaitable(call_result):
                result = await call_result
            else:
                result = call_result

        # MANAGED AGENT ---------------------
        elif res.name in self.managed_agents:
            subagent = self.managed_agents[res.name]["function"]
            sub = subagent(**res.arguments)

            # If it's async generator → iterate
            if inspect.isasyncgen(sub):
                async for x in sub:
                    yield x
                result = x
            else:
                # If coroutine → await
                if inspect.isawaitable(sub):
                    result = await sub
                else:
                    result = sub

        # UNKNOWN
        else:
            result = "tool / agent not found"

        # Update context
        self.context.append({
            "role": "assistant",
            "content": f"\nIteration [{self.execution_iteration}] → Observation from {res.name}: {result}\n"
        })

        self.execution_iteration += 1

        # RECURSE correctly using `async for`
        async for msg in self.forward():
            yield msg
        return

    # Final answer (only for planning agent)
    if res.name in ("final_answer", "final_answer_tool") and self.agent == "planning_agent":
        yield {"type": "FINAL_ANSWER", "content": res.arguments.get("answer")}

    # FINAL RETURN (async generator cannot use `return`)
    yield {
        "type": "FINAL_ANSWER",
        "content": res.arguments
    }
