from groq import Groq
from dotenv import load_dotenv
import os
from typing import List, Dict

load_dotenv()

# -------- SYSTEM PROMPTS -------- #

SUMMARY_SYSTEM_PROMPT = """
  You are a tool-output summarization agent.

  Your job is to strictly extract information that is directly useful for completing the task.

  Rules:
  - Extract facts, results, constraints, errors, and signals only.
  - Remove navigation text, UI noise, boilerplate, repetition, and procedural details.
  - Do NOT infer, explain, speculate, or restate the task.
  - Do NOT add new information.
  - If no task-relevant information exists, output exactly: NONE

  Output format:
  - Concise Markdown
  - Bullet points only
  - Maximum 4 bullets (prefer 1-2)
"""

SUMMARY_USER_PROMPT = """
  Task: {task}
  Tool used: {tool_used}

  Raw tool output:
  {observations}
"""


VERIFICATION_SYSTEM_PROMPT = """
  You are a validation agent.

  Your task is to decide whether the given output (from agent or tool) contains ANY information
  that could reasonably help solve the task.

  Rules:
  - Do NOT summarize.
  - Do NOT explain.
  - Do NOT infer missing information.
  - Accept even minimal but relevant signals.
  - Reject if the output is pure noise, navigation, UI chrome, or empty.

  Output exactly one word:
    ACCEPT
    REJECT
"""

VERIFICATION_USER_PROMPT = """
  Task: {task}
  Tool output: {observations}
"""

class Context_Manager:
  def __init__(self, model):
    self.client = Groq(
      api_key=os.getenv("GROQ_API_KEY")
    )
    self.model = model
    self.MAX_RETIES = 3

  def verify_tool_output(self, task:str = "", tool_output:str = "", tries = 0) -> bool:
    """
      Verify the tool output
        - rejects uncluttered tool's output
        - rejects if there is nothing relevent present in tool's output
        - but even if there is very little information that maybe used to solve task then accept the tool_output
    """

    messages = [
      {"role": "system", "content": VERIFICATION_SYSTEM_PROMPT},
      {
        "role": "user",
        "content": VERIFICATION_USER_PROMPT.format(
          task=task,
          observations=tool_output
        )
      }
    ]

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        stream=False
      )

      verdict = response.choices[0].message.content.strip()
      return verdict == "ACCEPT"

    except Exception:
      if tries > self.MAX_RETIES:
        return True
      return self.verify_tool_output(task, tool_output, tries=tries + 1)
  
  def summarize_tool_output(self, task: str, tool_output: str, tool_used: str ) -> str:
    """
      Minimize tool output while preserving task-critical information.
      Returns a Markdown bullet summary or 'NONE'.
    """

    messages = [
      {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
      {
        "role": "user",
        "content": SUMMARY_USER_PROMPT.format(
          task=task,
          tool_used=tool_used,
          observations=tool_output
        )
      }
    ]

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        stream=False
      )

      return response.choices[0].message.content.strip()

    except Exception:
      return tool_output
    
  def minimize_context(self, task:str, observations: list[dict]) -> list[int]:
    """
      this would be called if agent run out of context_length and made to minimize at least as possible
       - ensuring observations is retained for solving the task
       - remove any error or non-relevent content
       - if there is any search result, only retains last or more suitable one
       - return list of observation list indices to retain
    """
    retained_indices: List[int] = []

    for idx, obs in enumerate(observations):

      is_valid = self.verify_tool_output(
        task=task,
        tool_output=obs["result"],
        tries=0
      )

      if is_valid:
        retained_indices.append(idx)

    if not retained_indices and observations:
      return [len(observations) - 1]

    return retained_indices